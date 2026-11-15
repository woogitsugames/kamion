import json, sys, math
R = {'skorupska17': (53.133953, 23.180958), 'dobra3': (53.138052, 23.180663), 'zwierzyniecka4': (53.119647, 23.149357),
     'hallera19': (53.153529, 23.125354), 'kopernika5a': (53.121630, 23.143090), 'wiezowiec_m57': (53.153231, 23.168022)}


def dist(a, b):
    la = math.radians((a[0] + b[0]) / 2)
    dx = (b[1] - a[1]) * 111320 * math.cos(la)
    dy = (b[0] - a[0]) * 110574
    return math.hypot(dx, dy), (math.degrees(math.atan2(dx, dy)) + 360) % 360


P = []
for fn in sys.argv[1:]:
    P += json.load(open(fn))
print('photos', len(P))
lats = [float(p['lat']) for p in P]; lngs = [float(p['lng']) for p in P]
print('bbox', min(lats), max(lats), min(lngs), max(lngs), P[0]['shotDate'], P[-1]['shotDate'])
for k, c in R.items():
    best = []
    for p in P:
        d, b = dist((float(p['lat']), float(p['lng'])), c)
        h = float(p['heading'] or 0)
        diff = ((b - h + 540) % 360) - 180
        best.append((round(d), round(diff), p['id'], p['shotDate'][:16], round(h)))
    best.sort()
    print(k, best[:5])
    fwd = [x for x in best if abs(x[1]) < 30 and x[0] < 700]
    print('  forward<30deg<700m:', len(fwd), fwd[:8])
