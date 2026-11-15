"""Najbliższa nazwana droga (way) do punktów: argv[1]=osm json, argv[2..]=key:lat:lon."""
import sys, json, math
d = json.load(open(sys.argv[1]))
K = 111320 * math.cos(math.radians(53.13)), 110574
ways = [e for e in d['elements'] if e['type'] == 'way' and e['tags'].get('name') and all(e['geometry'])
        and e['tags'].get('highway') not in ('footway', 'cycleway', 'path', 'steps', 'track', 'service', 'construction', 'proposed', 'platform')]
for a in sys.argv[2:]:
    key, la, lo = a.split(':')
    la, lo = float(la), float(lo)
    p = (lo * K[0], la * K[1])
    best = (1e9, None, None)
    for w in ways:
        g = [(x['lon'] * K[0], x['lat'] * K[1]) for x in w['geometry']]
        for A, B in zip(g, g[1:]):
            L2 = (B[0] - A[0]) ** 2 + (B[1] - A[1]) ** 2
            t = 0 if L2 == 0 else max(0, min(1, ((p[0] - A[0]) * (B[0] - A[0]) + (p[1] - A[1]) * (B[1] - A[1])) / L2))
            dd = math.dist(p, (A[0] + t * (B[0] - A[0]), A[1] + t * (B[1] - A[1])))
            if dd < best[0]:
                best = (dd, w['id'], w['tags']['name'])
    print(key, round(best[0], 1), best[1], best[2])
