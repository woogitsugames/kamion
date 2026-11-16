import json, pickle, sys
sys.path.insert(0, "tools/worldgen")
import numpy as np, shapely
from roads import pipeline, tunnels as TN
from terrain_mesh import conform as CF
d = pickle.load(open("artifacts/tunnel-0211/dev_dump.pkl", "rb"))
w = d["w"]; g = json.loads((pipeline.REGIONS / "bialystok-kleeberga" / "roads.graph.json").read_text(encoding="utf-8"))
G = TN.plan(w, g)[0]; F = G["F"]
grid = TN.Grid(w.hf, d["zc"])
for p in w.buf.parts:
    if p.layer not in ("road", "bridge", "paved") or p.src.startswith(("c:w23982181", "c:w249740778")) or not len(p.T):
        continue
    cen = p.V[p.T].mean(1)
    ins = shapely.contains_xy(F, cen[:, 0], cen[:, 1])
    if not ins.any(): continue
    q = cen[ins]
    zr = np.array([TN._floor_field([G], grid, np.ones((1,1),bool))[0,0] if False else 0 for _ in [0]])
    zrr = TN._floor_field([G], grid, TN._poly_mask(F.buffer(1), grid))
    jj = np.rint(grid.y1 - q[:, 1]).astype(int); ii = np.rint(q[:, 0] - grid.x0).astype(int)
    h = q[:, 2] - (zrr[jj, ii] + TN.FLOOR_DROP_M)
    print(f"{p.layer:7s} {p.mat:18s} {p.src[:60]:60s} n={ins.sum():5d} h min {h.min():5.2f} med {np.median(h):5.2f} max {h.max():5.2f}")
