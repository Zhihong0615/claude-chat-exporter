#!/usr/bin/env python3
"""Local-only browser app. No chat data leaves this machine."""
from __future__ import annotations
import hmac
import json
import mimetypes
import os
import secrets
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, urlsplit
from exporter import MAX_INPUT, ExportError, describe, load_export, make_output

ROOT = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
WEB = ROOT / 'web'
TOKEN = secrets.token_urlsafe(32)

class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

class Handler(BaseHTTPRequestHandler):
    server_version = 'LocalExporter/1.0'
    sys_version = ''
    def log_message(self, format, *args):
        return
    def _respond(self, code: int, data: bytes, content_type: str, extra: dict | None = None):
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', (extra or {}).get('Cache-Control', 'no-store'))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        for k,v in (extra or {}).items():
            if k.lower() != 'cache-control': self.send_header(k,v)
        self.end_headers()
        try: self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError): pass
    def _json(self, code, obj):
        self._respond(code, json.dumps(obj,ensure_ascii=False).encode('utf-8'), 'application/json; charset=utf-8')
    def _authorized(self):
        permitted=f'http://127.0.0.1:{self.server.server_port}'
        return (self.headers.get('Origin','') == permitted and
                hmac.compare_digest(self.headers.get('X-Session-Token',''),TOKEN))
    def do_GET(self):
        path=urlsplit(self.path).path
        names={'/':'index.html', '/app.js':'app.js', '/style.css':'style.css',
               '/fonts/source-han-serif-cn-vf.woff2':'fonts/source-han-serif-cn-vf.woff2',
               '/fonts/jetbrains-mono-vf.woff2':'fonts/jetbrains-mono-vf.woff2'}
        if path not in names:
            self._json(404,{'error':'页面不存在。'});return
        item=WEB / names[path]
        if not item.is_file():
            self._json(404,{'error':'界面文件缺失。'});return
        mime=mimetypes.guess_type(str(item))[0] or 'application/octet-stream'
        if path.startswith('/fonts/'):
            self._respond(200,item.read_bytes(),'font/woff2',{'Cache-Control':'public, max-age=86400'})
        else:
            self._respond(200,item.read_bytes(),mime+'; charset=utf-8')
    def do_POST(self):
        try:
            if not self._authorized():
                self._json(403,{'error':'无效的本地会话，请重新打开软件。'});return
            path=urlsplit(self.path).path
            if path=='/api/shutdown':
                self._json(200,{'ok':True});threading.Thread(target=self.server.shutdown,daemon=True).start();return
            if path not in ('/api/inspect','/api/export'):
                self._json(404,{'error':'接口不存在。'});return
            try:n=int(self.headers.get('Content-Length','0'))
            except ValueError: raise ExportError('无法读取文件大小。')
            if n<=0 or n>MAX_INPUT: raise ExportError(f'文件为空或超过 {MAX_INPUT // (1024 * 1024)} MB 限制。')
            payload=self.rfile.read(n)
            if len(payload)!=n: raise ExportError('文件传输不完整。')
            chats=load_export(payload)
            if path=='/api/inspect':
                self._json(200,describe(chats));return
            try:
                indices=json.loads(self.headers.get('X-Selected','[]'))
            except json.JSONDecodeError as exc: raise ExportError('会话选择无效。') from exc
            if not isinstance(indices,list): raise ExportError('会话选择无效。')
            data,name,mime=make_output(chats,indices,self.headers.get('X-Format','md'),self.headers.get('X-Details','1')=='1', self.headers.get('X-Language','zh'))
            self._respond(200,data,mime,{'Content-Disposition':"attachment; filename*=UTF-8''"+quote(name,safe=''), 'X-Output-Name':quote(name,safe='')})
        except ExportError as exc:self._json(400,{'error':str(exc)})
        except (BrokenPipeError, ConnectionResetError):pass
        except Exception:
            self._json(500,{'error':'转换失败，请检查文件格式和剩余内存。'})

def main():
    host='127.0.0.1'
    with Server((host,0),Handler) as server:
        url=f'http://{host}:{server.server_port}/#token={TOKEN}'
        print('Claude 聊天导出工具已启动。关闭此窗口即可停止。',flush=True)
        print('如果浏览器没有自动打开，请复制下面的本地地址：',flush=True)
        print(url,flush=True)
        if os.environ.get('CLAUDE_EXPORTER_NO_BROWSER')!='1':
            try: webbrowser.open(url)
            except Exception: pass
        try:server.serve_forever(poll_interval=.3)
        except KeyboardInterrupt:pass

if __name__=='__main__':main()
