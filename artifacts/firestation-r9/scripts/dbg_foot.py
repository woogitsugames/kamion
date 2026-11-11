import json, sys
from pathlib import Path
import numpy as np, shapely
REPO = Path(__file__).resolve().parents[3]
d = json.loads((REPO / "art-source/world/landmarks/fire_station_jrg2/dims.json").read_text(encoding="utf-8"))
A = np.array(d["axis"]["origin_en"]); U = np.array(d["axis"]["u"]); U = U / np.hypot(*U); V = np.array([-U[1], U[0]])
def rect(u, v):
    return shapely.Polygon([A + U * a + V * b for a, b in ((u[0], v[0]), (u[1], v[0]), (u[1], v[1]), (u[0], v[1]))])
m = d["middle"]
blocks = shapely.union_all([rect(d["garage"]["u"], d["garage"]["v"]), rect(m["u"], [m["v_sw"], m["v_ne"]]), rect(d["hall"]["u"], d["hall"]["v"])])
foot = shapely.Polygon([[-262.92, -142.67], [-248.56, -154.39], [-248.18, -153.91], [-240.74, -159.51], [-239.85, -158.33], [-237.42, -160.1], [-233.51, -165.5], [-224.75, -172.17], [-209.53, -153.03], [-220.88, -143.87], [-219.95, -142.68], [-231.72, -133.16], [-229.42, -130.09], [-235.82, -125.08], [-243.99, -118.69], [-262.92, -142.67]])
print(blocks.geom_type, blocks.area, foot.area, blocks.symmetric_difference(foot).area)
print(shapely.hausdorff_distance(blocks.exterior, foot.exterior, densify=0.02))
print(max(foot.exterior.distance(shapely.Point(p)) for p in blocks.exterior.segmentize(0.2).coords),
      max(blocks.exterior.distance(shapely.Point(p)) for p in foot.exterior.segmentize(0.2).coords))
