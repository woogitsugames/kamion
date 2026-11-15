"""Download Panoramax items (hd asset) by id from search json. Usage: pmx_dl.py search.json outdir viewdir id_prefix...
Writes outdir/pmx_summary.json (merged)."""
import json, sys, os, subprocess, hashlib, time
from PIL import Image
d = json.load(open(sys.argv[1]))
out, view = sys.argv[2], sys.argv[3]
os.makedirs(out, exist_ok=True); os.makedirs(view, exist_ok=True)
sp = os.path.join(out, 'pmx_summary.json')
summ = json.load(open(sp)) if os.path.exists(sp) else {}
want = sys.argv[4:]
for x in d['features']:
    if not any(x['id'].startswith(w) for w in want):
        continue
    a = x['assets']
    url = (a.get('hd') or a.get('sd'))['href']
    f = os.path.join(out, 'pmx_' + x['id'][:8] + '.jpg')
    if not os.path.exists(f):
        r = subprocess.run(['curl', '-sSL', '-m', '180', '-o', f, '-w', '%{http_code}', url], capture_output=True, text=True)
        print(x["id"][:8], r.stdout)
        if r.stdout != "200":
            time.sleep(5); r = subprocess.run(["curl", "-sSL", "-m", "180", "-o", f, url]); time.sleep(1)
    im = Image.open(f); im.load()
    w = 960
    im.convert('RGB').resize((w, round(im.size[1] * w / im.size[0]))).save(os.path.join(view, 'pmx_' + x['id'][:8] + '.jpg'), quality=85)
    p = x['properties']
    lo, la = x['geometry']['coordinates']
    self_link = [l['href'] for l in x.get('links', []) if l.get('rel') == 'self']
    summ[x['id']] = dict(file=f, size=im.size, url=url, item=self_link[0] if self_link else None, collection=x.get('collection'),
                         lat=la, lon=lo, azimuth=p.get('view:azimuth'), datetime=p.get('datetime'), license=p.get('license'),
                         providers=[pr.get('name') for pr in p.get('providers', [])] or p.get('geovisio:producer'),
                         sha256=hashlib.sha256(open(f, 'rb').read()).hexdigest())
    print(x['id'][:8], im.size, p.get('license'), summ[x['id']]['providers'], p.get('view:azimuth'))
json.dump(summ, open(sp, 'w'), ensure_ascii=False, indent=1)
