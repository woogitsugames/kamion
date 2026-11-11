"""ADR 0107: plan view of the generated house plots (no Unity): footprints, plot outlines, fence bays by type, gates,
driveways, existing OSM barriers, road footprint from the built world's road layer is not needed - roads from the
graph buffer (debug approximation).   uv run --project tools/worldgen python artifacts/buildings-r15/plots_plot.py"""
import json, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np, shapely, yaml
from shapely.geometry import LineString
from streetscape import buildings_mesh as BM, plots as PL, sources as SRC
rid = "bialystok-industrial-c"
rdir = REPO / "Data" / "Regions" / rid
reg = yaml.safe_load((rdir / "region.yaml").read_text(encoding="utf-8"))
origin = np.array([reg["origin"]["x"], reg["origin"]["y"]])
blds = BM.load(json.loads((rdir / "buildings.geojson").read_text(encoding="utf-8")), tuple(origin), [])
graph = json.loads((rdir / "roads.graph.json").read_text(encoding="utf-8"))
lines = []
for e in graph["edges"]:
    g = e.get("geometry") or e.get("coords") or e.get("polyline")
    cs = g["coordinates"] if isinstance(g, dict) else g
    lines.append(LineString(np.asarray(cs, float)[:, :2] - origin).buffer(5.5))
roads = shapely.unary_union(lines)
src = SRC.load(rid)
barriers = [LineString(np.asarray(f["geometry"]["coordinates"], float)[:, :2] - origin) for f in src["osm"]["ways"]
            if f["tags"].get("barrier") in ("fence", "yes", "wall", "retaining_wall", "hedge")]
houses = [{"id": b["id"], "poly": b["poly"]} for b in blds if b["typ"] == "house"]
obst = [b["poly"] for b in blds if b["typ"] != "house" and b["poly"].area >= PL.BIG_BUILDING_M2]
plots = PL.plan(houses, roads, obst, barriers)
bpoly = shapely.unary_union([b["poly"] for b in blds])
cut = shapely.unary_union([roads.buffer(0.3), bpoly.buffer(0.3)])
near = PL._Near(); near.add([s for b in barriers for s in PL._segments(b)])
print("houses", len(houses), "plots", len(plots), "median m2", np.median([p["poly"].area for p in plots]))
cx, cy, R = (float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])) if len(sys.argv) > 3 else (-512, 132, 110)
fig, ax = plt.subplots(figsize=(14, 14))
for g in getattr(roads, "geoms", [roads]):
    ax.fill(*g.exterior.xy, color="#bbb")
for b in blds:
    ax.fill(*b["poly"].exterior.xy, color="#c96" if b["typ"] == "house" else "#888")
for b in barriers:
    ax.plot(*b.xy, color="k", lw=1.5)
COL = {"mesh": "g", "panel": "#333", "picket": "#a60", "concrete": "#77a"}
for p in plots:
    lay = PL.layout(p, cut, near)
    ax.plot(*p["poly"].exterior.xy, color="#ddd", lw=0.5)
    for name, m, n, q0, q1 in lay["bays"]:
        ax.plot([q0[0], q1[0]], [q0[1], q1[1]], color=COL[name.split("_")[2]], lw=1.2)
    for kind, c in (("gate", "r"), ("wicket", "m")):
        if lay[kind]:
            ax.plot(*lay[kind][1], "s", color=c, ms=4)
    for which, m, d, L in lay["drive"]:
        L = L or 6.0
        ax.plot([m[0], m[0] + d[0] * L], [m[1], m[1] + d[1] * L], color="#999", lw=4, alpha=0.6)
    near.add(lay["segs"])
ax.set_xlim(cx - R, cx + R); ax.set_ylim(cy - R, cy + R); ax.set_aspect("equal")
out = Path(__file__).parent / "plots_plan.png"
fig.savefig(out, dpi=80); print(out)
