import http.client
import json
import threading
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app

SAMPLE = json.dumps([{'uuid':'synthetic','name':'Demo','chat_messages':[{'sender':'human','text':'Hello 世界'}]}], ensure_ascii=False).encode()

class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = app.Server(('127.0.0.1', 0), app.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.origin = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def request(self, method, path, body=b'', headers=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        conn.request(method, path, body=body, headers=headers or {})
        res = conn.getresponse()
        result = (res.status, dict(res.getheaders()), res.read())
        conn.close()
        return result

    def test_security_headers_and_routes(self):
        code, headers, body = self.request('GET', '/')
        self.assertEqual(code, 200)
        self.assertEqual(headers['Cache-Control'], 'no-store')
        self.assertIn("frame-ancestors 'none'", headers['Content-Security-Policy'])
        self.assertEqual(self.request('GET', '/../../app.py')[0], 404)

    def test_origin_and_token_required(self):
        good = {'Origin': self.origin, 'X-Session-Token': app.TOKEN}
        self.assertEqual(self.request('POST', '/api/inspect', SAMPLE, {})[0], 403)
        self.assertEqual(self.request('POST', '/api/inspect', SAMPLE, {**good, 'Origin':'https://invalid.example'})[0], 403)
        self.assertEqual(self.request('POST', '/api/inspect', SAMPLE, {**good, 'X-Session-Token':'wrong'})[0], 403)
        code, _, body = self.request('POST', '/api/inspect', SAMPLE, good)
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(body)['total_messages'], 1)

    def test_export_in_both_languages(self):
        for lang, marker in [('en', '## User'), ('zh', '## 用户')]:
            headers = {'Origin': self.origin, 'X-Session-Token': app.TOKEN, 'X-Selected':'[0]', 'X-Format':'md', 'X-Language':lang}
            code, _, body = self.request('POST', '/api/export', SAMPLE, headers)
            self.assertEqual(code, 200)
            self.assertIn(marker, body.decode())
            self.assertIn('Hello 世界', body.decode())

if __name__ == '__main__':
    unittest.main()
