"""ADR 0163 control cameras: the G7 photo positions (geotag of the Commons photo; azimuth UNVERIFIED -> both directions
of the nearest street axis) and one eye-level view along every house street of G7. Output: gate3-cameras schema."""
import csv, json, sys
from pathlib import Path
import numpy as np
from pyproj import Transformer
from shapely.geometry import LineString, Point
from shapely.ops import unary_union, linemerge

REPO = Path(__file__).resolve().parents[2]
REGION = REPO / "Data/Regions/bialystok-industrial-c"
O = np.array([777995.0, 596223.0])
U = 200.0          # above every roof: the runner re-seats `seat: road` cameras 1.7 m over the collision below
g = json.loads((REGION / "roads.graph.json").read_text(encoding="utf-8"))
edges = [(e["attrs"].get("name", {}).get("v"), LineString(np.asarray(e["geometry"], float)[:, :2] - O)) for e in g["edges"]]
tr = Transformer.from_crs(4326, 2180, always_xy=True)
cams = []


def cam(cid, p, d, note, fov=62.0, dist=30.0):
    d = np.asarray(d, float) / np.linalg.norm(d)
    q = np.asarray(p, float) + d * dist
    cams.append({"id": cid, "type": "persp", "kind": "photo_match", "seat": "road", "pos": [round(float(p[0]), 2), round(float(p[1]), 2), U],
                 "look_at": [round(float(q[0]), 2), round(float(q[1]), 2), U - 0.6], "fov_deg": fov, "note": note})


with open(REPO / "research/g7-street-greenery/manifest.csv", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        if not row["id"].startswith("G7-P"):
            continue
        x, y = tr.transform(float(row["lon"]), float(row["lat"]))
        p = np.array([x, y]) - O
        name, line = min(((n, l) for n, l in edges if n), key=lambda nl: nl[1].distance(Point(*p)))
        s = line.project(Point(*p))
        a, b = np.array(line.interpolate(max(s - 1, 0)).coords[0]), np.array(line.interpolate(min(s + 1, line.length)).coords[0])
        d = (b - a) / np.linalg.norm(b - a)
        pid = row["id"][3:].lower()
        for tag, dd in (("a", d), ("b", -d)):
            cam(f"g7_{pid}_{tag}", p, dd, f"{row['id']} {row['ulica']} geotag, along {name} ({tag}); photo files/g7-photo-{pid[1:]}.jpg")
for name in ["Kowieńska", "Lidzka", "Skidelska", "Wołkowyska", "Świsłocka", "Wileńska", "Grodzieńska", "Racławicka", "Łańcucka"]:
    u = unary_union([l for n, l in edges if n == name])
    u = linemerge(u) if u.geom_type == "MultiLineString" else u
    line = max(getattr(u, "geoms", [u]), key=lambda l: l.length)
    for tag, f0, sg in (("1", 0.12, 1), ("2", 0.88, -1)):
        s = line.length * f0
        a, b = np.array(line.interpolate(s).coords[0]), np.array(line.interpolate(s + sg * 2).coords[0])
        n = np.array([-(b - a)[1], (b - a)[0]]) / 2.0
        cam(f"g7_st_{name.encode('ascii', 'ignore').decode().lower()}_{tag}", a + n * 1.2, b - a, f"{name}: eye level along the street axis from {int(f0 * 100)} %")
out = {"schema": "truck-sim-pl/gate3-cameras/1", "region": "bialystok-industrial-c",
       "frame": "local E,N,U (E,N = EPSG:2180 minus region origin; U re-seated on the collision)", "cameras": cams}
(REGION / "veg0163_cameras.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(cams), [c["id"] for c in cams])
