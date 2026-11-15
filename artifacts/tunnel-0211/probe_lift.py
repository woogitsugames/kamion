import json, pickle, sys
sys.path.insert(0, "tools/worldgen")
import numpy as np, shapely
from roads import pipeline, tunnels as TN
R = "bialystok-kleeberga"
g = json.loads((pipeline.REGIONS / R / "roads.graph.json").read_text(encoding="utf-8"))
d = pickle.load(open("artifacts/tunnel-0211/dev_dump.pkl", "rb")); w = d["w"]
G = TN.plan(w, g)[0]; F = G["F"].buffer(0.3)
run_ids = tuple(r["c"].id for r in G["runs"])
c0 = G["runs"][0]["c"]
for p in w.buf.parts:
    if p.layer not in ("paved", "plot_ground", "collision", "road") or p.src.startswith(run_ids) or not len(p.V): continue
    m = shapely.contains_xy(F, p.V[:, 0], p.V[:, 1])
    if not m.any(): continue
    zr = np.array([c0.zc(c0.line.project(v[:2])[0]) for v in p.V[m]])
    low = (p.V[m, 2] - zr) < 4.5
    if low.any(): print(p.layer, p.mat, p.src[:60], "in", int(m.sum()), "low", int(low.sum()), "of", len(p.V))
