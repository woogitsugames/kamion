"""ADR 0190 cameras round the tower: every wall from 60 m (LOD0 if the chunk has it) and 200 m (LOD1), the roof.
-> artifacts/tower2-0190/tower_cameras.json (gate3-cameras schema; local E,N = EPSG:2180 - origin, U = EVRF2007)"""
import json, math
from pathlib import Path
import numpy as np
REPO = Path(__file__).resolve().parents[3]
R = REPO / "Data/Regions/bialystok-industrial-c"
o = json.loads((R / "generated/world_manifest.json").read_text(encoding="utf8"))["origin_epsg2180"]
BID = "bdot:2BE4B431-CA0F-1BF0-E053-CC2BA8C0D140"
f = next(f for f in json.loads((R / "buildings.geojson").read_text(encoding="utf8"))["features"] if f["id"] == BID)
p, g = f["properties"], f["geometry"]
ring = np.array(g["coordinates"][0] if g["type"] == "Polygon" else g["coordinates"][0][0])[:, :2] - [o["x"], o["y"]]
cen = (ring.min(0) + ring.max(0)) / 2
z0, h = p.get("ground_z_evrf2007") or 133.0, p["height_m"]
cams = []
def cam(cid, brg, dist, up, look_h, fov, note):
    n = np.array([math.sin(math.radians(brg)), math.cos(math.radians(brg))])
    pos = cen + n * dist
    cams.append({"id": cid, "type": "persp", "kind": "photo_match", "seat": "file",
                 "pos": [round(float(pos[0]), 2), round(float(pos[1]), 2), round(z0 + up, 2)],
                 "look_at": [round(float(cen[0]), 2), round(float(cen[1]), 2), round(z0 + look_h, 2)], "fov_deg": fov, "note": note})
for name, brg in (("se", 118.0), ("nw", 298.0), ("sw", 208.0), ("ne", 28.0)):
    cam(f"t190_{name}_60", brg, 60 + 18, 12, h * 0.55, 60.0, f"{name} wall from 60 m")
    cam(f"t190_{name}_200", brg, 200 + 18, 12, h * 0.55, 20.0, f"{name} wall from 200 m, tele (LOD1)")
cam("t190_s_150", 180.0, 150, 2, h * 0.6, 30.0, "from the south like the Mapillary photos (gable SW + wall SE)")
cam("t190_roof_s", 165.0, 110, h + 14, h + 2, 30.0, "roof masts from the south, above the roof")
cam("t190_roof_w", 255.0, 110, h + 14, h + 2, 30.0, "roof masts from the west, above the roof")
out = {"schema": "truck-sim-pl/gate3-cameras/1", "region": "bialystok-industrial-c",
       "frame": "local E,N,U (E,N = EPSG:2180 minus region origin; U = EVRF2007)", "cameras": cams}
(REPO / "artifacts/tower2-0190/tower_cameras.json").write_text(json.dumps(out, indent=1), encoding="utf8")
print(len(cams), ",".join(c["id"] for c in cams), "z0", z0, "h", h)
