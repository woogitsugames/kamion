"""Diagnostics of the plot plan on pass-1 geometry: what every gate faces (ADR 0124 item 1)."""
import sys, collections, pickle
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
import numpy as np
from shapely.geometry import LineString, Point
from roads import pipeline
from streetscape import stage as SS, plots as PLT, paved as PV
rid = "bialystok-industrial-c"
w = pipeline.build(rid)
rp = SS.plan_plots(w, rid)
road_parts = [p for p in w.buf.parts if p.layer == "road"]
carriage = PV.road_footprint_polygon([p for p in road_parts if p.mat.startswith("road_")])
print("mats", collections.Counter(p.mat for p in road_parts))
c0 = w.net.chains[0]
print("chain meta keys", sorted(c0.meta.keys()), "side keys", sorted(c0.side["L"].keys()))
print("sec", getattr(c0, "sec_idx", None) is not None, [a for a in dir(c0) if not a.startswith("_")][:40])
chains = {c.id: c for c in w.net.chains}
for p in rp["plots"]:
    g = p["lay"]["gate"]
    if g is None:
        continue
    a = p.get("access")
    m, n = g["m"], g["n"]
    d_road = Point(*m).distance(rp["roads_poly"])
    d_car = Point(*m).distance(carriage)
    ray = LineString([m + n * 0.2, m + n * 30.0]).intersection(carriage)
    d_ray = None if ray.is_empty else round(float(Point(*m).distance(ray)), 1)
    ch = chains.get(a["chain"]) if a and a["chain"] else None
    print(p["id"][-8:], p["front_style"], "road_d", None if p["road_d"] is None else round(p["road_d"], 1), "d_fp", round(d_road, 1), "d_car", round(d_car, 1), "ray", d_ray,
          "acc", None if a is None else (round(a["d_cw"], 1), a["kind"], a["walk"], a["chain"][-24:] if a["chain"] else None),
          "meta", None if ch is None else {k: ch.meta[k] for k in ch.meta if k in ("cls", "class", "highway", "name")})
