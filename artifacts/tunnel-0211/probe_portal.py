import json, pickle, sys
sys.path.insert(0, "tools/worldgen"); sys.path.insert(0, "tools/worldgen/qa")
import numpy as np, shapely
import junction_topview as jt
from roads import pipeline, tunnels as TN
R = "bialystok-kleeberga"
jt.colour = lambda n: (0, 0, 0)
W = jt.load_world(R)
d = pickle.load(open("artifacts/tunnel-0211/dev_dump.pkl", "rb")); w = d["w"]
g = json.loads((pipeline.REGIONS / R / "roads.graph.json").read_text(encoding="utf-8"))
G = TN.plan(w, g)[0]; F = G["F"].buffer(4.0).difference(G["F"].buffer(-1.0))
c0 = G["runs"][0]["c"]
out = {}
for nm, tr, lo, hi in W:
    c = tr.mean(1)
    m = shapely.contains_xy(F, c[:, 0], c[:, 1])
    if not m.any(): continue
    for t in c[m]:
        zr = float(c0.zc(c0.line.project(t[:2])[0]))
        h = t[2] - zr
        if 0.3 < h < 4.6:
            k = nm; out.setdefault(k, []).append((round(t[0], 1), round(t[1], 1), round(h, 2)))
for k, v in sorted(out.items(), key=lambda x: -len(x[1])):
    print(k, len(v), v[:4])

