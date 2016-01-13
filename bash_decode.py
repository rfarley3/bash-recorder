#!/usr/bin/env python
import sys
import json
import base64


for line in sys.stdin:
    # print(line)
    data = json.loads(line)
    # print(data)
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
    print('%s %s:%s %s %s' % (int(data['server_ts']), data['src']['remote_ip'], user, sess, data['cmd']))
