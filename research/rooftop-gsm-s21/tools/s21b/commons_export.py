"""Kopiuje miniatury Commons s21b do files/ (JPG q82, ≤ 960 px) i zapisuje metadane do out/commons_s21b_meta.json.
Użycie: python3 -I commons_export.py <cb_dir> <research_dir>"""
import json, os, sys, math, hashlib
from PIL import Image
CB, RD = sys.argv[1], sys.argv[2]
info = json.load(open(os.path.join(CB, 'info.json')))
geo = json.load(open(os.path.join(CB, 'geo.json')))
OP = json.load(open(os.path.join(RD, 'commons_s21b_opisy.json')))
R = {'skorupska17': (53.133953, 23.180958), 'dobra3': (53.138052, 23.180663), 'zwierzyniecka4': (53.119647, 23.149357),
     'hallera19': (53.153529, 23.125354), 'kopernika5a': (53.121630, 23.143090), 'wiezowiec_m57': (53.153231, 23.168022)}
pos = {}
for v in geo.values():
    for r in v:
        pos[r['title']] = (r['lat'], r['lon'])
for t, p in info.items():
    for c in p.get('coordinates', []):
        if c.get('type') == 'camera':
            pos[t] = (c['lat'], c['lon'])


def dist(a, b):
    la = math.radians((a[0] + b[0]) / 2)
    return math.hypot((b[1] - a[1]) * 111320 * math.cos(la), (b[0] - a[0]) * 110574)


out = []
for t, p in sorted(info.items()):
    ii = p['imageinfo'][0]
    k = ii['sha1'][:10]
    if k not in OP:
        continue
    em = ii.get('extmetadata', {})
    src = os.path.join(CB, 'img', ii['sha1'] + '.jpg')
    fn = 'commons_s21b_%s.jpg' % k
    im = Image.open(src).convert('RGB')
    im.thumbnail((960, 960))
    im.save(os.path.join(RD, 'files', fn), quality=82)
    ps = pos.get(t)
    near = min((dist(ps, c), n) for n, c in R.items()) if ps else None
    out.append(dict(title=t, page=ii.get('descriptionurl'), thumb=ii.get('thumburl'), user=ii.get('user'), sha1_oryginalu=ii['sha1'],
                    licencja=em.get('LicenseShortName', {}).get('value'), data=em.get('DateTimeOriginal', {}).get('value', '')[:19],
                    lat=ps[0] if ps else None, lon=ps[1] if ps else None, najblizszy=near[1] if near else None, odl=round(near[0]) if near else None,
                    plik='files/' + fn, sha256=hashlib.sha256(open(os.path.join(RD, 'files', fn), 'rb').read()).hexdigest()))
json.dump(out, open(os.path.join(RD, 'out', 'commons_s21b_meta.json'), 'w'), ensure_ascii=False, indent=1)
print(len(out))
