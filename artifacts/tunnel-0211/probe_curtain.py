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
band = F.buffer(6).difference(F.buffer(-6))
out = {}
for nm, tr, lo, hi in W:
    c = tr.mean(1)
    dz = tr[:, :, 2].max(1) - tr[:, :, 2].min(1)
    m = shapely.contains_xy(band, c[:, 0], c[:, 1]) & (dz > 2.0)
    if m.any():
        out[nm] = (int(m.sum()), np.round(c[m][:3], 1).tolist())
for k, v in sorted(out.items(), key=lambda x: -x[1][0]): print(k, v)
