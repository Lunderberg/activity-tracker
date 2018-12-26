#!/usr/bin/env python3

from glob import glob
import os

import tornado.httpserver
import tornado.ioloop
import tornado.log
import tornado.web

from record_value import RecordValue

class Handler(tornado.web.StaticFileHandler):
    def parse_url_path(self, url_path):
        if not url_path or url_path.endswith('/'):
            url_path += 'index.html'
        return url_path

def make_app():
    web_serve_path = os.path.join(os.path.dirname(__file__),
                                  'web-serve')

    return tornado.web.Application([
        (r'/cgi-bin/record-value.py', RecordValue),
        (r'/(.*)', Handler, {'path': web_serve_path}),
    ])


def main():
    certfile = sorted(glob('config/config/live/*/fullchain.pem'))[-1]
    keyfile = sorted(glob('config/config/live/*/privkey.pem'))[-1]
    print(certfile)

    tornado.log.enable_pretty_logging()
    app = make_app()
    https = tornado.httpserver.HTTPServer(app, ssl_options = {
        'certfile': certfile,
        'keyfile': keyfile,
    })
    https.listen(12345)
    tornado.ioloop.IOLoop.current().start()

if __name__=='__main__':
    main()
