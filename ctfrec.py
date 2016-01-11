from __future__ import (
    print_function,
    division,
)
from time import time
import sys
import json
import requests
import logging
import base64
from bottle import run, route, post, request


DEBUG = True
LHOST = '0.0.0.0'
HOST = '127.0.0.1'
PORT = 9999


class ServerError(BaseException):
    pass


class ClientError(BaseException):
    pass


def load_request(possible_keys):
    try:
        pdata = json.load(request.body)
    except ValueError as e:
        pdata = {"ValueError": "%s" % e}
    for k in possible_keys:
        if k not in pdata:
            pdata[k] = None
    return pdata


class Server(object):
    def __init__(self, addr=None):
        self.host = LHOST
        self.port = PORT
        if addr is not None:
            (self.host, self.port) = addr
        self.cmds = []

    def run(self):
        route('/')(self.handle_index)
        route('/cmds')(self.handle_cmds)
        post('/cmd')(self.handle_cmd_post)
        run(host=self.host, port=self.port, debug=DEBUG)

    def pr_dbg(self, msg):
        msg = '%s [DBG] server %s' % (int(time()), msg)
        if DEBUG:
            print(msg)
        logging.debug(msg)

    def pr_inf(self, msg):
        msg = '%s [INF] server %s' % (int(time()), msg)
        print(msg)
        logging.info(msg)

    def handle_index(self):
        self.pr_inf('handle_index')
        success = True
        resp = 'CTF Record API is running'
        return json.dumps({'success': success, 'resp': resp}) + '\n'

    def handle_cmds(self):
        ip = request.environ.get('REMOTE_ADDR')
        self.pr_inf('handle_cmds %s' % ip)
        if ip != '127.0.0.1':
            success = False
            resp = ('No remote requests allowed, your ip %s' % ip)
            return json.dumps({'success': success, 'resp': resp}) + '\n'
        cmds = self.load_cmds()
        success = True
        return json.dumps({'success': success, 'resp': cmds}) + '\n'

    def load_cmds(self):
        return self.cmds

    def handle_cmd_post(self):
        pdata = load_request(['ts', 'cmd', 'src'])
        pdata['server_ts'] = time()
        if pdata['src'] is None:
            pdata['src'] = {}
        pdata['src']['remote_ip'] = request.environ.get('REMOTE_ADDR')
        success, resp_str = self.rec_cmd(pdata)
        resp = {'str': resp_str}
        return json.dumps({'success': success, 'resp': resp}) + '\n'

    def rec_cmd(self, cmd):
        self.cmds.append(cmd)
        # semaphore to lock output or sqlite
        try:
            msg = 'rec_cmd: %s' % json.dumps(cmd)
        except TypeError as e:
            msg = 'rec_cmd: %s, typeerror %s' % (cmd, e)
        self.pr_inf(msg)
        return (True, msg)


class Client(object):
    """Importable object to wrap REST calls into python"""
    def __init__(self, addr=None):
        self.host = HOST
        self.port = PORT
        if addr is not None:
            (self.host, self.port) = addr

    def pr_dbg(self, msg):
        msg = '%s [DBG] client %s' % (int(time()), msg)
        if DEBUG:
            print(msg)
        logging.debug(msg)

    def pr_err(self, msg):
        msg = '%s [ERR] client %s' % (int(time()), msg)
        print(msg)
        logging.error(msg)

    def url(self, endpoint):
        return 'http://%s:%s%s' % (self.host, self.port, endpoint)

    def get(self, endpoint):
        try:
            resp = requests.get(self.url(endpoint))
        except requests.ConnectionError as e:
            raise ClientError(e)
        try:
            resp_val = json.loads(resp.text)
        except ValueError as e:
            # remote server fails and kills connection or returns nothing
            raise ClientError(e)
        return resp_val

    def post(self, endpoint, data):
        try:
            resp = requests.post(self.url(endpoint), data=json.dumps(data))
        except requests.ConnectionError as e:
            raise ClientError(e)
        try:
            resp_val = json.loads(resp.text)
        except ValueError as e:
            # remote server fails and kills connection or returns nothing
            raise ClientError(e)
        return resp_val

    def is_running(self):
        try:
            rjson = self.get('/')
        except ClientError:
            return False
        return rjson['success']

    def cmd(self, cmd, session=None, user=None, ctf_user=None):
        opts = {}
        opts['ts'] = time()
        opts['cmd'] = cmd
        opts['src'] = {}
        opts['src']['session'] = session
        opts['src']['user'] = user
        opts['src']['ctf_user'] = user
        try:
            rjson = self.post('/cmd', opts)
        except ClientError:
            return False
        return True  # rjson

    def get_cmds(self):
        try:
            rjson = self.get('/cmds')
        except ClientError:
            return []
        return rjson

    def get_cmds_decoded(self):
        try:
            rjson = self.get('/cmds')
        except ClientError:
            return []
        cmds = []
        for j in rjson['resp']:
            try:
                decoded = base64.b64decode(j['cmd']).decode('ascii')
            except TypeError as e:
                # print('TypeError %s' % e)
                decoded = j['cmd']
            j['cmd'] = decoded
            cmds.append(j)
        return cmds


def getopts(argv):
    return {}


def main(opts):
    backend = Server()
    backend.run()
    return 0


if __name__ == '__main__':
    sys.exit(main(getopts(sys.argv)))
