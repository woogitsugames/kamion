"""ADR 0206: passability sweep of the D64 control route through the tile (no phone run): every 2 m along the route
polyline (variant A, dk65_route_plan.json, cut to the tile), lateral offsets -3..+3 m, find the road collision surface
and list any triangle of ANY material (finest LOD, incl. bridge/furniture/terrain) and of terrain_lod2 (= terrain
collision) between 0.3 and 4.5 m above it. Also checks that a road collision surface exists (no holes) and the
largest step of the collision surface between consecutive stations."""
import json, sys, struct, numpy as np
sys.path.insert(0, 'tools/worldgen'); sys.path.insert(0, 'tools/worldgen/qa')
import junction_topview as jt
from roads import pipeline
R = 'bialystok-kleeberga'
reg = pipeline.load_region(R); ox, oy = reg['origin']['x'], reg['origin']['y']; bb = reg['bbox']
jt.colour = lambda n: (0, 0, 0)
W = jt.load_world(R)
sys.argv = sys.argv[:1]
exec(open('artifacts/tunnel-0211/probe_lod2.py', encoding='utf-8').read().split("g = json.load")[0])  # T: terrain_lod2 + road_collision
plan = json.load(open('docs/reports/map/dk65_route_plan.json', encoding='utf-8'))['variants']['A_old_road']['polyline']
P = np.array(plan, float)
inb = (P[:, 0] >= bb['xmin'] - 50) & (P[:, 0] <= bb['xmax'] + 50) & (P[:, 1] >= bb['ymin']) & (P[:, 1] <= bb['ymax'])
P = P[inb]
s = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
def tri_z(tris, x, y):
    m = (tris[:, :, 0].min(1) <= x) & (tris[:, :, 0].max(1) >= x) & (tris[:, :, 1].min(1) <= y) & (tris[:, :, 1].max(1) >= y)
    out = []
    for t in tris[m]:
        (x1, y1), (x2, y2), (x3, y3) = t[:, :2]; d = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
        if abs(d) < 1e-9: continue
        a = ((y2 - y3) * (x - x3) + (x3 - x2) * (y - y3)) / d; b = ((y3 - y1) * (x - x3) + (x1 - x3) * (y - y3)) / d; c = 1 - a - b
        if min(a, b, c) >= -1e-6: out.append(a * t[0, 2] + b * t[1, 2] + c * t[2, 2])
    return out
blocked, holes, prev, maxstep, n = [], 0, None, 0.0, 0
for q in np.arange(0, s[-1], 2.0):
    X, Y = np.interp(q, s, P[:, 0]), np.interp(q, s, P[:, 1])
    if not (bb['xmin'] + 1 < X < bb['xmax'] - 1): continue
    i = min(max(1, np.searchsorted(s, q)), len(P) - 1); t = P[i] - P[i - 1]; t /= np.hypot(*t); nr = np.array([-t[1], t[0]])
    for off in (-3.0, -1.5, 0.0, 1.5, 3.0):
        x, y = np.array([X, Y]) + off * nr - (ox, oy); n += 1
        road = [z for nm, tr in T if nm == 'road_collision' for z in tri_z(tr, x, y)]
        if not road: holes += 1; continue
        r0 = min(road, key=lambda z: abs(z - (prev if prev is not None else z)))
        if off == 0.0:
            if prev is not None: maxstep = max(maxstep, abs(r0 - prev))
            prev = r0
        hit = [(round(z - r0, 2), 'terrain_lod2') for nm, tr in T if nm == 'terrain_lod2' for z in tri_z(tr, x, y) if 0.3 < z - r0 < 4.5]
        for nm, tr, lo, hi in W:
            if lo[0] <= x <= hi[0] and lo[1] <= y <= hi[1]:
                hit += [(round(z - r0, 2), nm) for z in tri_z(tr, x, y) if 0.3 < z - r0 < 4.5]
        if hit: blocked.append((round(q), off, X.round(1), Y.round(1), sorted(hit)[:3]))
print(f'route {s[-1]:.0f} m in tile, samples {n}, no road collision {holes}, blocked {len(blocked)}, max axis step {maxstep:.2f} m')
for b in blocked[:40]: print(' ', b)

