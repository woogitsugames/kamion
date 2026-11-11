"""ADR 0097 extra review cameras (seat = file height): roofs of the house cluster of r10_house_1/2 from above and
around, a close look at a block wall (sill streaks, plinth line) and the far side of r10_block_1.
    uv run --project tools/worldgen python artifacts/buildings-r13/cams_r13.py  -> artifacts/buildings-r13/cams_r13.json"""
import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
import numpy as np  # noqa: E402
import yaml  # noqa: E402
from streetscape import buildings_mesh as BM  # noqa: E402

rdir = REPO / "Data" / "Regions" / "bialystok-industrial-c"
reg = yaml.safe_load((rdir / "region.yaml").read_text(encoding="utf-8"))
fc = json.loads((rdir / "buildings.geojson").read_text(encoding="utf-8"))
blds = {b["id"]: b for b in BM.load(fc, (reg["origin"]["x"], reg["origin"]["y"]), [])}
base = {c["id"]: c for c in json.loads((rdir / "buildings_r10_cameras.json").read_text(encoding="utf-8"))["cameras"]}


def zg_of(cid):
    return base[cid]["pos"][2] - 11.7


cams = []


def cam(cid, bid, zg, dist, az_deg, up, look_up, fov=55.0):
    c = np.asarray(blds[bid]["poly"].centroid.coords[0])
    a = math.radians(az_deg)
    p = c + dist * np.array([math.sin(a), math.cos(a)])
    cams.append({"id": cid, "type": "persp", "kind": "photo_match", "seat": "file",
                 "pos": [round(float(p[0]), 2), round(float(p[1]), 2), round(zg + up, 2)],
                 "look_at": [round(float(c[0]), 2), round(float(c[1]), 2), round(zg + look_up, 2)],
                 "fov_deg": fov, "note": f"ADR 0097 review camera, {bid}, {dist} m at az {az_deg} deg, {up} m up"})


h2 = "bdot:2BE4B431-C793-1BF0-E053-CC2BA8C0D140"
h1 = "bdot:2BE4B431-C792-1BF0-E053-CC2BA8C0D140"
for k, az in enumerate((20, 110, 200, 290)):
    cam(f"r13_house2_az{az}", h2, zg_of("r10_house_2"), 20.0, az, 9.0, 4.0)
cam("r13_house1_az200", h1, zg_of("r10_house_1"), 20.0, 200, 9.0, 4.0)
cam("r13_houses_aerial", h2, zg_of("r10_house_2"), 60.0, 250, 35.0, 2.0, fov=60.0)
b3 = base["r10_block_3"]["note"].split()[1]
b1 = base["r10_block_1"]["note"].split()[1]
# block_3: 14 m from the camera-side wall centre, eye level (sill streaks, plinth line, balconies)
p0, l0 = np.array(base["r10_block_3"]["pos"][:2]), np.array(base["r10_block_3"]["look_at"][:2])
dv = (l0 - p0) / np.linalg.norm(l0 - p0)
p = l0 - dv * 14.0
z3 = zg_of("r10_block_3")
cams.append({"id": "r13_block3_close", "type": "persp", "kind": "photo_match", "seat": "file",
             "pos": [round(float(p[0]), 2), round(float(p[1]), 2), round(z3 + 1.7, 2)],
             "look_at": [round(float(l0[0]), 2), round(float(l0[1]), 2), round(z3 + 4.0, 2)], "fov_deg": 60.0,
             "note": "ADR 0097: 14 m in front of the r10_block_3 look-at point, eye level"})
for az in (0, 180):
    cam(f"r13_block1_az{az}", b1, zg_of("r10_block_1"), 45.0, az, 1.7, 6.0, fov=60.0)
out = {"schema": "truck-sim-pl/gate3-cameras/1", "region": "bialystok-industrial-c",
       "frame": "local E,N,U (E,N = EPSG:2180 minus region origin; U = EVRF2007)", "cameras": cams}
(Path(__file__).parent / "cams_r13.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print(len(cams), [c["id"] for c in cams])
