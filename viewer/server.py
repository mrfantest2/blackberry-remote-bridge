#!/usr/bin/env python3
"""Read-only BlackBerry screenshot preview, bound exclusively to loopback."""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit
from datetime import datetime

PREVIEW = Path('/home/SD/BlackBerryBridge/private-previews/latest.png')
PAGE = '''<!doctype html><html><head><meta charset="utf-8"><title>BlackBerry Local Viewer</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{font:16px Arial;background:#17202a;color:white;text-align:center;margin:16px}
a{color:#8bd}img{max-width:95%;height:auto;border:1px solid #789}</style></head>
<body><h2>BlackBerry Torch 9810</h2><p>Private, read-only screenshot preview.</p>
<p>Captured: {timestamp}</p><p><a href="/">Refresh page</a></p>
<img alt="Latest BlackBerry screenshot" src="/preview.png"></body></html>'''

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/':
            timestamp = (datetime.fromtimestamp(PREVIEW.stat().st_mtime).astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')
                         if PREVIEW.is_file() else 'Unavailable')
            from html import escape
            data = PAGE.replace('{timestamp}', escape(timestamp)).encode('utf-8')
            content_type = 'text/html; charset=utf-8'
        elif path == '/preview.png':
            if not PREVIEW.is_file():
                self.send_error(404, 'Capture unavailable'); return
            data = PREVIEW.read_bytes(); content_type = 'image/png'
        elif path == '/health':
            data = b'OK'; content_type = 'text/plain; charset=utf-8'
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

if __name__ == '__main__':
    ThreadingHTTPServer(('127.0.0.1', 18765), Handler).serve_forever()
