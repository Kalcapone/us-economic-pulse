#!/usr/bin/env python3
"""
Local proxy server for US Economic Pulse.
Serves static files and proxies /fred requests to the FRED API
to work around browser CORS restrictions.
"""
import http.server
import urllib.request
import urllib.parse
import os

PORT = int(os.environ.get('PORT', 8080))
FRED_API = 'https://api.stlouisfed.org/fred/series/observations'

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/fred'):
            self.proxy_fred()
        else:
            super().do_GET()

    def proxy_fred(self):
        # Strip /fred prefix and pass the rest as query string
        qs = self.path[len('/fred'):]
        target = FRED_API + qs
        try:
            req = urllib.request.Request(target, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as resp:
                body = resp.read()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        except Exception as e:
            self.send_response(502)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(str(e).encode())

    def log_message(self, fmt, *args):
        # Suppress noisy access logs; only print errors
        if int(args[1]) >= 400:
            super().log_message(fmt, *args)

os.chdir(os.path.dirname(os.path.abspath(__file__)))
print(f'Proxy running at http://localhost:{PORT}')
http.server.HTTPServer(('', PORT), ProxyHandler).serve_forever()
