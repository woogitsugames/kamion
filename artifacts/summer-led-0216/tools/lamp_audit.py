"""ADR 0216 audit: street lamps per road (nearest graph edge <= 16 m) with a built-up proxy (buildings within 60 m per
100 m of edge). Usage: python lamp_audit.py <region> [--all]  (run from the repo/worktree root)."""
import json, sys, glob, collections
import numpy as np
from shapely.geometry import LineString, Point, shape
from shapely.strtree import STRtree
rid = sys.argv[1]; show_all = "--all" in sys.argv
R = f"Data/Regions/{rid}"
reg = __import__("yaml").safe_load(open(f"{R}/region.yaml", encoding="utf-8")); ox, oy = reg["origin"]["x"], reg["origin"]["y"]
g = json.load(open(f"{R}/roads.graph.json", encoding="utf-8"))
edges = g["edges"]; lines = [LineString(e["geometry"]) for e in edges]; tree = STRtree(lines)
b = json.load(open(f"{R}/buildings.geojson", encoding="utf-8"))
bc = [shape(f["geometry"]).centroid for f in b["features"]]; btree = STRtree(bc) if bc else None
fam = collections.Counter(); per = collections.defaultdict(collections.Counter)
for f in sorted(glob.glob(f"Data/raw/derived/{rid}/world/instances_*.json")):
    for it in json.load(open(f, encoding="utf-8"))["instances"]:
        if not it["p"].startswith("lamp_"): continue
        fam[it["p"]] += 1
        p = Point(it["e"] + ox, it["n"] + oy); i = tree.nearest(p)
        if lines[i].distance(p) <= 16.0: per[edges[i]["osm_way"]][it["p"]] += 1
def a(e, k): return (e["attrs"].get(k) or {}).get("v")
ways = collections.defaultdict(list)
for e, l in zip(edges, lines): ways[e["osm_way"]].append((e, l))
rows = []
for w, el in ways.items():
    e0 = el[0][0]; L = sum(l.length for _, l in el)
    nb = len({j for _, l in el for j in (btree.query(l.buffer(60.0), predicate="intersects") if btree else [])})
    ref = f'{a(e0,"ref") or ""}/{a(e0,"old_ref") or ""}'
    main = a(e0, "highway") in ("primary", "secondary", "trunk", "primary_link") or "65" in ref or "671" in ref
    if show_all or main:
        rows.append(dict(way=w, hw=a(e0, "highway"), ref=ref, name=a(e0, "name"), len_m=round(L), bld_per_100m=round(nb / max(L, 1) * 100, 1),
                         lamps=dict(per.get(w, {}))))
print(json.dumps({"region": rid, "families": dict(sorted(fam.items())), "sodium": sum(v for k, v in fam.items() if ("old" in k and "_led_" not in k) or "arc" in k),
                  "roads": sorted(rows, key=lambda r: -r["len_m"])}, ensure_ascii=False, indent=1))
