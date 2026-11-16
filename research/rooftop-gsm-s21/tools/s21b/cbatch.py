"""Commons: geosearch wokół dachów + imageinfo partiami (50 tytułów / wywołanie), potem miniatury 1280 px z thumburl API.
Pauzy 5 s między wywołaniami, po 429 backoff 120/240/480 s. UA generyczny, tylko domeny Wikimedia.
Użycie: python3 -I cbatch.py outdir [extra_titles.json]"""
import json, sys, os, time, urllib.request, urllib.parse, urllib.error, hashlib, datetime
UA = {'User-Agent': 'research-client/1.0 (generic)'}
OD = sys.argv[1]
os.makedirs(os.path.join(OD, 'img'), exist_ok=True)
LOG = os.path.join(OD, 'log.json')
log = json.load(open(LOG)) if os.path.exists(LOG) else []
R = {'skorupska17': (53.133953, 23.180958), 'dobra3': (53.138052, 23.180663), 'zwierzyniecka4': (53.119647, 23.149357),
     'hallera19': (53.153529, 23.125354), 'kopernika5a': (53.121630, 23.143090), 'wiezowiec_m57': (53.153231, 23.168022)}


def now():
    return datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')


def get(url, binary=False):
    for i, back in enumerate((120, 240, 480, 600)):
        try:
            b = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read()
            log.append({'ts': now(), 'url': url[:200], 'status': 200})
            time.sleep(5)
            return b if binary else json.loads(b)
        except urllib.error.HTTPError as e:
            log.append({'ts': now(), 'url': url[:200], 'status': e.code})
            print('HTTP', e.code, url[:100], flush=True)
            json.dump(log, open(LOG, 'w'), indent=0)
            if e.code != 429:
                return None
            time.sleep(back)
    return None


API = 'https://commons.wikimedia.org/w/api.php?'
GEO = os.path.join(OD, 'geo.json')
geo = json.load(open(GEO)) if os.path.exists(GEO) else {}
for k, (la, lo) in R.items():
    if k in geo:
        continue
    j = get(API + urllib.parse.urlencode(dict(action='query', list='geosearch', gscoord=f'{la}|{lo}', gsradius=600, gsnamespace=6, gslimit=60, format='json')))
    if j is None or 'query' not in j:
        print('geo fail', k, str(j)[:300], flush=True); continue
    geo[k] = j['query']['geosearch']
    print(k, len(geo[k]), flush=True)
    json.dump(geo, open(GEO, 'w'), indent=0)
NMAX = int(os.environ.get('NMAX', '20'))
titles = sorted({r['title'] for v in geo.values() for r in v[:NMAX]})
if len(sys.argv) > 2:
    titles = sorted(set(titles) | set(json.load(open(sys.argv[2]))))
INFO = os.path.join(OD, 'info.json')
info = json.load(open(INFO)) if os.path.exists(INFO) else {}
todo = [t for t in titles if t not in info]
for i in range(0, len(todo), 50):
    ch = todo[i:i + 50]
    j = get(API + urllib.parse.urlencode(dict(action='query', titles='|'.join(ch), prop='imageinfo|coordinates', iiprop='url|extmetadata|user|size|sha1',
                                              iiurlwidth=960, coprop='type|name|dim', coprimary='all', format='json')))
    if j is None or 'query' not in j:
        print('info fail', str(j)[:300], flush=True); continue
    for p in j['query']['pages'].values():
        info[p['title']] = p
    json.dump(info, open(INFO, 'w'), indent=0)
    print('info', len(info), flush=True)
json.dump(log, open(LOG, 'w'), indent=0)
print('titles', len(titles), 'info', len(info))

IMG = os.path.join(OD, 'img')
for t in titles:
    p = info.get(t)
    if not p or 'imageinfo' not in p:
        continue
    ii = p['imageinfo'][0]
    fn = os.path.join(IMG, ii['sha1'] + '.jpg')
    if os.path.exists(fn) or not ii.get('thumburl'):
        continue
    b = get(ii['thumburl'], binary=True)
    if b:
        open(fn, 'wb').write(b)
        print('img', t[:70], flush=True)
json.dump(log, open(LOG, 'w'), indent=0)
