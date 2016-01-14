#!/usr/bin/env python
from __future__ import (
    print_function,
)
from time import time, sleep
import sys
import json
import requests
import logging
import base64
import argparse
from collections import deque
from threading import Thread, Lock
from bottle import run, route, post, request
from bottle import ServerAdapter
from wsgiref.simple_server import make_server, WSGIRequestHandler
import ssl


DEBUG = True
LHOST = '0.0.0.0'
HOST = '127.0.0.1'
PORT = 9999
MAX_LEN = 4096  # abitrary max len of submitted cmds
LOG_FILE = 'bashrec.log'
CERT_FILE = 'server.pem'
# openssl req -new -x509 -keyout server.pem -out server.pem -days 365 -nodes


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
    def __init__(self, addr=None, log=LOG_FILE, ssl=False, cert=CERT_FILE):
        self.host = LHOST
        self.port = PORT
        self.ssl = ssl
        self.cert = cert
        if addr is not None:
            (self.host, self.port) = addr
        self.log = log
        self.log_lock = Lock()
        self.inbound_cmds = deque()
        self.cmds = []
        if self.ssl:
            self.ssl_server = self.gen_ssl_server()
        self.collector_thread = Thread(target=self.collect_inbound_cmds)
        self.collector_thread.daemon = True
        self.collector_thread.start()

    def gen_ssl_server(self):
        cert_file = self.cert
        class SSLWSGIRefServer(ServerAdapter):
            def run(self, handler):
                # print('calling ssl.run %s' % cert_file)
                if self.quiet:
                    class QuietHandler(WSGIRequestHandler):
                        def log_request(*args, **kw):
                            pass
                    self.options['handler_class'] = QuietHandler
                srv = make_server(self.host, self.port, handler, **self.options)
                srv.socket = ssl.wrap_socket(
                    srv.socket,
                    certfile=cert_file,
                    server_side=True)
                srv.serve_forever()
        self.pr_dbg('Wrapped socket in ssl with cert %s' % self.cert)
        return SSLWSGIRefServer(host=self.host, port=self.port)

    def run(self):
        route('/')(self.handle_index)
        route('/cmds')(self.handle_cmds)
        post('/cmd')(self.handle_cmd_post)
        if self.ssl:
            run(server=self.ssl_server, debug=DEBUG)
        else:
            run(host=self.host, port=self.port, debug=DEBUG)

    def collect_inbound_cmds(self):
        while True:
            while self.inbound_cmds:
                c = self.inbound_cmds.popleft()
                c_str = json.dumps(c) + '\n'
                self.log_lock.acquire()
                with open(self.log, 'ab') as f:
                    f.write(c_str)
                self.cmds.append(c)
                self.log_lock.release()
            sleep(1)

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
        cmds = []
        self.log_lock.acquire()
        with open(self.log, 'rb') as f:
            lines = f.readlines()
        self.log_lock.release()
        for l in lines:
            c = json.loads(l)
            cmds.append(c)
        return cmds

    def handle_cmd_post(self):
        pdata = load_request(['ts', 'cmd', 'src', 'optout'])
        pdata['server_ts'] = time()
        if pdata['src'] is None:
            pdata['src'] = {}
        pdata['src']['remote_ip'] = request.environ.get('REMOTE_ADDR')
        success, resp_str = self.rec_cmd(pdata)
        resp = {'str': resp_str}
        return json.dumps({'success': success, 'resp': resp}) + '\n'

    def rec_cmd(self, cmd):
        try:
            cmd_str = json.dumps(cmd)
        except TypeError as e:
            return (False, 'rec_cmd json_typeerror(%s)' % (e, cmd))
        if len(cmd_str) > MAX_LEN:
            return (False, 'rec_cmd too long %s' % cmd_str)
        self.inbound_cmds.append(cmd)
        msg = 'rec_cmd: %s' % cmd_str
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

    def cmd(self, cmd, session=None, user=None, ctf_user=None, optout=False):
        opts = {}
        opts['ts'] = time()
        opts['cmd'] = cmd
        opts['optout'] = optout
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
                self.pr_dbg('TypeError %s' % e)
                decoded = j['cmd']
            j['cmd'] = decoded
            cmds.append(j)
        return cmds


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description='Bash Recorder module, stores remote bash history')
    parser.add_argument(
        '--ssl', '-s',
        action='store_true',
        dest='ssl',
        default=False,
        help='use SSL')
    parser.add_argument(
        '--cert', '-c',
        action='store',
        dest='ssl_cert',
        default=CERT_FILE,
        help='path to SSL cert file')
    parser.add_argument(
        '--log', '-l',
        action='store',
        dest='log_file',
        default=LOG_FILE,
        help='path to log file')
    parser.add_argument(
        '--port', '-p',
        action='store',
        dest='listen_port',
        default=PORT,
        help='port to bind listen')
    results = parser.parse_args()
    args = {}
    args['ssl'] = results.ssl
    args['cert'] = results.ssl_cert
    args['log'] = results.log_file
    args['addr'] = (LHOST, results.listen_port)
    return args


def main(argv):
    args = parse_args(argv)
    backend = Server(
        addr=args['addr'],
        log=args['log'],
        ssl=args['ssl'],
        cert=args['cert'])
    backend.run()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
