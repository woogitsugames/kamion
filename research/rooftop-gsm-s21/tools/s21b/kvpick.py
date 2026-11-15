import json, sys, math, glob, os, urllib.request, time
from PIL import Image
UA = {'User-Agent': 'research-client/1.0 (generic)'}
R = {'skorupska17': (53.133953, 23.180958), 'dobra3': (53.138052, 23.180663), 'zwierzyniecka4': (53.119647, 23.149357),
     'hallera19': (53.153529, 23.125354), 'kopernika5a': (53.121630, 23.143090), 'wiezowiec_m57': (53.153231, 23.168022)}


def dist(a, b):
    la = math.radians((a[0] + b[0]) / 2)
    dx = (b[1] - a[1]) * 111320 * math.cos(la)
    dy = (b[0] - a[0]) * 110574
    return math.hypot(dx, dy), (math.degrees(math.atan2(dx, dy)) + 360) % 360


P = {}
for fn in glob.glob('kvs_*.json') + ['kvseq_10733.json']:
    for p in json.load(open(fn)):
        p['seq'] = fn
        P[p['id']] = p
roof = sys.argv[1]; maxd = float(sys.argv[2]); maxdiff = float(sys.argv[3]); step = int(sys.argv[4]); dl = len(sys.argv) > 5
c = R[roof]
c_ = []
for p in P.values():
    d, b = dist((float(p['lat']), float(p['lng'])), c)
    diff = ((b - float(p['heading'] or 0) + 540) % 360) - 180
    if d < maxd and abs(diff) < maxdiff:
        c_.append((p['shotDate'][:10], d, diff, p))
c_.sort(key=lambda x: (x[0], x[1]))
sel = c_[::step]
for date, d, diff, p in sel:
    print(roof, p['id'], date, round(d), round(diff), p['heading'], p['lat'], p['lng'], p['seq'])
    if dl:
        fn = f'dl/kv_{p["id"]}.jpg'
        if not os.path.exists(fn):
            try:
                open(fn, 'wb').write(urllib.request.urlopen(urllib.request.Request(p['fileurlProc'], headers=UA), timeout=90).read())
                im = Image.open(fn); im.thumbnail((960, 960)); im.save(f'dl/kv_{p["id"]}_960.jpg')
            except Exception as e:
                print('  ERR', e)
            time.sleep(1)
print(len(c_))
