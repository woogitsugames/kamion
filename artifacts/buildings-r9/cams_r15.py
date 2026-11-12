"""ADR 0114 review cameras, added to the r13 / r14 set (cams_r13.json):
  r15_sill_5m / r15_sill_20m   square on the r10_block_3 wall from 5 m and 20 m (sill marks, measured with sill_contrast.py)
  r15_front_<style>            eye level on the carriageway, 40 deg oblique on the gate of a plot with that front fence
  r15_cab_<k>                  driver eye 2.5 m, 14 m before a gate, looking along the street (what the cab sees)
  r15_dist_<m>                 the r10_house_2 view from 60 / 120 / 250 m (pop check: what is still drawn)
Plots come from the generator report (Data/Regions/<id>/generated/streetscape_qa.json: plots.list).
    uv run --project tools/worldgen python artifacts/buildings-r9/cams_r15.py -> artifacts/buildings-r9/cams_r15.json"""
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
import yaml  # noqa: E402
from streetscape import buildings_mesh as BM  # noqa: E402

rdir = REPO / "Data" / "Regions" / "bialystok-industrial-c"
reg = yaml.safe_load((rdir / "region.yaml").read_text(encoding="utf-8"))
base = json.loads((HERE / "cams_r13.json").read_text(encoding="utf-8"))
cams = [c for c in base["cameras"] if not c["id"].startswith("r15_")]
r10 = {c["id"]: c for c in json.loads((rdir / "buildings_r10_cameras.json").read_text(encoding="utf-8"))["cameras"]}
_t = json.loads((rdir / "terrain.json").read_text(encoding="utf-8"))
_hm = np.fromfile(REPO / _t["encoding"]["file"], dtype="<u2").reshape(_t["samples"][1], _t["samples"][0])
_ox, _oy = reg["origin"]["x"], reg["origin"]["y"]


def ground(p):
    i = int(round(p[0] + _ox - _t["bbox"][0]))
    j = int(round(_t["bbox"][3] - (p[1] + _oy)))
    i, j = min(max(i, 0), _hm.shape[1] - 1), min(max(j, 0), _hm.shape[0] - 1)
    return _t["encoding"]["offset_m"] + float(_hm[j, i]) * _t["encoding"]["scale_m_per_unit"]


def add(cid, p, look, eye, look_h, fov, note):
    zg = ground(p)
    cams.append({"id": cid, "type": "persp", "kind": "photo_match", "seat": "file",
                 "pos": [round(float(p[0]), 2), round(float(p[1]), 2), round(zg + eye, 2)],
                 "look_at": [round(float(look[0]), 2), round(float(look[1]), 2), round(ground(look) + look_h, 2)],
                 "fov_deg": fov, "note": note})


# sill marks: square on the wall the r10_block_3 camera looks at
fc = json.loads((rdir / "buildings.geojson").read_text(encoding="utf-8"))
blds = {b["id"]: b for b in BM.load(fc, (_ox, _oy), [])}
b3 = blds[r10["r10_block_3"]["note"].split()[1]]
p0, l0 = np.array(r10["r10_block_3"]["pos"][:2]), np.array(r10["r10_block_3"]["look_at"][:2])
ring = np.asarray(b3["poly"].exterior.coords)[:, :2]
best = None
for a, b in zip(ring[:-1], ring[1:]):
    L = float(np.hypot(*(b - a)))
    if L < 8.0:
        continue
    t = (b - a) / L
    n = np.array([t[1], -t[0]])                       # outward normal of a CCW ring
    if (p0 - a) @ n <= 0:
        continue
    s = float(np.clip((l0 - a) @ t, 3.0, L - 3.0))
    hit = a + t * s
    d = float(np.hypot(*(hit - l0)))
    if best is None or d < best[0]:
        best = (d, hit, n, t, L, s)
_, hit, n, t, L, s = best
hit = hit + t * (min(L - s - 4.0, 0.0))
for dist, look_h, eye in ((5.0, 2.2, 1.7), (20.0, 4.5, 1.7)):
    add(f"r15_sill_{int(dist)}m", hit + n * dist, hit, eye, look_h, 55.0,
        f"ADR 0114: square on the wall of {b3['id']} from {dist} m (sill marks; pixel = {2 * dist * math.tan(math.radians(27.5)) / 1080 * 100:.1f} cm)")

qa = json.loads((rdir / "generated" / "streetscape_qa.json").read_text(encoding="utf-8"))
plots = [p for p in qa.get("plots", {}).get("list", []) if p["gate"] and p["access"]]
seen, k = set(), 0
for p in sorted(plots, key=lambda q: q["id"]):
    if p["front"] in seen:
        continue
    seen.add(p["front"])
    m, nn = np.array(p["gate"]["m"]), np.array(p["gate"]["n"])
    tt = np.array([-nn[1], nn[0]])
    road = m + nn * (p["access"]["d_cw"] + 2.5)
    add(f"r15_front_{p['front']}", road + tt * 5.0, m - nn * 2.0, 1.6, 1.1, 62.0,
        f"ADR 0114: plot {p['id']} ({p['age']}, front {p['front']}, side {p['side']}, gate {p['gate']['kind']}, "
        f"walk {p['access']['walk']}), eye 1.6 m on the carriageway")
    if k < 3:
        add(f"r15_cab_{k}", road - tt * 14.0 - nn * 0.5, m + tt * 6.0, 2.5, 1.2, 60.0,
            f"ADR 0114: driver eye 2.5 m, 14 m before the gate of plot {p['id']} ({p['front']})")
        k += 1
h2 = r10["r10_house_2"]
p0, l0 = np.array(h2["pos"][:2]), np.array(h2["look_at"][:2])
dv = (l0 - p0) / np.linalg.norm(l0 - p0)
for dist in (60, 120, 250):
    add(f"r15_dist_{dist}", l0 - dv * dist, l0, 2.5, 1.5, 60.0, f"ADR 0114: the r10_house_2 plot from {dist} m, eye 2.5 m (pop check)")
out = dict(base)
out["cameras"] = cams
(HERE / "cams_r15.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print(len(cams), [c["id"] for c in cams if c["id"].startswith("r15_")])
