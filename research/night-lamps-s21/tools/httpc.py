"""Wspólny klient HTTP (UA generyczny, retry z backoffem)."""
import time, urllib.request, urllib.parse, json, sys

UA = 'research-client/1.0 (generic)'


def get(url, data=None, timeout=150, tries=5, headers=None):
    h = {'User-Agent': UA}
    if headers:
        h.update(headers)
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers=h)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:  # noqa
            last = e
            sys.stderr.write('retry %d %s: %s\n' % (i, url[:120], e))
            time.sleep(5 * (i + 1) ** 2 if '429' not in str(e) else 30 * (i + 1))
    raise last


def getjson(url, **kw):
    return json.loads(get(url, **kw))


def overpass(q, out):
    for ep in ['https://overpass-api.de/api/interpreter',
               'https://overpass.private.coffee/api/interpreter',
               'https://overpass.kumi.systems/api/interpreter']:
        try:
            b = get(ep, data=urllib.parse.urlencode({'data': q}).encode(), tries=3, timeout=200)
            json.loads(b)
            open(out, 'wb').write(b)
            return ep
        except Exception as e:  # noqa
            sys.stderr.write('endpoint fail %s %s\n' % (ep, e))
    raise RuntimeError('overpass failed')


if __name__ == '__main__':
    q = open(sys.argv[1]).read()
    ep = overpass(q, sys.argv[2])
    d = json.load(open(sys.argv[2]))
    print(ep, len(d['elements']), d.get('osm3s', {}).get('timestamp_osm_base'))
