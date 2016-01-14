# store in /etc/pystartup.py
# in bashrc: export PYTHONSTARTUP=/etc/pystartup.py
# you will need to pip install readline
import atexit


def remote_log_history():
    import readline
    from time import time
    import requests
    import os
    import json
    import base64
    cnt = readline.get_current_history_length()
    for i in xrange(cnt):
        cmd = readline.get_history_item(i + 1)
        data = {}
        data['ts'] = time()
        data['cmd'] = base64.b64encode(cmd.encode('ascii'))
        data['optout'] = None
        if 'STATSOPTOUT' in os.environ:
            data['optout'] = os.environ['STATSOPTOUT']
        data['src'] = {}
        data['src']['user'] = os.environ['USER']
        if 'SESSIP' in os.environ:
            data['src']['ip'] = os.environ['SESSIP']
        pid = os.getpid()
        ppid = os.getppid()
        sessid = 'SESSID'
        if 'SESSID' in os.environ:
            sessid = os.environ['SESSID']
        data['src']['session'] = '%s.%s.%s.py' % (pid, ppid, sessid)
        url = 'http://ctf.local:9999/cmd'
        # print('request: %s' % json.dumps(data))
        try:
            requests.post(url, data=json.dumps(data), timeout=2.0)
        except:  # ConnectionError, HTTPError, Timeout, TooManyRedirects
            pass
    # del readline, time, requests, os, json


atexit.register(remote_log_history)
del atexit, remote_log_history
