#!/usr/bin/env python3

import argparse
from glob import glob

import tornado.httpserver
import tornado.ioloop
import tornado.log

import sql_backend
import tornado_sql

def run(database, port, use_ssl=True):
    conn = sql_backend.make_connection(database)

    sql_backend.initial_setup(conn)

    tornado.log.enable_pretty_logging()
    app = tornado_sql.make_app(conn)

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
        lambda :sql_backend.purge_old_session_ids(conn),
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
    try:
        main()
    except Exception:
        import pdb, traceback
        traceback.print_exc()
        pdb.post_mortem()
