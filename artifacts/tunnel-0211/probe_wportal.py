import sys, pickle, json
sys.path.insert(0, "tools/worldgen"); sys.path.insert(0, "tools/worldgen/qa")
import numpy as np, shapely
import junction_topview as jt
from roads import pipeline, tunnels as TN
jt.colour = lambda n: (0, 0, 0)
W = jt.load_world("bialystok-kleeberga")
d = pickle.load(open("artifacts/tunnel-0211/dev_dump.pkl", "rb")); w = d["w"]
g = json.loads((pipeline.REGIONS / "bialystok-kleeberga" / "roads.graph.json").read_text(encoding="utf-8"))
G = TN.plan(w, g)[0]; F = G["F"]
print("F", [tuple(np.round(p, 1)) for p in F.exterior.coords])
c0 = G["runs"][0]["c"]
q = np.array([-160.0, -231.0])
for nm, tr, lo, hi in W:
    if nm not in ("terrain_grass",): continue
    c = tr.mean(1)
    m = np.hypot(*(c[:, :2] - q).T) < 12
    if not m.any(): continue
    zr = np.array([c0.zc(c0.line.project(t[:2])[0]) for t in c[m]])
    h = c[m, 2] - zr
    sel = h > 0.5
    print(nm, m.sum(), "high", sel.sum(), np.round(c[m][sel][:12], 1).tolist())
