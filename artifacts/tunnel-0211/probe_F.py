import json, pickle, sys
sys.path.insert(0, "tools/worldgen")
import numpy as np, shapely
from roads import pipeline, tunnels as TN
d = pickle.load(open("artifacts/tunnel-0211/dev_dump.pkl", "rb"))
w = d["w"]; g = json.loads((pipeline.REGIONS / "bialystok-kleeberga" / "roads.graph.json").read_text(encoding="utf-8"))
G = TN.plan(w, g)[0]; F = G["F"]
grid = TN.Grid(w.hf, d["zc"])
m = TN._poly_mask(F, grid)
jj, ii = np.where(m)
r = G["runs"][0]["c"]
zr = np.array([r.zc(r.line.project((grid.x0+i, grid.y1-j))[0]) for j, i in zip(jj, ii)])
nmt = w.hf.z[jj, ii] - zr; zc = d["zc"][jj, ii] - zr; dk = np.where(d["deck_mask"][jj, ii], d["deck"][jj, ii] - zr, np.nan)
print("F nodes", len(jj), "NMT-road pct", np.percentile(nmt, [1, 5, 25, 50, 75, 95]).round(2))
print("zc0-road pct", np.percentile(zc, [1, 5, 25, 50, 75, 95]).round(2))
print("deck nodes", np.isfinite(dk).sum(), np.nanpercentile(dk, [1, 50, 99]).round(2))
# map of NMT-road in F as text, 3 m step
x0, y0, x1, y1 = F.bounds
for y in np.arange(y1, y0, -3):
    row = ""
    for x in np.arange(x0, x1, 2):
        if not F.contains(shapely.Point(x, y)): row += " "; continue
        i, j = int(round(x - grid.x0)), int(round(grid.y1 - y))
        v = w.hf.z[j, i] - r.zc(r.line.project((x, y))[0])
        row += "#" if d["deck_mask"][j, i] else ("." if v < 1 else ("o" if v < 4.5 else "+"))
    print(row)
