#!/usr/bin/env python3

import base64
import bcrypt
import datetime
import functools
import json
import os

import tornado.web
import psycopg2
import psycopg2.extras

session_timeout_days = 2

@functools.lru_cache()
def get_query(name):
    filename = os.path.join(
        os.path.dirname(__file__),
        'sql_queries',
        '{}.sql'.format(name)
    )
    return open(filename).read()


def initial_setup(database):
    conn = psycopg2.connect(database=database,
                            cursor_factory=psycopg2.extras.NamedTupleCursor)
    with conn:
        with conn.cursor() as cur:
            cur.execute(get_query('initial_setup'))


def create_user(conn, username, password, email_address = None):
    salt = bcrypt.gensalt()
    hashed_pw = bcrypt.hashpw(password, salt)

    with conn:
        with conn.cursor() as cur:
            cur.execute(get_query('create_user'),
                        dict(username = username,
                             hashed_pw = hashed_pw,
                             email_address = email_address,
                        ))

def setup_default_activities(conn, user_id):
    update_activities(conn, user_id,
                      [{'activity_name': 'home',
                        'activity_color': 'DarkGreen',
                        'display': True,
                        },

                       {'activity_name': 'work',
                        'activity_color': 'Tomato',
                        'display': True,
                        },

                       {'activity_name': 'travel',
                        'activity_color': 'DarkOrange',
                        'display': True,
                        },

                       {'activity_name': 'sleep',
                        'activity_color': 'DarkSlateBlue',
                        'display': True,
                        },

                       {'activity_name': 'errands',
                        'activity_color': 'Cyan',
                        'display': True,
                        },

                       {'activity_name': 'out',
                        'activity_color': 'Silver',
                        'display': True,
                        },
                      ])


def generate_session_id():
    return base64.b64encode(os.urandom(16)).decode('ascii')


def log_in(conn, username, password):
    with conn, conn.cursor() as cur:
        cur.execute(get_query('look_up_user'),
                    dict(username = username))
        record = cur.fetchone()


    output = {
        'user_id': None,
        'password_matches': False,

        'session_id': None,
        'session_counter': None,
        'session_expiration': None,
    }


    if record is None:
        return output

    output['user_id'] = record.user_id
    password_matches = bcrypt.checkpw(password, record.hashed_pw)
    output['password_matches'] = password_matches

    if not password_matches:
        return output


    session_id = generate_session_id()
    output['session_id'] = session_id
    session_expiration = (datetime.datetime.now() +
                          datetime.timedelta(days=session_timeout_days))
    output['session_expiration'] = session_expiration

    salt = bcrypt.gensalt()
    hashed_session_id = bcrypt.hashpw(session_id, salt)

    with conn, conn.cursor() as cur:
        cur.execute(get_query('new_session'),
                    dict(user_id = record.user_id,
                         hashed_session_id = hashed_session_id,
                         session_expiration = session_expiration,
                    ))
        result = cur.fetchone()
        output['session_counter'] = result.session_counter

    return output


def check_session_id(conn, user_id, session_counter, session_id):
    with conn, conn.cursor() as cur:
        cur.execute(get_query('look_up_session'),
                    dict(session_counter = session_counter,
                         user_id = user_id))
        record = cur.fetchone()

    output = {
        'session_counter_exists': False,
        'has_correct_session_id': False,
        'session_active': False,
    }

    if record:
        output['session_counter_exists'] = True
    else:
        return output

    if bcrypt.checkpw(session_id, record.hashed_session_id):
        output['has_correct_session_id'] = True
    else:
        return output

    if record.session_active:
        output['session_active'] = True
    else:
        return output

    return output


def purge_old_session_ids(database):
    conn = psycopg2.connect(database=database,
                            cursor_factory=psycopg2.extras.NamedTupleCursor)

    with conn, conn.cursor() as cur:
        cur.execute(get_query('purge_old_session_ids'))


def log_out(conn, user_id, session_counter, session_id):
    res = check_session_id(conn, user_id, session_counter, session_id)

    if res['session_counter_exists']:
        with conn, conn.cursor() as cur:
            cur.execute(get_query('delete_session'),
                        dict(session_counter = session_counter))


