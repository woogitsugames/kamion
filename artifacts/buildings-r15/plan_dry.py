"""Dry run of the plot plan on pass-1 road geometry (no export): report + plan picture.
    uv run --project tools/worldgen python artifacts/buildings-r15/plan_dry.py [out.png]"""
import sys, json, time, pickle
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
import numpy as np
from roads import pipeline
from streetscape import stage as SS, plots as PLT, paved as PV
t = time.time()
rid = "bialystok-industrial-c"
w = pipeline.build(rid)
print("pass1", round(time.time() - t), "s")
rp = SS.plan_plots(w, rid)
print("plots", len(rp["plots"]), "drops", len(rp["drops"]))
import collections
print("age", collections.Counter(p["age"] for p in rp["plots"]))
print("front", collections.Counter(p["front_style"] for p in rp["plots"]))
print("side", collections.Counter(p["side_style"] for p in rp["plots"]))
print("gates", sum(p["lay"]["gate"] is not None for p in rp["plots"]), "wickets", sum(p["lay"]["wicket"] is not None for p in rp["plots"]),
      "access", sum(p.get("access") is not None for p in rp["plots"]), "garage-aligned", sum(p["lay"]["garage"] is not None for p in rp["plots"]))
print("walk", collections.Counter((p["access"]["kind"], p["access"]["walk"]) for p in rp["plots"] if p.get("access")))
print("d_cw", sorted(round(p["access"]["d_cw"], 1) for p in rp["plots"] if p.get("access")))
n = PLT.apply_drops(w.net, rp["drops"])
print("applied", n)
import shapely
bp = shapely.union_all([p["foot"] for p in rp["plots"]])
items = PLT.paved_items(rp, rp["roads_poly"], bp, [])
print("paved items", collections.Counter(i["mat"] for i in items), {m: round(sum(i["poly"].area for i in items if i["mat"] == m)) for m in set(i["mat"] for i in items)})
class Buf:
    def __init__(s): s.parts = []
    def add(s, layer, mat, V, UV, T, **k): s.parts.append((layer, mat, len(T)))
rep = {}
b = Buf()
PLT.build(b, rp, lambda q: 0.0, None, rep)
print(json.dumps(rep["plots"], indent=0))
print("tris by layer", collections.Counter({(l, m): 0 for l, m, n in b.parts}) or "", {k: sum(n for l, m, n in b.parts if (l, m) == k) for k in set((l, m) for l, m, n in b.parts)})
if len(sys.argv) > 1:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(16, 16))
    for g in getattr(rp["roads_poly"], "geoms", [rp["roads_poly"]]):
        ax.fill(*g.exterior.xy, color="#bbb")
    for p in rp["plots"]:
        if p.get("lawn") is not None:
            for g in getattr(p["lawn"], "geoms", [p["lawn"]]):
                ax.fill(*g.exterior.xy, color="#bfe3a8")
        for q in (p.get("drive"), p.get("path")):
            if q is not None:
                for g in getattr(q, "geoms", [q]):
                    ax.fill(*g.exterior.xy, color="#999")
        for g in getattr(p["foot"], "geoms", [p["foot"]]):
            ax.fill(*g.exterior.xy, color="#c66")
        col = {"old": "#840", "prl": "#048", "new": "#000"}[p["age"]]
        for r in p["lay"]["runs"]:
            ax.plot([r["a"][0], r["b"][0]], [r["a"][1], r["b"][1]], color=col, lw=1.6 if r["front"] else 0.8)
        g = p["lay"]["gate"]
        if g is not None:
            ax.plot(*g["m"], "o", color="orange", ms=4)
    ax.set_aspect("equal")
    xs = [p["poly"].centroid.x for p in rp["plots"]]; ys = [p["poly"].centroid.y for p in rp["plots"]]
    if len(sys.argv) > 2:
        cx, cy, r = map(float, sys.argv[2:5])
        ax.set_xlim(cx - r, cx + r); ax.set_ylim(cy - r, cy + r)
    fig.savefig(sys.argv[1], dpi=110, bbox_inches="tight")
