"""Probe the JRG2 site: BDOT buildings near the OSM footprint, route geometry nearby, Mapillary frames."""
import json, glob, os, sys, math
from pathlib import Path
from shapely.geometry import shape, Polygon, LineString, Point

REPO = Path(__file__).resolve().parents[3]
R = REPO / "Data/Regions/bialystok-industrial-c"
ox, oy = 777995.0, 596223.0
ring = [[-222.74, -173.85], [-233.36, -165.13], [-238.92, -159.17], [-240.01, -160.4], [-262.44, -142.62], [-243.73, -118.95], [-229.11, -130.46], [-232.18, -134.34], [-217.59, -145.82], [-217.37, -145.53], [-206.88, -153.79], [-222.74, -173.85]]
fp = Polygon(ring)
d = json.load(open(R / "buildings.geojson", encoding="utf-8"))
print("crs", d["crs"])
for f in d["features"]:
    g = shape(f["geometry"])
    from shapely.affinity import translate
    g = translate(g, -ox, -oy)
    if g.distance(fp) < 60:
        p = f["properties"]
        print(json.dumps({"id": p["id"], "dist": round(g.distance(fp), 1), "inter": round(g.intersection(fp).area, 1), "area": p["area_m2"], "fn": p["function"], "h": p["height_m"], "hsrc": p["height_source"], "lod2": p["height_lod2_2017_m"], "eave": p["lod2_eave_rel_m"], "roof": p["roof_type_lod2"], "st": p["storeys"], "gz": p["ground_z_evrf2007"], "name": p["name"],
                          "ring": [[round(x, 2), round(y, 2)] for x, y in (g.exterior.coords if g.geom_type == "Polygon" else g.geoms[0].exterior.coords)]}, ensure_ascii=False))
r = json.load(open(R / "route_start.json"))
line = LineString(r["points_en"])
s = line.project(fp.centroid)
print("route station nearest", round(s, 1), "of", round(line.length, 1), "pt", line.interpolate(s).coords[0], "dist", round(line.distance(fp), 1))
for ds in (-150, -100, -50, 0, 50, 100):
    q = line.interpolate(s + ds)
    print("  s", round(s + ds), [round(c, 1) for c in q.coords[0]])
