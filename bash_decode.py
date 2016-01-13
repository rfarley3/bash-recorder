#!/usr/bin/env python
import sys
import json
import base64
import time


def follow(thefile, full):
    for line in thefile.readlines():
        yield line
    thefile.seek(0,2)
    while True:
        line = thefile.readline()
        if not line:
            time.sleep(0.1)
            continue
        yield line


def pretty_print(line):
    data = json.loads(line)
    decoded = 'invalid or none command'
    if 'cmd' in data and data['cmd'] is not None:
        decoded = base64.b64decode(data['cmd'])
    data['cmd'] = decoded
    sess = 'no_session'
    if 'src' in data and 'session' in data['src']:
        sess = data['src']['session']
    user = 'unk_user'
    if 'src' in data and 'user' in data['src']:
        user = data['src']['user']
    # print('%s' % json.dumps(data))
    return '%s %s:%s %s %s' % (int(data['server_ts']), data['src']['remote_ip'], user, sess, data['cmd'])


def main(logfilename, full=True):
    print("Open bash recorder logfile %s" % logfilename)
    logfile = open(logfilename,'r')
    loglines = follow(logfile, full)
    for line in loglines:
        # print(line)
        s = pretty_print(line)
        print(s)


if __name__ == '__main__':
    main('bashrec.log')

