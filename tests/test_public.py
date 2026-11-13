import http.client
import json
import threading
import unittest
import app
import exporter

# Public mode deliberately has stricter limits than the desktop app.
original_limits = (app.MAX_INPUT, exporter.MAX_INPUT, exporter.MAX_EXPANDED, exporter.MAX_FILES)
import public_app

class PublicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        public_app.configure_limits()
        cls.server = public_app.PublicServer(('127.0.0.1', 0), public_app.PublicHandler)
        cls.server.public_origin = 'https://example.test'
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        app.MAX_INPUT, exporter.MAX_INPUT, exporter.MAX_EXPANDED, exporter.MAX_FILES = original_limits

    def request(self, method, path, body=b'', headers=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        conn.request(method, path, body=body, headers=headers or {})
        response = conn.getresponse()
        result = (response.status, response.read())
        conn.close()
        return result

    def test_public_origin_session_and_no_shutdown(self):
        status, body = self.request('GET', '/api/session')
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)['mode'], 'public')
        data = json.dumps([{'name':'Demo','chat_messages':[{'text':'Synthetic'}]}]).encode()
        headers = {'Origin':'https://example.test','X-Session-Token':json.loads(body)['token']}
        self.assertEqual(self.request('POST', '/api/inspect', data, headers)[0], 200)
        self.assertEqual(self.request('POST', '/api/inspect', data, {**headers,'Origin':'https://invalid.test'})[0], 403)
        self.assertEqual(self.request('POST', '/api/shutdown', b'', headers)[0], 404)
        self.assertEqual(self.request('GET', '/api/session')[0], 200)

if __name__ == '__main__':
    unittest.main()
