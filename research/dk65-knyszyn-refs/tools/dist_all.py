"""Merge commons.json + commons_route.json; compute distance to route & to S19 viaduct; write candidates.json"""
import json, math, sys
from pyproj import Transformer
R = '/workspace/kamion/.claude/worktrees/agent-ab851075007c7ffbb/'
pl = json.load(open(R + 'docs/reports/map/dk65_route_plan.json'))['variants']['A_old_road']['polyline']
fw = Transformer.from_crs('EPSG:4326', 'EPSG:2180', always_xy=True)
cum = [0]
for i in range(1, len(pl)): cum.append(cum[-1] + math.dist(pl[i - 1], pl[i]))
A = json.load(open(sys.argv[1]))['files']; B = json.load(open(sys.argv[2]))['files']
A.update(B)
out = {}
for t, f in A.items():
    co = f.get('coords') or []
    if not co: continue
    c = co[0]; X, Y = fw.transform(c['lon'], c['lat'])
    best = (1e9, 0)
    for k in range(1, len(pl)):
        ax, ay = pl[k - 1]; bx, by = pl[k]; dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy
        tt = max(0, min(1, ((X - ax) * dx + (Y - ay) * dy) / L2)) if L2 else 0
        d = math.dist((X, Y), (ax + tt * dx, ay + tt * dy))
        if d < best[0]: best = (d, (cum[k - 1] + tt * math.sqrt(L2)) / 1000)
    f.update({'x': round(X, 1), 'y': round(Y, 1), 'dist_route_m': round(best[0], 1), 'km': round(best[1], 3), 'lat': c['lat'], 'lon': c['lon'], 'cotype': c.get('type'), 'heading': c.get('dim')})
    out[t] = f
json.dump(out, open(sys.argv[3], 'w'), ensure_ascii=False, indent=1)
for t, f in sorted(out.items(), key=lambda kv: kv[1]['km']):
    if f['dist_route_m'] <= float(sys.argv[4]) and 'bocian' not in t.lower() and 'ciconia' not in t.lower() and (f.get('mime') or '').startswith('image/jp') and f['km'] > 8.3:
        print(f"{f['km']:6.2f} {f['dist_route_m']:6.1f} {f['license']:14s} {(f['date'] or '')[:10]:10s} {t[5:90]}")
