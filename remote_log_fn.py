
def remote_log(msg, user=None):
    data = {}
    data['cmd'] = msg
    data['src'] = {}
    data['src']['ctf_user'] = user
    url = 'https://ctf.local:9999/cmd'
    try:
        requests.post(url, data=json.dumps(data), timeout=2.0)
    except:  # ConnectionError, HTTPError, Timeout, TooManyRedirects
        pass