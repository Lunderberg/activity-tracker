#!/usr/bin/env python3

from glob import glob
from http.server import HTTPServer, CGIHTTPRequestHandler, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
import ssl
import os

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    pass

def main():
    os.chdir(os.path.dirname(__file__))
    os.chdir('web-serve')

    httpd = ThreadingHTTPServer(('0.0.0.0',12345), CGIHTTPRequestHandler)
    certfile = glob('../config/config/live/*/fullchain.pem')[0]
    keyfile = glob('../config/config/live/*/privkey.pem')[0]
    httpd.socket = ssl.wrap_socket(httpd.socket,
                                   certfile=certfile,
                                   keyfile=keyfile,
                                   server_side=True)

    # Forking causes SSL errors
    # https://blog.farville.com/15-line-python-https-cgi-server/
    CGIHTTPRequestHandler.have_fork = False
    httpd.serve_forever()

if __name__=='__main__':
    main()
