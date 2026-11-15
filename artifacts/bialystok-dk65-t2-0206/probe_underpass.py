"""ADR 0206: vertical probe through the generated world along the DK8 underpass below rondo Szymańskiego.
For points on both carriageway axes, lists every triangle (any material / node, incl. collision) above the XY point."""
import json, sys, struct, numpy as np
from pathlib import Path
sys.path.insert(0, 'tools/worldgen'); sys.path.insert(0, 'tools/worldgen/qa')
import junction_topview as jt
from roads import pipeline
R = 'bialystok-kleeberga'
reg = pipeline.load_region(R); ox, oy = reg['origin']['x'], reg['origin']['y']
jt.colour = lambda name: (0, 0, 0)          # keep every material
def read_all(path):
    b = path.read_bytes(); n = struct.unpack("<I", b[12:16])[0]; j = json.loads(b[20:20 + n])
    for node in j["nodes"]:
        if "mesh" not in node: continue
        if node.get("extras", {}).get("lod", 0) != 0: continue
        nm = node.get("name", "")
        for name, tris in jt.read_glb.__wrapped__(path, node) if hasattr(jt.read_glb, '__wrapped__') else []:
            yield nm, name, tris
world = jt.load_world(R)
g = json.load(open(f'Data/Regions/{R}/roads.graph.json', encoding='utf-8'))
def pts(way):
    e = next(e for e in g['edges'] if e['osm_way'] == way); P = np.array(e['geometry'])
    s = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
    return [(np.interp(q, s, P[:, 0]), np.interp(q, s, P[:, 1])) for q in np.linspace(0, s[-1], 9)]
def inside(t, x, y):
    (x1, y1), (x2, y2), (x3, y3) = t[:, :2]
    d = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
    if abs(d) < 1e-9: return None
    a = ((y2 - y3) * (x - x3) + (x3 - x2) * (y - y3)) / d; b = ((y3 - y1) * (x - x3) + (x1 - x3) * (y - y3)) / d; c = 1 - a - b
    return (a * t[0, 2] + b * t[1, 2] + c * t[2, 2]) if min(a, b, c) >= -1e-6 else None
for way in map(int, sys.argv[1:]):
    print('way', way)
    for X, Y in pts(way):
        x, y = X - ox, Y - oy; hits = []
        for name, tris, lo, hi in world:
            if not (lo[0] <= x <= hi[0] and lo[1] <= y <= hi[1]): continue
            m = (tris[:, :, 0].min(1) <= x) & (tris[:, :, 0].max(1) >= x) & (tris[:, :, 1].min(1) <= y) & (tris[:, :, 1].max(1) >= y)
            for t in tris[m]:
                z = inside(t, x, y)
                if z is not None: hits.append((round(float(z), 2), name))
        hits = sorted(set(hits)); print(f'  {X:.0f},{Y:.0f}', hits[:3], '...', hits[-4:])
# lateral sweep: for each probe point, offsets -5..+5 m across the axis; report anything between road+0.3 and road+4.5 m
print('clearance sweep (obstacles 0.3-4.5 m above the road surface)')
for way in map(int, sys.argv[1:]):
    e = next(e for e in g['edges'] if e['osm_way'] == way); P = np.array(e['geometry'])
    s = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]; bad = 0; n = 0; minclr = 99
    for q in np.linspace(0, s[-1], 31):
        p = np.array([np.interp(q, s, P[:, 0]), np.interp(q, s, P[:, 1])]); t = P[-1] - P[0]; t /= np.hypot(*t); nr = np.array([-t[1], t[0]])
        for off in np.arange(-4.0, 4.01, 1.0):
            x, y = p + off * nr - (ox, oy); zs = []
            for name, tris, lo, hi in world:
                if not (lo[0] <= x <= hi[0] and lo[1] <= y <= hi[1]): continue
                m = (tris[:, :, 0].min(1) <= x) & (tris[:, :, 0].max(1) >= x) & (tris[:, :, 1].min(1) <= y) & (tris[:, :, 1].max(1) >= y)
                for tr in tris[m]:
                    z = inside(tr, x, y)
                    if z is not None: zs.append((z, name))
            road = [z for z, nm in zs if nm == 'collision_asphalt']
            if not road: continue
            r0 = min(road); n += 1
            above = [z - r0 for z, nm in zs if z - r0 > 0.3]
            if above: minclr = min(minclr, min(above))
            ob = [(round(z - r0, 2), nm) for z, nm in zs if 0.3 < z - r0 < 4.5]
            if ob:
                bad += 1; print("   blocked q", round(q), "off", off, ob[:3])
    print(way, 'samples', n, 'blocked', bad, 'min overhead clearance m', round(minclr, 2))
