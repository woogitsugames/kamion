import json, os, math, sys
B = sys.argv[1]
info = json.load(open(os.path.join(B, 'info.json')))
geo = json.load(open(os.path.join(B, 'geo.json')))
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
    dx = (b[1] - a[1]) * 111320 * math.cos(la); dy = (b[0] - a[0]) * 110574
    return math.hypot(dx, dy), (math.degrees(math.atan2(dx, dy)) + 360) % 360


out = []
for t, p in info.items():
    ii = (p.get('imageinfo') or [{}])[0]
    fn = os.path.join(B, 'img', ii.get('sha1', 'x') + '.jpg')
    have = os.path.exists(fn)
    ps = pos.get(t)
    near = ''
    if ps:
        d = sorted((dist(ps, c)[0], k, dist(ps, c)[1]) for k, c in R.items())[0]
        near = '%s %dm brg%d' % (d[1], d[0], d[2])
    out.append((t, ii.get('sha1'), have, ps, near))
    print('Y' if have else '-', (ii.get('sha1') or '')[:10], t[5:75], ps, near)
json.dump(out, open(os.path.join(B, 'list.json'), 'w'), indent=0)
