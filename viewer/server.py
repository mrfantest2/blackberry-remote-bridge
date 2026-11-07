#!/usr/bin/env python3
"""Localhost-only, read-only preview of the latest private BlackBerry capture."""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit
from html import escape

PREVIEW = Path('/home/SD/BlackBerryBridge/private-previews/latest.png')
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/':
            body = ('<!doctype html><html><head><meta charset="utf-8"><title>BlackBerry Local Viewer</title>'
                    '<meta name="viewport" content="width=device-width,initial-scale=1"></head>'
                    '<body style="font:16px Arial;background:#17202a;color:white;text-align:center">'
                    '<h2>BlackBerry Torch 9810</h2><p>Private, manually refreshed screenshot. No input control.</p>'
                    '<p><a style="color:#8bd" href="/">Refresh preview</a></p>'
                    '<img alt="BlackBerry screenshot" style="max-width:95%;height:auto;border:1px solid #789" src="/preview.png"></body></html>')
            data=body.encode(); content_type='text/html; charset=utf-8'
        elif path == '/preview.png':
            if not PREVIEW.is_file():
                self.send_error(404, 'Capture unavailable'); return
            data=PREVIEW.read_bytes(); content_type='image/png'
        elif path == '/health':
            data=b'OK'; content_type='text/plain'
        else:
            self.send_error(404); return
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'none'; img-src 'self'; style-src 'unsafe-inline'")
        self.end_headers(); self.wfile.write(data)
    def do_POST(self): self.send_error(405)
    def do_HEAD(self): self.send_error(405)
ThreadingHTTPServer(('127.0.0.1', 18765), Handler).serve_forever()
