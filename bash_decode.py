#!/usr/bin/env python
import sys
import json
import base64


for line in sys.stdin:
    # print(line)
    data = json.loads(line)
    print(data)
    decoded = 'invalid or none command'
    if 'cmd' in data and data['cmd'] is not None:
        decoded = base64.b64decode(data['cmd'])
    data['cmd'] = decoded
    print('%s' % json.dumps(data))
