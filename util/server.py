import argparse
import sys
from builtins import Exception
from http.server import HTTPServer, SimpleHTTPRequestHandler

from werkzeug.serving import ForkingMixIn


class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        return super(CORSRequestHandler, self).end_headers()

    def do_OPTIONS(self):
        self.do_GET()


class ForkingHTTPServer(ForkingMixIn, HTTPServer):
    def finish_request(self, request, client_address):
        try:
            request.settimeout(15)
            # "super" can not be used because BaseServer is not created from object
            HTTPServer.finish_request(self, request, client_address)
        except Exception as e:
            print(f"[-] {e}")


class WebServer:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

    def start(self):
        httpd = ForkingHTTPServer((f'{self.ip}', self.port), CORSRequestHandler)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            httpd.server_close()
            exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Simple CORS Webserver")
    parser.add_argument("ip", help="Listen address", type=str)
    parser.add_argument("port", help="Listen port", type=int)
    args = parser.parse_args()

    server = WebServer(ip=args.ip, port=args.port)
    server.start()
