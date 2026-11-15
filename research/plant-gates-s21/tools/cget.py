import sys, time, json, urllib.request, urllib.error, urllib.parse
UA = 'research-client/1.0 (generic)'
API = 'https://commons.wikimedia.org/w/api.php'


def get(url, tries=12, binary=False, params=None):
    if params:
        url = url + '?' + urllib.parse.urlencode(params)
    else:
        url = urllib.parse.quote(url, safe=':/?&=%,.-_~+|()#;@!$*\'')
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                d = r.read()
                return d if binary else d.decode('utf-8')
        except urllib.error.HTTPError as e:
            if e.code in (429, 503, 502, 504):
                ra = int(e.headers.get('retry-after', '20') or 20)
                w = min(max(ra, 8), 90) * (1 + i * 0.25)
                print(f'[{e.code}] wait {w:.0f}s', file=sys.stderr)
                time.sleep(w)
                continue
            raise
        except Exception as e:
            print('[err]', e, file=sys.stderr)
            time.sleep(10 * (i + 1))
    raise SystemExit('failed ' + url)


def api(**p):
    p.setdefault('format', 'json')
    return json.loads(get(API, params=p))


def catmembers(cat, ns=None):
    out = []
    cont = {}
    while True:
        p = dict(action='query', list='categorymembers', cmtitle='Category:' + cat, cmlimit=500, **cont)
        if ns is not None:
            p['cmnamespace'] = ns
        d = api(**p)
        out += d['query']['categorymembers']
        if 'continue' in d:
            cont = {'cmcontinue': d['continue']['cmcontinue']}
        else:
            return out


def geosearch(lat, lon, radius=1000, limit=500):
    d = api(action='query', list='geosearch', gscoord=f'{lat}|{lon}', gsradius=radius, gslimit=limit, gsnamespace=6)
    return d['query']['geosearch']


def imageinfo(titles):
    res = {}
    for i in range(0, len(titles), 40):
        d = api(action='query', prop='imageinfo|coordinates', titles='|'.join(titles[i:i + 40]),
                iiprop='extmetadata|url|sha1|size|timestamp', iiurlwidth=1600, coprop='type|dim|heading', coprimary='all')
        for pg in d['query']['pages'].values():
            res[pg['title']] = pg
    return res


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'url':
        out = sys.argv[3] if len(sys.argv) > 3 else None
        d = get(sys.argv[2], binary=bool(out))
        if out:
            open(out, 'wb').write(d)
            print('saved', out, len(d))
        else:
            print(d)
    elif cmd == 'cat':
        for m in catmembers(sys.argv[2]):
            print(m['ns'], m['title'])
    elif cmd == 'geo':
        for m in geosearch(sys.argv[2], sys.argv[3], int(sys.argv[4])):
            print(m['dist'], m['lat'], m['lon'], m['title'])
    elif cmd == 'info':
        titles = [l.strip() for l in open(sys.argv[2]) if l.strip()]
        json.dump(imageinfo(titles), open(sys.argv[3], 'w'), ensure_ascii=False, indent=1)
        print('ok', len(titles))
