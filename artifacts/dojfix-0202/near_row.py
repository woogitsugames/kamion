"""ADR 0202: authored overrides within 12 m of the chain row (argument: an overrides.yaml, e.g. Argon's dojgreen-0186)."""
import sys

import numpy as np
import yaml
from shapely.geometry import LineString, Polygon

O = np.array([780043.0, 590079.0])
ov = yaml.safe_load(open(sys.argv[1], encoding="utf-8"))["overrides"]
row = LineString(np.array([[780013.35, 590461.80], [780018.27, 590448.69]]) - O)
print("row local", [tuple(round(v, 2) for v in c) for c in row.coords])
for o in ov:
    geoms = []
    if o.get("polygon_epsg2180"):
        geoms.append(Polygon(np.asarray(o["polygon_epsg2180"], float) - O))
    for r in o.get("polygons_en") or []:
        geoms.append(Polygon(r))
    if o.get("polygon_en"):
        geoms.append(Polygon(o["polygon_en"]))
    for r in o.get("polygons_epsg2180") or []:
        geoms.append(Polygon(np.asarray(r, float) - O))
    if o.get("line_epsg2180"):
        geoms.append(LineString(np.asarray(o["line_epsg2180"], float) - O))
    for ln in o.get("lines") or []:
        if ln.get("line_epsg2180"):
            geoms.append(LineString(np.asarray(ln["line_epsg2180"], float) - O))
    for g in geoms:
        d = g.distance(row)
        if d < 12:
            print(round(d, 2), o["id"], o["kind"])
