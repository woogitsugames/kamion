"""Pobiera miniatury 1600 px z upload.wikimedia.org (domena Wikimedia) dla wpisów z ov.json; pauzy 4 s, backoff 60 s przy 429.
Użycie: python3 -I dlthumb.py ov.json outdir [filtr_podciągu ...]"""
import json, sys, os, time, urllib.request, hashlib
UA = {'User-Agent': 'research-client/1.0 (generic)'}
d = json.load(open(sys.argv[1]))
od = sys.argv[2]
flt = sys.argv[3:]
log = []
for k, v in d.items():
    if flt and not any(f in v['title'] for f in flt):
        continue
    u = v['url']
    a, b, name = u.split('/')[-3:]
    thumb = f'https://upload.wikimedia.org/wikipedia/commons/thumb/{a}/{b}/{name}/1280px-{name}'
    fn = os.path.join(od, k[:8] + '.jpg')
    if os.path.exists(fn):
        continue
    for i in range(4):
        try:
            data = urllib.request.urlopen(urllib.request.Request(thumb, headers=UA), timeout=90).read()
            open(fn, 'wb').write(data)
            log.append((k, 'ok', thumb, hashlib.sha256(data).hexdigest()))
            print('ok', k[:8], v['title'][:60], flush=True)
            break
        except Exception as e:
            print('err', k[:8], e, flush=True)
            log.append((k, str(e), thumb, ''))
            time.sleep(60 if "429" in str(e) else 8)
            if "400" in str(e): break
    time.sleep(4)
json.dump(log, open(os.path.join(od, 'log_%d.json' % int(time.time())), 'w'), indent=1)
