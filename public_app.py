#!/usr/bin/env python3
"""Constrained HTTP backend for a public HTTPS reverse proxy.

Only the proxy should be internet-facing. This process listens on loopback and
keeps uploaded documents in process memory; it does not authenticate users.
"""
import hmac
import json
import os
import threading
from urllib.parse import urlsplit

import app
import exporter

PUBLIC_LIMIT = 20 * 1024 * 1024

def configure_limits():
    app.MAX_INPUT = PUBLIC_LIMIT
    exporter.MAX_INPUT = PUBLIC_LIMIT
    exporter.MAX_EXPANDED = 64 * 1024 * 1024
    exporter.MAX_FILES = 1000

class PublicServer(app.Server):
    # A restart must be able to bind while previous connections are in TIME_WAIT.
    # On the Linux deployment, an active listener still prevents another bind.
    allow_reuse_address = True
    def __init__(self, address, handler):
        self.slots = threading.BoundedSemaphore(8)
        self.conversion_slots = threading.BoundedSemaphore(2)
        super().__init__(address, handler)
    def get_request(self):
        client, address = super().get_request()
        client.settimeout(30)
        return client, address
    def process_request(self, request, address):
        if not self.slots.acquire(blocking=False):
            try:
                request.sendall(b'HTTP/1.1 503 Service Unavailable\r\nConnection: close\r\nContent-Length: 0\r\nRetry-After: 10\r\n\r\n')
            except OSError:
                pass
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, address)
        except Exception:
            self.slots.release()
            raise
    def process_request_thread(self, request, address):
        try:
            super().process_request_thread(request, address)
        finally:
            self.slots.release()

class PublicHandler(app.Handler):
    def _authorized(self):
        return (self.headers.get('Origin', '') == self.server.public_origin and
                hmac.compare_digest(self.headers.get('X-Session-Token', ''), app.TOKEN))
    def do_GET(self):
        if urlsplit(self.path).path == '/api/session':
            self._json(200, {'token': app.TOKEN, 'mode': 'public'})
            return
        super().do_GET()
    def do_POST(self):
        path = urlsplit(self.path).path
        if path == '/api/shutdown':
            self._json(404, {'error':'Not found'})
            return
        if path not in ('/api/inspect', '/api/export') or not self._authorized():
            super().do_POST()
            return
        if not self.server.conversion_slots.acquire(blocking=False):
            body = json.dumps({'error': '服务器繁忙，请稍后重试。'}, ensure_ascii=False).encode('utf-8')
            self._respond(503, body, 'application/json; charset=utf-8', {'Retry-After': '10'})
            return
        try:
            super().do_POST()
        finally:
            self.server.conversion_slots.release()

def main():
    origin = os.environ.get('CLAUDE_EXPORTER_PUBLIC_ORIGIN', '')
    parts = urlsplit(origin)
    if parts.scheme != 'https' or not parts.hostname or parts.path or parts.query or parts.fragment or parts.username or parts.password:
        raise SystemExit('Set CLAUDE_EXPORTER_PUBLIC_ORIGIN to the exact HTTPS origin')
    configure_limits()
    port = int(os.environ.get('CLAUDE_EXPORTER_PUBLIC_PORT', '18760'))
    with PublicServer(('127.0.0.1', port), PublicHandler) as server:
        server.public_origin = origin
        server.serve_forever(poll_interval=.3)

if __name__ == '__main__':
    main()