def extend_session(conn, session_counter):
    session_expiration = (datetime.datetime.now() +
                          datetime.timedelta(days=session_timeout_days))
    with conn, conn.cursor() as cur:
        cur.execute(get_query('extend_session'),
                    dict(session_counter = session_counter,
                         session_expiration = session_expiration))


def update_activities(conn, user_id, params):
    with conn, conn.cursor() as cur:
        batch_params = [{'user_id': user_id,
                         'activity_id': i,
                         'activity_name': p['activity_name'],
                         'activity_color': p['activity_color'],
                         'display': p['display']}
                       for i,p in enumerate(params)]
        psycopg2.extras.execute_batch(cur,
                                      get_query('update_activity'),
                                      batch_params)


def read_activity_map(conn, user_id):
    with conn, conn.cursor() as cur:
        cur.execute(get_query('read_activity_map'),
                    dict(user_id = user_id))
        return [row._asdict() for row in cur.fetchall()]


def load_text_file(database, text_file, user_name):
    conn = psycopg2.connect(database=database,
                            cursor_factory=psycopg2.extras.NamedTupleCursor)

    with conn, conn.cursor() as cur, open(text_file) as file:
        for line in file:
            time,activity = line.split()
            time = dateutil.parser.parse(time)



class DatabaseWebHandler(tornado.web.RequestHandler):
    def initialize(self, database):
        self.database = database

    @property
    def conn(self):
        if hasattr(self, '_conn'):
            return self._conn


        self._conn = psycopg2.connect(
            database=self.database,
            cursor_factory=psycopg2.extras.NamedTupleCursor)

        return self._conn

    def validate_session_id(self):
        user_id = self.get_cookie('user_id')
        session_counter = self.get_cookie('session_counter')
        session_id = self.get_cookie('session_id')

        if (user_id is None or
            session_counter is None or
            session_id is None):

            self.set_status(403)
            return

        res = check_session_id(self.conn,
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

        if signed_in:
            user_id = self.get_cookie('user_id')
            activities = read_activity_map(self.conn, user_id)
        else:
            activities = []

        cache = {'activities': activities}
        cache_definition = "var cache = {};".format(json.dumps(cache))
        dummy_text = "console.log('template not replaced');"
        html = html.replace(dummy_text, cache_definition)

        self.set_status(200)
        self.set_header('Content-type', 'text/html')
        self.write(html)



class RecordTransaction(DatabaseWebHandler):
    def post(self):
        self.set_header('Content-type', 'text/html')

        now = datetime.datetime.now()
        activity = self.get_argument('activity')

        entry = '{}\t{}\n'.format(now.isoformat(), activity)
        self.write(entry)



class ReadLog(DatabaseWebHandler):
    def get(self):
        if not self.validate_session_id():
            return

        self.set_header('Content-type', 'text/html')

        user_id = self.get_cookie('user_id')


        now = datetime.datetime.now()
        activity = 'sleep'
        entry = '{}\t{}\n'.format(now.isoformat(), activity)
        self.write(entry)

class LogIn(DatabaseWebHandler):
    def post(self):
        params = json.loads(self.request.body.decode('utf-8'))

        results = log_in(self.conn, params['username'], params['password'])

        self.set_header('Content-type', 'text/html')

        if results['session_counter'] is None:
            self.clear_cookie('user_id')
            self.clear_cookie('session_counter')
            self.clear_cookie('session_id')
        else:
            self.set_cookie('user_id', results['user_id'])
            self.set_cookie('session_counter', str(results['session_counter']))
            self.set_cookie('session_id', results['session_id'])


        return_params = {
            'password_matches': results['password_matches'],
            'session_id': results['session_id'],
            'session_counter': results['session_counter'],
        }

        self.write(json.dumps(return_params))


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

        res = log_out(self.conn, user_id, session_counter, session_id)


class UpdateSettings(DatabaseWebHandler):
    def post(self):
        if not self.validate_session_id():
            return

        user_id = self.get_cookie('user_id')
        params = json.loads(self.request.body.decode('utf-8'))

        update_activities(self.conn, user_id, params)



def main():
    database = 'postgres'
    initial_setup(database)

    conn = psycopg2.connect(database=database,
                            cursor_factory=psycopg2.extras.NamedTupleCursor)
    import IPython; IPython.embed()

if __name__=='__main__':
    main()
