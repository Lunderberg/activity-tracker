#!/usr/bin/env python3

import datetime
import os

import tornado.web

record_file = os.path.join(os.path.dirname(__file__),
                           'web-serve', 'record.txt')

class RecordValue(tornado.web.RequestHandler):
    def post(self):
        self.set_header('Content-type', 'text/html')

        now = datetime.datetime.now()
        activity = self.get_argument('activity')
        with open(record_file, 'a') as f:
            f.write('{}\t{}\n'.format(now.isoformat(), activity))

        with open(record_file) as f:
            self.write(f.read())
