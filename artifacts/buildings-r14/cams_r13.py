"""ADR 0097 extra review cameras (seat = file height): roofs of the house cluster of r10_house_1/2 from above and
around, a close look at a block wall (sill streaks, plinth line) and the far side of r10_block_1.
    uv run --project tools/worldgen python artifacts/buildings-r14/cams_r13.py  -> artifacts/buildings-r14/cams_r13.json"""
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
# ADR 0107 (review 0097 P2-m): r13_house2_az20 sat in a tree crown and r13_block1_az180 under the terrain (the height
# came from another camera's ground). Ground = NMT under the camera; azimuth swept off trees (instances_*.json).
_t = json.loads((rdir / "terrain.json").read_text(encoding="utf-8"))
_hm = np.fromfile(REPO / _t["encoding"]["file"], dtype="<u2").reshape(_t["samples"][1], _t["samples"][0])
_ox, _oy = reg["origin"]["x"], reg["origin"]["y"]


def ground(p):
    i = int(round(p[0] + _ox - _t["bbox"][0]))
    j = int(round(_t["bbox"][3] - (p[1] + _oy)))
    i, j = min(max(i, 0), _hm.shape[1] - 1), min(max(j, 0), _hm.shape[0] - 1)
    return _t["encoding"]["offset_m"] + float(_hm[j, i]) * _t["encoding"]["scale_m_per_unit"]


_trees = []
for f in sorted((REPO / "Data" / "raw" / "derived" / "bialystok-industrial-c" / "world").glob("instances_*.json")):
    d = json.loads(f.read_text(encoding="utf-8"))
    _trees += [(it["e"], it["n"]) for it in d["instances"]
               if isinstance(it, dict) and str(it.get("p", "")).startswith("tree_") and not str(it["p"]).startswith("tree_shrub")]
_trees = np.asarray(_trees, float).reshape(-1, 2)


def clear_of_trees(p, c):
    if not len(_trees):
        return True
    if np.min(np.hypot(*(_trees - p).T)) < 8.0:
        return False
    ab = c - p
    t = np.clip(((_trees - p) @ ab) / float(ab @ ab), 0.0, 1.0)
    return float(np.min(np.hypot(*(_trees - (p + t[:, None] * ab)).T))) > 3.5


def cam(cid, bid, zg, dist, az_deg, up, look_up, fov=55.0):
    c = np.asarray(blds[bid]["poly"].centroid.coords[0])
    for off in (0, 12, -12, 24, -24, 36, -36, 48, -48):
        a = math.radians(az_deg + off)
        p = c + dist * np.array([math.sin(a), math.cos(a)])
        if clear_of_trees(p, c):
            break
    zg = max(zg, ground(p) - up + 1.7)          # never lower than eye level above the ground under the camera
    cams.append({"id": cid, "type": "persp", "kind": "photo_match", "seat": "file",
                 "pos": [round(float(p[0]), 2), round(float(p[1]), 2), round(zg + up, 2)],
                 "look_at": [round(float(c[0]), 2), round(float(c[1]), 2), round(zg + look_up, 2)],
                 "fov_deg": fov, "note": f"ADR 0097 review camera, {bid}, {dist} m at az {az_deg} deg, {up} m up"})


h2 = "bdot:2BE4B431-C793-1BF0-E053-CC2BA8C0D140"
h1 = "bdot:2BE4B431-C792-1BF0-E053-CC2BA8C0D140"
for k, az in enumerate((20, 110, 200, 290)):
    cam(f"r13_house2_az{az}", h2, zg_of("r10_house_2"), 20.0, az, 9.0, 4.0)
cam("r13_house1_az200", h1, zg_of("r10_house_1"), 20.0, 200, 9.0, 4.0)
# ADR 0107 (P1-h): eye-level views of the plots round the two review houses (fence, gate, driveway, garden)
for az in (70, 160, 250, 340):
    cam(f"r14_plot2_eye_az{az}", h2, ground(np.asarray(blds[h2]["poly"].centroid.coords[0])), 17.0, az, 1.7, 1.5, fov=62.0)
cam("r14_plot1_eye_az250", h1, ground(np.asarray(blds[h1]["poly"].centroid.coords[0])), 17.0, 250, 1.7, 1.5, fov=62.0)
cam("r14_plots_aerial_low", h2, zg_of("r10_house_2"), 38.0, 215, 16.0, 1.0, fov=60.0)
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
