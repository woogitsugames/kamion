"""ADR 0097: oblique matplotlib views of MultiRoof houses (roof covering + walls rising to the roof), a geometry sanity
check independent of Unity.   uv run --project tools/worldgen python artifacts/buildings-r14/roof_plot.py [n]"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import shapely  # noqa: E402
import yaml  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402
from streetscape import buildings_mesh as BM  # noqa: E402
from streetscape import facade_kit as FK  # noqa: E402
from streetscape import roofs as RF  # noqa: E402

n = int(sys.argv[1]) if len(sys.argv) > 1 else 12
rdir = REPO / "Data" / "Regions" / "bialystok-industrial-c"
reg = yaml.safe_load((rdir / "region.yaml").read_text(encoding="utf-8"))
blds = BM.load(json.loads((rdir / "buildings.geojson").read_text(encoding="utf-8")), (reg["origin"]["x"], reg["origin"]["y"]), [])
tree = shapely.STRtree([b["poly"] for b in blds])
want = {"bdot:2BE4B431-C793-1BF0-E053-CC2BA8C0D140"}
sel = []
for b in blds:
    if b["typ"] != "house":
        continue
    key, poly, p = b["id"], b["poly"], b["props"]
    near = [blds[j]["poly"] for j in tree.query(poly.buffer(0.6)) if blds[j] is not b]
    r = RF.plan(poly, p, float(p.get("height_m") or 6.0), 0.0, lambda s, key=key: FK.hfloat(key, s), near, False)
    if isinstance(r, RF.MultiRoof) and (key in want or len(sel) < n):
        sel.append((key, poly, r))
cols = 4
rows = -(-len(sel) // cols)
fig = plt.figure(figsize=(4 * cols, 3.6 * rows))
for k, (key, poly, r) in enumerate(sel):
    ax = fig.add_subplot(rows, cols, k + 1, projection="3d")
    acc = BM.Acc()
    RF.build(acc, r, poly, "roof", soffit_mat="soffit", fascia_mat="fascia")
    polys, colors = [], []
    for (layer, mat), items in acc.d.items():
        if layer != "buildings":
            continue
        for V, T, *_ in items:
            for t in T:
                polys.append(V[t])
                colors.append({"roof": "#8a4b38", "fascia": "#dddddd", "soffit": "#bbbbbb", "hall_flashing": "#222222"}.get(mat, "#999"))
    ring = np.asarray(poly.exterior.coords)
    for a, b_ in zip(ring[:-1], ring[1:]):
        prof = r.profile(a, b_)
        L = float(np.hypot(*(b_ - a)))
        d = (b_ - a) / max(L, 1e-9)
        pts = [np.r_[a + d * u, z] for u, z in prof]
        wall = [np.r_[a, 0.0]] + pts + [np.r_[b_, 0.0]]
        polys.append(np.array(wall))
        colors.append("#e8dcc0")
    pc = Poly3DCollection(polys, facecolors=colors, edgecolors="#444", linewidths=0.2)
    ax.add_collection3d(pc)
    allv = np.concatenate(polys)
    c = allv.mean(0)
    s = (allv.max(0) - allv.min(0)).max() / 2
    ax.set_xlim(c[0] - s, c[0] + s); ax.set_ylim(c[1] - s, c[1] + s); ax.set_zlim(0, 2 * s)
    ax.view_init(elev=28, azim=-60 + 37 * k)
    ax.set_title(f"{key[-12:]} parts {len(r.parts)}", fontsize=8)
    ax.set_axis_off()
out = Path(__file__).parent / "roof_plot.png"
fig.savefig(out, dpi=70)
print(out, len(sel))
