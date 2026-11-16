import json, pickle, sys
sys.path.insert(0, "tools/worldgen")
import numpy as np
from roads import pipeline, tunnels as TN
R = "bialystok-kleeberga"
g = json.loads((pipeline.REGIONS / R / "roads.graph.json").read_text(encoding="utf-8"))
d = pickle.load(open("artifacts/tunnel-0211/dev_dump.pkl", "rb")); w = d["w"]
TN.build(w, R, d["zc"], d["mask"], [], g, lambda *a: None)
q = np.array([734, -18])
for p in w.buf.parts:
    if not len(p.T): continue
    c = p.V[p.T].mean(1)
    dd = np.hypot(*(c[:, :2] - q).T)
    if dd.min() < 3: print(p.layer, p.mat, p.src[:70], round(float(dd.min()), 2), round(float(c[dd.argmin(), 2]), 2), p.footprint)
