"""ADR 0206: does the terrain_lod2 mesh (= Unity terrain COLLISION, RegionImporter) hang over the DK8 underpass road?
Prints, along both carriageway axes, the terrain_lod2 heights above the road collision surface."""
import json, sys, struct, numpy as np
from pathlib import Path
sys.path.insert(0, 'tools/worldgen'); sys.path.insert(0, 'tools/worldgen/qa')
from roads import pipeline
R = 'bialystok-kleeberga'
reg = pipeline.load_region(R); ox, oy = reg['origin']['x'], reg['origin']['y']
wdir = pipeline.REPO / 'Data' / 'raw' / 'derived' / R / 'world'
def nodes(path, want):
    b = path.read_bytes(); n = struct.unpack("<I", b[12:16])[0]; j = json.loads(b[20:20 + n]); bin0 = 20 + n + 8
    ct = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}; nc = {"SCALAR": 1, "VEC3": 3, "VEC2": 2, "VEC4": 4}
    def acc(i):
        a = j["accessors"][i]; bv = j["bufferViews"][a["bufferView"]]; off = bin0 + bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        dt = np.dtype(ct[a["componentType"]]); k = nc[a["type"]]
        return np.frombuffer(b, dt, a["count"] * k, off).reshape(a["count"], k)
    for node in j["nodes"]:
        if node.get("name", "") not in want or "mesh" not in node: continue
        t = np.array(node.get("translation", [0, 0, 0]), float)
        for pr in j["meshes"][node["mesh"]]["primitives"]:
            p = acc(pr["attributes"]["POSITION"]).astype(float) + t; idx = acc(pr["indices"]).reshape(-1, 3)
            yield node["name"], np.stack([-p[:, 0], p[:, 2], p[:, 1]], 1)[idx]
T = []
for f in sorted(wdir.glob('chunk_*.glb')):
    for nm, tr in nodes(f, {'terrain_lod2', 'road_collision'}):
        T.append((nm, tr))
print({nm for nm, _ in T})
def zs(x, y):
    out = []
    for nm, tris in T:
        m = (tris[:, :, 0].min(1) <= x) & (tris[:, :, 0].max(1) >= x) & (tris[:, :, 1].min(1) <= y) & (tris[:, :, 1].max(1) >= y)
        for t in tris[m]:
            (x1, y1), (x2, y2), (x3, y3) = t[:, :2]; d = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
            if abs(d) < 1e-9: continue
            a = ((y2 - y3) * (x - x3) + (x3 - x2) * (y - y3)) / d; b = ((y3 - y1) * (x - x3) + (x1 - x3) * (y - y3)) / d; c = 1 - a - b
            if min(a, b, c) >= -1e-6: out.append((nm, a * t[0, 2] + b * t[1, 2] + c * t[2, 2]))
    return out
g = json.load(open(f'Data/Regions/{R}/roads.graph.json', encoding='utf-8'))
for way in map(int, sys.argv[1:]):
    e = next(e for e in g['edges'] if e['osm_way'] == way); P = np.array(e['geometry']); s = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
    worst = 99
    for q in np.linspace(-40, s[-1] + 40, 61):
        t = (P[-1] - P[0]) / np.hypot(*(P[-1] - P[0])); nr = np.array([-t[1], t[0]])
        base = P[0] + q * t if q < 0 else (P[-1] + (q - s[-1]) * t if q > s[-1] else np.array([np.interp(q, s, P[:, 0]), np.interp(q, s, P[:, 1])]))
        for off in (-3, -1.5, 0, 1.5, 3):
            x, y = base + off * nr - (ox, oy); h = zs(x, y)
            road = [z for nm, z in h if nm == 'road_collision']; ter = [z for nm, z in h if nm == 'terrain_lod2']
            if not road: continue
            r0 = min(road); over = [z - r0 for z in ter if z - r0 > 0.25]
            if over and min(over) < 4.5: worst = min(worst, min(over)); print(f'  {way} q={q:.0f} off={off} terrain_lod2 {min(over):.2f} m above road collision')
    print(way, 'min terrain_lod2 overhead (<4.5 m listed):', worst)
