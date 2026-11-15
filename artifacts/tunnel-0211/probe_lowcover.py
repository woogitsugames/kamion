import json, pickle, sys
sys.path.insert(0, "tools/worldgen")
import numpy as np, shapely
from roads import pipeline, tunnels as TN
R = "bialystok-kleeberga"
g = json.loads((pipeline.REGIONS / R / "roads.graph.json").read_text(encoding="utf-8"))
d = pickle.load(open("artifacts/tunnel-0211/dev_dump.pkl", "rb")); w = d["w"]
G0 = TN.plan(w, g)[0]
TN.build(w, R, d["zc"], d["mask"], [], g, lambda *a: None)
F = G0["F"]
runs = G0["runs"]
def zr(q):
    return max(float(np.max(r["c"].crossfall_z(np.array([s, s]), np.array([-r["c"].hw_at(s), r["c"].hw_at(s)])))) for r in runs for s in [min(max(r["c"].line.project(q)[0], r["sa"]-20), r["sb"]+20)])
for p in w.buf.parts:
    if not p.src.startswith("tunnel") or p.layer == "bridge" and "wall" in p.src: continue
    m = shapely.contains_xy(F.buffer(-0.2), p.V[:, 0], p.V[:, 1])
    if not m.any(): continue
    idx = np.where(m)[0]
    h = np.array([p.V[k, 2] - zr(p.V[k, :2]) for k in idx])
    bad = h < 4.75
    if bad.any(): print(p.src, p.mat, int(bad.sum()), np.round(p.V[idx[bad]][:5], 1).tolist(), np.round(h[bad][:5], 2).tolist())
