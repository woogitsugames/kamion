"""ADR 0184 cameras: blocks / offices in chunks farther than 60 m from the start route (Low draws LOD1 only there),
seen from both sides of the longest footprint edge, 10 m above the ground. -> artifacts/atlas-0184/lod1_cameras.json"""
import json, math
from pathlib import Path
import numpy as np
REPO = Path(__file__).resolve().parents[3]
R = REPO / "Data/Regions/bialystok-industrial-c"
m = json.loads((R / "generated/world_manifest.json").read_text(encoding="utf8"))
o = m["origin_epsg2180"]
feats = {f["properties"]["id"]: f for f in json.loads((R / "buildings.geojson").read_text(encoding="utf8"))["features"]}
T = {"blk_a": ("bdot:2BE4B431-B246-1BF0-E053-CC2BA8C0D140", 45), "blk_b": ("bdot:28632721-2d7e-11ee-92d3-480fcf3c9bd7", 45),
     "blk_c": ("bdot:2BE4B431-AF4E-1BF0-E053-CC2BA8C0D140", 45), "hi_d": ("bdot:5565d6d1-197c-11ed-bb26-b8ca3aa2e5c2", 90),
     "tower": ("bdot:2BE4B431-CA0F-1BF0-E053-CC2BA8C0D140", 80)}
cams = []
for name, (bid, dist) in T.items():
    f = feats[bid]; p = f["properties"]; g = f["geometry"]
    ring = np.array(g["coordinates"][0] if g["type"] == "Polygon" else g["coordinates"][0][0])[:, :2] - [o["x"], o["y"]]
    cen = (ring.min(0) + ring.max(0)) / 2
    seg = np.diff(ring, axis=0); i = int(np.hypot(*seg.T).argmax()); d = seg[i] / np.hypot(*seg[i]); n = np.array([d[1], -d[0]])
    z0 = p.get("ground_z_evrf2007") or 133.0; h = p["height_m"]
    for side, s in (("p", 1), ("n", -1)):
        pos = cen + s * n * dist + d * dist * 0.35
        cams.append({"id": f"a184_{name}_{side}", "type": "persp", "kind": "photo_match", "seat": "file",
                     "pos": [round(pos[0], 2), round(pos[1], 2), round(z0 + 10, 2)],
                     "look_at": [round(cen[0], 2), round(cen[1], 2), round(z0 + h * 0.55, 2)], "fov_deg": 50.0,
                     "note": f"{bid} h {h} m storeys {p.get('storeys')}, {dist} m off the longest edge"})
out = {"schema": "truck-sim-pl/gate3-cameras/1", "region": "bialystok-industrial-c",
       "frame": "local E,N,U (E,N = EPSG:2180 minus region origin; U = EVRF2007)", "cameras": cams}
(REPO / "artifacts/atlas-0184/lod1_cameras.json").write_text(json.dumps(out, indent=1), encoding="utf8")
print(len(cams), [c["id"] for c in cams])
