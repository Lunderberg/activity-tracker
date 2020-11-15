#!/usr/bin/env python3

import base64
import bcrypt
import datetime
import functools
import os
import sqlite3
import uuid

import dateutil.parser

session_timeout_days = 2

@functools.lru_cache()
def get_query(name):
    filename = os.path.join(
        os.path.dirname(__file__),
        'sql_queries',
        '{}.sql'.format(name)
    )
    return open(filename).read()

def make_connection(database = None):
    if database is None:
        database = os.path.join(os.path.dirname(__file__), 'activities.db')

    conn = sqlite3.connect(database, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn


def initial_setup(conn):
    with conn:
        conn.executescript(get_query('initial_setup'))


def create_user(conn, username, password, email_address = None):
    salt = bcrypt.gensalt()
    hashed_pw = bcrypt.hashpw(password, salt)
    user_id = str(uuid.uuid4())

    with conn:
        conn.execute(get_query('create_user'),
                     dict(user_id=user_id,
                          username = username,
                          hashed_pw = hashed_pw,
                          email_address = email_address,
                          ))

    setup_default_activities(conn, user_id)

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
    with conn:
        cur = conn.execute(get_query('look_up_user'),
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

    output['user_id'] = record['user_id']
    password_matches = bcrypt.checkpw(password, record['hashed_pw'])
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

    with conn:
        cur = conn.execute(get_query('new_session'),
                           dict(user_id = record['user_id'],
                                hashed_session_id = hashed_session_id,
                                session_expiration = session_expiration,
                                ))
        output['session_counter'] = cur.lastrowid

    return output


def check_session_id(conn, user_id, session_counter, session_id):
    with conn:
        cur = conn.execute(get_query('look_up_session'),
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

    if bcrypt.checkpw(session_id, record['hashed_session_id']):
        output['has_correct_session_id'] = True
    else:
        return output

    if record['session_active']:
        output['session_active'] = True
    else:
        return output

    return output


def purge_old_session_ids(conn):
    with conn:
        conn.execute(get_query('purge_old_session_ids'))


def log_out(conn, user_id, session_counter, session_id):
    res = check_session_id(conn, user_id, session_counter, session_id)

    if res['session_counter_exists']:
        with conn:
            conn.execute(get_query('delete_session'),
                         dict(session_counter = session_counter))


def extend_session(conn, session_counter):
    session_expiration = (datetime.datetime.now() +
                          datetime.timedelta(days=session_timeout_days))
    with conn:
        conn.execute(get_query('extend_session'),
                     dict(session_counter = session_counter,
                          session_expiration = session_expiration))


def update_activities(conn, user_id, params):
    with conn:
        batch_params = [{'user_id': user_id,
                         'activity_id': i,
                         'activity_name': p['activity_name'],
                         'activity_color': p['activity_color'],
                         'display': p['display']}
                       for i,p in enumerate(params)]
        conn.executemany(get_query('update_activity'), batch_params)


def read_activity_map(conn, user_id):
    with conn:
        cur = conn.execute(get_query('read_activity_map'),
                           dict(user_id = user_id))
        return [dict(row) for row in cur.fetchall()]


def load_text_file(conn, user_id, text_filepath):
    activity_map = {d['activity_name']:d['activity_id']
                    for d in read_activity_map(conn, user_id)}

    with conn, open(text_filepath) as f:
        batch_params = []
        for line in f:
            line = line.split()
            if line:
                time,activity = line
                time = dateutil.parser.parse(time)
                batch_params.append({
                    'user_id': user_id,
                    'txn_date': time,
                    'activity_id': activity_map[activity],
                })

        conn.executemany(get_query('insert_transaction'), batch_params)

def insert_transaction(conn, user_id, activity_id, txn_date=None):
    if txn_date is None:
        txn_date = datetime.datetime.now()

    with conn:
        conn.execute(get_query('insert_transaction'),
                     dict(user_id = user_id,
                          activity_id = activity_id,
                          txn_date = txn_date))


def overwrite_transactions(conn, user_id, window_range, new_transactions):
    for txn in new_transactions:
        if not (window_range[0] <= txn['txn_date'] <= window_range[1]):
            raise ValueError('Replacement transaction not in range')

    batch_params = [ {'user_id': user_id,
                      'activity_id': txn['activity_id'],
                      'txn_date': txn['txn_date'],
                      }
                     for txn in new_transactions]

    with conn:
        conn.execute(get_query('delete_transactions'),
                     dict(user_id = user_id,
                          window_start = window_range[0],
                          window_end = window_range[1]))

        conn.executemany(get_query('insert_transaction'), batch_params)



def read_logs(conn, user_id,
              min_time=None, max_time=None, num_days=None,
              as_str=False):
    if min_time is None and max_time is None and num_days is not None:
        max_time = datetime.datetime.now()
        min_time = max_time - datetime.timedelta(days = num_days)

    elif min_time is not None and max_time is None and num_days is not None:
        max_time = min_time + datetime.timedelta(days = num_days)

    elif min_time is None and max_time is not None and num_days is not None:
        min_time = max_time - datetime.timedelta(days = num_days)

    elif min_time is not None and max_time is None and num_days is not None:
        max_time = datetime.datetime.now()


    with conn:
        cur = conn.execute(get_query('read_logs'),
                           dict(user_id = user_id,
                                min_time = min_time,
                                max_time = max_time))
        output = [dict(row) for row in cur.fetchall()]

    if as_str:
        for log in output:
            log['txn_date'] = log['txn_date'].isoformat()

    return output


# From https://stackoverflow.com/a/58295869/2689797
def timedelta_format(dt):
    diff = dt.total_seconds()
    #d = int(diff / 86400)
    d = 0
    h = int((diff - (d * 86400)) / 3600)
    m = int((diff - (d * 86400 + h * 3600)) / 60)
    s = int((diff - (d * 86400 + h * 3600 + m *60)))
    if d > 0:
        fdiff = '{d}d {h}h {m}m {s}s'
    elif h > 0:
        fdiff = '{h}h {m}m {s}s'
    elif m > 0:
        fdiff = '{m}m {s}s'
    else:
        fdiff = '{s}s'

    fdiff = fdiff.format(d=d, h=h, m=m, s=s)
    return fdiff

def summarize_recent_activity(conn, user_id, summary_windows, as_str=False):
    summary_windows = {'summary_window{}'.format(i)
                       :
                       '-{} seconds'.format(dt.total_seconds())

                       for i,dt in enumerate(summary_windows)}

    query = (get_query('summarize_recent_activity')
             .replace('(:summary_window)',
                      ','.join('(:{})'.format(k) for k in summary_windows))
    )
    params = {'user_id': user_id,
              **summary_windows}

    with conn:
        cur = conn.execute(query, params)
        output = [dict(row) for row in cur.fetchall()]
    import IPython; IPython.embed()

    if as_str:
        for row in output:
            row['summary_window'] = timedelta_format(row['summary_window'])
            row['time_spent'] = timedelta_format(row['time_spent'])

    return output


def summarize_by_day(conn, user_id, as_primitive=False):
    with conn, conn.cursor() as cur:
        cur.execute(get_query('summarize_by_day'),
                    dict(user_id = user_id))
        output = [row._asdict() for row in cur.fetchall()]

    if as_primitive:
        for row in output:
            row['window_start'] = str(row['window_start'])
            row['window_end'] = str(row['window_end'])
            row['time_spent'] = row['time_spent'].total_seconds()

    return output




def get_cache_data(conn, user_id, signed_in=True):
    if signed_in:
        return {'signed_in': signed_in,
                'activities': read_activity_map(conn, user_id),
                'logs': read_logs(conn, user_id, num_days=8, as_str=True),
                'summary_recent': summarize_recent_activity(
                    conn, user_id,
                    summary_windows = [datetime.timedelta(days=d) for d in [1,7,30]],
                    as_str = True,
                ),
                'summary_by_day': summarize_by_day(conn, user_id, as_primitive=True),
        }
    else:
        return {'signed_in': signed_in,
                'activities': [],
                'logs': [],
                'summary_recent': [],
                'summary_by_day': [],
        }





def main():
    conn = make_connection()
    initial_setup(conn)

    #create_user(conn, 'asdf', 'qwer')
    #load_text_file(conn, user_id, 'record.txt')


    res = log_in(conn, 'asdf', 'qwer')
    user_id = res['user_id']

    res_session = check_session_id(conn, user_id,
                                   res['session_counter'],
                                   res['session_id'])

    extend_session(conn, res['session_counter'])

    activity_map = read_activity_map(conn, user_id)

    insert_transaction(conn, user_id, 0)

    overwrite_transactions(
        conn, user_id,
        (datetime.datetime.now() - datetime.timedelta(days=1),
         datetime.datetime.now()),
        [{'activity_id': 0,
          'txn_date': datetime.datetime.now() - datetime.timedelta(hours=12)},
         {'activity_id': 1,
          'txn_date': datetime.datetime.now() - datetime.timedelta(hours=8)},
         {'activity_id': 2,
          'txn_date': datetime.datetime.now() - datetime.timedelta(hours=4)},
         ])

    logs = read_logs(conn, user_id, num_days = 7, as_str=True)

    # recent = summarize_recent_activity(
    #     conn, user_id,
    #     summary_windows = [datetime.timedelta(days=d) for d in [1,7,30]])

    import IPython; IPython.embed()

if __name__=='__main__':
    try:
        main()
    except Exception:
        import traceback, pdb
        traceback.print_exc()
        pdb.post_mortem()
