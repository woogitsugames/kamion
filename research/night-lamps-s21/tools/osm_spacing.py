"""Rozstaw latarni z OSM: latarnia (highway=street_lamp) -> najbliższa nazwana droga (<= MAXD m od osi),
rzut na łańcuch ulicy (połączone way o tej samej nazwie), podział na rzędy po stronie osi (lewa/prawa/oś |t|<2 m),
kolejne odstępy wzdłuż s w obrębie rzędu; odstępy > GAPMAX odrzucone (brak mapowania). Wynik CSV + podsumowanie."""
import sys, json, math, csv, statistics, collections

src, out_csv, out_sum = sys.argv[1:4]
MAXD = 25.0
GAPMAX = 80.0
d = json.load(open(src))
lat0 = 53.13
KX = 111320.0 * math.cos(math.radians(lat0)); KZ = 110574.0
P = lambda la, lo: ((lo - 23.15) * KX, (la - lat0) * KZ)
lamps = [e for e in d['elements'] if e['type'] == 'node']
ways = [e for e in d['elements'] if e['type'] == 'way' and e['tags'].get('name') and all(g for g in e['geometry'])
        and e['tags'].get('highway') not in ('footway', 'cycleway', 'path', 'steps', 'pedestrian', 'track', 'service', 'bridleway', 'construction', 'proposed', 'platform', 'corridor')]
# indeks kafelkowy segmentów
segs = []
for w in ways:
    pts = [P(g['lat'], g['lon']) for g in w['geometry']]
    acc = 0.0
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if L > 0:
            segs.append((w['id'], w['tags']['name'], w['tags'].get('highway'), a, b, L, acc))
        acc += L
grid = collections.defaultdict(list)
for k, s in enumerate(segs):
    for gx in range(int(min(s[3][0], s[4][0]) // 50) - 1, int(max(s[3][0], s[4][0]) // 50) + 2):
        for gz in range(int(min(s[3][1], s[4][1]) // 50) - 1, int(max(s[3][1], s[4][1]) // 50) + 2):
            grid[(gx, gz)].append(k)
assign = []
for l in lamps:
    x, z = P(l['lat'], l['lon'])
    best = None
    for k in grid.get((int(x // 50), int(z // 50)), []):
        wid, name, hw, a, b, L, acc = segs[k]
        ux, uz = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        s = max(0.0, min(L, (x - a[0]) * ux + (z - a[1]) * uz))
        px, pz = a[0] + ux * s, a[1] + uz * s
        dist = math.hypot(x - px, z - pz)
        side = (ux * (z - a[1]) - uz * (x - a[0]))  # >0 lewa
        if best is None or dist < best[0]:
            best = (dist, wid, name, hw, acc + s, math.copysign(dist, side), ux, uz, px, pz)
    if best and best[0] <= MAXD:
        assign.append((l, best))
# łańcuch per nazwa: współrzędna s wzdłuż głównego kierunku (rzut na wektor PCA nazwy), nie per way
by_name = collections.defaultdict(list)
for l, b in assign:
    by_name[b[2]].append((l, b))
rows = []
summary = []
for name, lst in by_name.items():
    xs = [P(l['lat'], l['lon']) for l, _ in lst]
    if len(lst) < 3:
        continue
    # kierunek główny (PCA 2D)
    mx = sum(p[0] for p in xs) / len(xs); mz = sum(p[1] for p in xs) / len(xs)
    sxx = sum((p[0] - mx) ** 2 for p in xs); szz = sum((p[1] - mz) ** 2 for p in xs); sxz = sum((p[0] - mx) * (p[1] - mz) for p in xs)
    th = 0.5 * math.atan2(2 * sxz, sxx - szz)
    ux, uz = math.cos(th), math.sin(th)
    rowsets = collections.defaultdict(list)
    for (l, b), p in zip(lst, xs):
        t = b[5]
        row = 'oś' if abs(t) < 2.0 else ('L' if t > 0 else 'P')
        # orientacja lokalna segmentu vs globalna: strona względem segmentu way (L/P) jest lokalna; wystarcza
        s = b[4]  # długość łuku na way (acc + rzut)
        rowsets[(row, b[1])].append((s, l, b))
    gaps_all = []
    for row, pts in rowsets.items():
        pts.sort(key=lambda q: q[0])
        for (s1, l1, b1), (s2, l2, b2) in zip(pts, pts[1:]):
            g = math.dist(P(l1['lat'], l1['lon']), P(l2['lat'], l2['lon']))
            ok = 5.0 <= g <= GAPMAX
            rows.append([name, row[0], l1['id'], l2['id'], b1[1], round(g, 1), round(abs(b1[5]), 1), round(abs(b2[5]), 1), 'OK' if ok else 'odrzucony',
                         l1['tags'].get('support', ''), l1['tags'].get('lamp_mount', ''), l1['tags'].get('light:colour', ''), l1['tags'].get('light:method', ''), l1['tags'].get('height', '')])
            if ok:
                gaps_all.append(g)
    if gaps_all:
        q = sorted(gaps_all)
        summary.append((name, len(lst), dict(collections.Counter(r[0] for r, v in rowsets.items() for _ in v)), sorted({r[1] for r in rowsets}), len(q), round(q[0], 1), round(statistics.median(q), 1), round(q[-1], 1),
                        round(q[len(q) // 4], 1), round(q[(3 * len(q)) // 4], 1)))
with open(out_csv, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['ulica', 'rząd', 'node_a', 'node_b', 'way_id_a', 'odstęp_m', 'odl_osi_a_m', 'odl_osi_b_m', 'status', 'support', 'lamp_mount', 'light:colour', 'light:method', 'height'])
    w.writerows(rows)
summary.sort(key=lambda r: -r[4])
with open(out_sum, 'w') as f:
    json.dump(summary, f, ensure_ascii=False, indent=0)
for r in summary[:60]:
    print(r)
tagc = collections.Counter()
for l in lamps:
    for k in ('support', 'lamp_mount', 'light:colour', 'light:method', 'height', 'lamp_type', 'light:count'):
        if k in l['tags']:
            tagc[(k, l['tags'][k])] += 1
print('lamps', len(lamps), 'assigned', len(assign))
print(tagc.most_common(40))
