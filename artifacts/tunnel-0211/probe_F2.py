import json, pickle, sys
sys.path.insert(0, "tools/worldgen")
import numpy as np, shapely
from roads import pipeline, tunnels as TN
from terrain_mesh import conform as CF
d = pickle.load(open("artifacts/tunnel-0211/dev_dump.pkl", "rb"))
w = d["w"]; g = json.loads((pipeline.REGIONS / "bialystok-kleeberga" / "roads.graph.json").read_text(encoding="utf-8"))
G = TN.plan(w, g)[0]; F = G["F"]
runs = {r["c"].id for r in G["runs"]}
r = G["runs"][0]["c"]
oz, om = CF.rasterise([p for p in w.buf.parts if p.layer == "road" and p.footprint and p.src not in runs], w.hf)
grid = TN.Grid(w.hf, d["zc"])
x0, y0, x1, y1 = F.buffer(8).bounds
for y in np.arange(y1, y0, -3):
    row = ""
    for x in np.arange(x0, x1, 2):
        i, j = int(round(x - grid.x0)), int(round(grid.y1 - y))
        zr = r.zc(r.line.project((x, y))[0])
        ins = F.contains(shapely.Point(x, y))
        if d["deck_mask"][j, i]: ch = "#"
        elif om[j, i]: v = oz[j, i] - zr; ch = "R" if v > 3 else ("r" if v > 0.5 else "_")
        else: v = d["zc"][j, i] - zr; ch = "+" if v > 3 else ("o" if v > 0.5 else ".")
        row += ch if ins else ch.lower() if ch not in "+o._#" else {"+": "^", "o": ",", ".": " ", "_": " ", "#": "="}[ch]
    print(row)
srcs = sorted({p.src for p in w.buf.parts if p.layer in ("road", "bridge") and p.src not in runs and len(p.V) and shapely.intersects(F, shapely.MultiPoint(p.V[:, :2]))})
print(srcs[:40])
