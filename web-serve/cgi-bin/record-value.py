#!/usr/bin/env python3

import cgi, cgitb

import cgi
import cgitb
import datetime

cgitb.enable()

print("Content-type:text/html\n\n")

form = cgi.FieldStorage()

now = datetime.datetime.now()
activity = form['activity'].value

with open('record.txt','a') as f:
    f.write('{}\t{}\n'.format(now.isoformat(), activity))

print('{}: {}'.format(now.isoformat(), activity))
