#!/usr/bin/env python3

import argparse
from glob import glob
import os

import tornado.httpserver
import tornado.ioloop
import tornado.log
import tornado.web

import sql_backend

class Handler(tornado.web.StaticFileHandler):
    def parse_url_path(self, url_path):
        if not url_path or url_path.endswith('/'):
            url_path += 'index.html'
        return url_path

def make_app(database):
    web_serve_path = os.path.join(os.path.dirname(__file__),
                                  'web-serve')

    return tornado.web.Application([
        ('/cgi-bin/record-value.py',
         sql_backend.RecordTransaction,
         dict(database = database),
        ),

        ('/record.txt',
         sql_backend.ReadLog,
         dict(database = database),
        ),

        ('/log_in',
         sql_backend.LogIn,
         dict(database = database),
        ),

        ('/log_out',
         sql_backend.LogOut,
         dict(database = database),
        ),

        ('/refresh',
         sql_backend.RefreshSession,
         dict(database = database),
        ),

        (r'/(.*)', Handler, {'path': web_serve_path}),
    ])

def run(database, port, use_ssl=True):
    sql_backend.initial_setup(database)

    tornado.log.enable_pretty_logging()
    app = make_app(database)

    opts = {}
    if use_ssl:
        certfile = glob('config/config/live/*/fullchain.pem')[-1]
        keyfile = glob('config/config/live/*/privkey.pem')[-1]
        opts['ssl_options'] = {
            'certfile': certfile,
            'keyfile': keyfile,
        }

    server = tornado.httpserver.HTTPServer(app, **opts)
    server.listen(port)


    daily_purge = tornado.ioloop.PeriodicCallback(
        sql_backend.purge_old_session_ids,
        24*60*60*1000,
    )
    daily_purge.start()

    tornado.ioloop.IOLoop.current().start()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port',
                        type=int,
                        default=12345,
                        help='The port to listen on (default=12345)')
    parser.add_argument('--http-only',
                        action='store_true',
                        help='Use HTTP (without SSL)')
    parser.add_argument('-d', '--database',
                        type=str,
                        default='postgres',
                        help='Name of database to connect to (default=postgres)')

    args = parser.parse_args()

    run(args.database, args.port, use_ssl = not args.http_only)

    

if __name__=='__main__':
    main()
