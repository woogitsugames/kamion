"""Dry run of the plot plan on pass-1 road geometry (no export): report + plan picture.
    uv run --project tools/worldgen python artifacts/buildings-r16/plan_dry.py [out.png [cx cy r]]"""
import sys, json, time, collections
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
import numpy as np
import shapely
from roads import pipeline
from streetscape import stage as SS, plots as PLT, paved as PV, furniture as FU
t = time.time()
rid = "bialystok-industrial-c"
w = pipeline.build(rid)
print("pass1", round(time.time() - t), "s")
rp = SS.plan_plots(w, rid)
P = rp["plots"]
print("plots", len(P), "drops", len(rp["drops"]), "access", rp["access_stats"])
print("age", collections.Counter(p["age"] for p in P))
print("front", collections.Counter(p["front_style"] for p in P))
print("gates", sum(p["lay"]["gate"] is not None for p in P), "wickets", sum(p["lay"]["wicket"] is not None for p in P),
      "access", sum(p.get("access") is not None for p in P), "garage-aligned", sum(p["lay"]["garage"] is not None for p in P),
      "steps", sum(len(p["steps"]) for p in P), "garage doors", sum(len(p["garage_doors"]) for p in P))
print("d_cw", sorted(round(p["access"]["d_cw"], 1) for p in P if p.get("access")))
print("area median", round(float(np.median([p["poly"].area for p in P]))), "sum", round(sum(p["poly"].area for p in P)))
hk = PLT.apply_house_kerbs(w.net, P)
print("house kerbs", len(hk), round(sum(hk.values())), "m")
print("applied drops", PLT.apply_drops(w.net, rp["drops"]))
# fences crossing door steps / garage doors
bad = 0
for p in P:
    z = shapely.unary_union(p["door_zones"] or [shapely.Polygon()])
    for r in p["lay"]["runs"]:
        bad += shapely.LineString([r["a"], r["b"]]).intersects(z)
print("fence runs crossing a door zone:", bad)
bp = shapely.union_all([p["foot"] for p in P])
items = PLT.paved_items(rp, rp["roads_poly"], bp, [])
print("paved items", collections.Counter(i["mat"] for i in items), {m: round(sum(i["poly"].area for i in items if i["mat"] == m)) for m in set(i["mat"] for i in items)})
class Buf:
    def __init__(s): s.parts = []
    def add(s, layer, mat, V, UV, T, **k): s.parts.append((layer, mat, len(T)))
rep = {}
b = Buf()
surf = FU.SurfaceTop([p_ for p_ in w.buf.parts if p_.layer == "road"])
PLT.build(b, rp, lambda q: 0.0, surf, rep, items=[])
print(json.dumps({k: v for k, v in rep["plots"].items() if k != "list"}))
print("tris", {k: sum(n for l, m, n in b.parts if (l, m) == k) for k in sorted(set((l, m) for l, m, n in b.parts))})
if len(sys.argv) > 1:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(16, 16))
    for g in getattr(rp["roads_poly"], "geoms", [rp["roads_poly"]]):
        ax.fill(*g.exterior.xy, color="#ccc")
    for g in getattr(rp["carriage"], "geoms", [rp["carriage"]]):
        ax.fill(*g.exterior.xy, color="#999")
    for p in P:
        if p.get("lawn") is not None:
            for g in getattr(p["lawn"], "geoms", [p["lawn"]]):
                ax.fill(*g.exterior.xy, color="#bfe3a8")
        q = p.get("hard")
        if q is not None and not q.is_empty:
            for g in getattr(q, "geoms", [q]):
                ax.fill(*g.exterior.xy, color="#777")
        for g in getattr(p["foot"], "geoms", [p["foot"]]):
            ax.fill(*g.exterior.xy, color="#c66")
        for z in p["door_zones"]:
            ax.fill(*z.exterior.xy, color="#fc0", alpha=0.6)
        col = {"old": "#840", "prl": "#048", "new": "#000"}[p["age"]]
        for r in p["lay"]["runs"]:
            ax.plot([r["a"][0], r["b"][0]], [r["a"][1], r["b"][1]], color=col, lw=1.6 if r["front"] else 0.8)
        g = p["lay"]["gate"]
        if g is not None:
            ax.plot(*g["m"], "o", color="orange", ms=4)
        g = p["lay"]["wicket"]
        if g is not None:
            ax.plot(*g["m"], "o", color="blue", ms=3)
    ax.set_aspect("equal")
    if len(sys.argv) > 2:
        cx, cy, r = map(float, sys.argv[2:5])
        ax.set_xlim(cx - r, cx + r); ax.set_ylim(cy - r, cy + r)
    fig.savefig(sys.argv[1], dpi=110, bbox_inches="tight")
