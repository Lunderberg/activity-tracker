#!/usr/bin/env python3

import json
import os

import dateutil.parser

import tornado.web

import sql_backend


def make_app(conn):
    web_serve_path = os.path.join(os.path.dirname(__file__),
                                  'web-serve')

    return tornado.web.Application([
        ('/(index.html)?',
         IndexHtml,
         dict(conn = conn,
              web_serve_path = web_serve_path),
        ),

        ('/record_transaction',
         RecordTransaction,
         dict(conn = conn),
        ),

        ('/read_logs',
         ReadLogs,
         dict(conn = conn),
        ),

        ('/log_in',
         LogIn,
         dict(conn = conn),
        ),

        ('/log_out',
         LogOut,
         dict(conn = conn),
        ),

        ('/refresh',
         RefreshSession,
         dict(conn = conn),
        ),

        ('/update_settings',
         UpdateSettings,
         dict(conn = conn),
        ),

        ('/edit_data',
         EditData,
         dict(conn = conn),
         ),

        (r'/(.*)', StaticHandler, {'path': web_serve_path}),
    ])

class StaticHandler(tornado.web.StaticFileHandler):
    def parse_url_path(self, url_path):
        if not url_path or url_path.endswith('/'):
            url_path += 'index.html'
        return url_path


class DatabaseWebHandler(tornado.web.RequestHandler):
    def initialize(self, conn):
        self.conn = conn

    def validate_session_id(self):
        user_id = self.get_cookie('user_id')
        session_counter = self.get_cookie('session_counter')
        session_id = self.get_cookie('session_id')

        if (user_id is None or
            session_counter is None or
            session_id is None):

            self.set_status(403)
            return

        res = sql_backend.check_session_id(
            self.conn,
            user_id,
            session_counter,
            session_id)

        if res['session_active']:
            self.set_status(200)
        elif res['has_correct_session_id']:
            # TODO: Handle this case better to display "session
            # expired" or something like that
            self.set_status(403)
        else:
            self.set_status(403)

        return res['session_active']


class IndexHtml(DatabaseWebHandler):
    def initialize(self, web_serve_path, *args, **kwargs):
        super().initialize(*args, **kwargs)
        self.web_serve_path = web_serve_path

    def get(self, regex_match):
        filepath = os.path.join(self.web_serve_path, 'index.html')
        with open(filepath) as f:
            html = f.read()

        signed_in = self.validate_session_id()
        user_id = self.get_cookie('user_id')

        cache = sql_backend.get_cache_data(self.conn, user_id, signed_in)

        cache_definition = "var cache = {};".format(json.dumps(cache))
        dummy_text = "console.log('template not replaced');"
        html = html.replace(dummy_text, cache_definition)

        self.set_status(200)
        self.set_header('Content-type', 'text/html')
        self.write(html)



class RecordTransaction(DatabaseWebHandler):
    def post(self):
        if not self.validate_session_id():
            return

        user_id = self.get_cookie('user_id')

        params = json.loads(self.request.body.decode('utf-8'))
        activity_id = params['activity_id']

        sql_backend.insert_transaction(self.conn, user_id, activity_id)

        cache_data = sql_backend.get_cache_data(self.conn, user_id)

        self.set_header('Content-type', 'text/html')
        self.write(json.dumps(cache_data))



class ReadLogs(DatabaseWebHandler):
    def get(self):
        if not self.validate_session_id():
            return

        user_id = self.get_cookie('user_id')

        window_start = dateutil.parser.parse(self.get_argument('window-start'))
        window_end = dateutil.parser.parse(self.get_argument('window-end'))
        logs = sql_backend.read_logs(self.conn, user_id,
                                     min_time = window_start,
                                     max_time = window_end,
                                     as_str=True)

        output = {'window_start': window_start.isoformat(),
                  'window_end': window_end.isoformat(),
                  'logs': logs}

        self.set_header('Content-type', 'text/html')
        self.write(json.dumps(output))


class LogIn(DatabaseWebHandler):
    def post(self):
        params = json.loads(self.request.body.decode('utf-8'))

        results = sql_backend.log_in(self.conn,
                                     params['username'],
                                     params['password'])

        self.set_header('Content-type', 'text/html')

        if results['session_counter'] is None:
            signed_in = False
            self.clear_cookie('user_id')
            self.clear_cookie('session_counter')
            self.clear_cookie('session_id')
        else:
            signed_in = True
            self.set_cookie('user_id', results['user_id'])
            self.set_cookie('session_counter', str(results['session_counter']))
            self.set_cookie('session_id', results['session_id'])

        cache_data = sql_backend.get_cache_data(self.conn,
                                                results['user_id'],
                                                signed_in)
        self.set_header('Content-type', 'text/html')
        self.write(json.dumps(cache_data))


class RefreshSession(DatabaseWebHandler):
    def get(self):
        self.validate_session_id()


class LogOut(DatabaseWebHandler):
    def post(self):
        user_id = self.get_cookie('user_id')
        session_counter = self.get_cookie('session_counter')
        session_id = self.get_cookie('session_id')

        if (user_id is None or
            session_counter is None or
            session_id is None):

            self.set_status(401)
            return

        res = sql_backend.log_out(self.conn,
                                  user_id,
                                  session_counter,
                                  session_id)


class UpdateSettings(DatabaseWebHandler):
    def post(self):
        if not self.validate_session_id():
            return

        user_id = self.get_cookie('user_id')
        params = json.loads(self.request.body.decode('utf-8'))

        sql_backend.update_activities(self.conn, user_id, params)


class EditData(DatabaseWebHandler):
    def post(self):
        if not self.validate_session_id():
            return

        user_id = self.get_cookie('user_id')
        params = json.loads(self.request.body.decode('utf-8'))

        window_range = (dateutil.parser.parse(params['window_min']),
                        dateutil.parser.parse(params['window_max']))

        new_transactions = [
            {'activity_id': int(txn['activity_id']),
             'txn_date': dateutil.parser.parse(txn['txn_date']),
             }
            for txn in params['activities']
        ]

        sql_backend.overwrite_transactions(
            self.conn, user_id,
            window_range, new_transactions)

        cache_data = sql_backend.get_cache_data(self.conn, user_id)
        self.set_header('Content-type', 'text/html')
        self.write(json.dumps(cache_data))
