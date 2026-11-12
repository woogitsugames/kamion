"""ADR 0124 cameras r16_* added to the r15 set (see the tail of this file). Header of cams_r15.py kept:
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
base = json.loads((HERE / "cams_r15.json").read_text(encoding="utf-8"))
cams = [c for c in base["cameras"] if not c["id"].startswith("r16_")]
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


# ADR 0132: no review camera stands inside a building (r16_door_3 of ADR 0124 stood inside a house: the "carport" of
# review 0124 P1-c was the door canopy, window reveals and eaves of that house seen from within, walls back-face culled)
import shapely  # noqa: E402
from shapely.geometry import Point, shape  # noqa: E402
_fc = json.loads((rdir / "buildings.geojson").read_text(encoding="utf-8"))
_foot = shapely.STRtree([shapely.affinity.translate(shape(f["geometry"]), -_ox, -_oy) for f in _fc["features"]])


def inside_building(p, margin=0.6):
    q = Point(float(p[0]), float(p[1]))
    return any(_foot.geometries[i].distance(q) < margin for i in _foot.query(q.buffer(margin + 1.0)))


# ---- ADR 0124 (review 0114 P1-r8-a "kamera kontrolna zjazdu z 3 m", P2-r8-f)
qa = json.loads((rdir / "generated" / "streetscape_qa.json").read_text(encoding="utf-8"))
P = sorted(qa["plots"]["list"], key=lambda q: q["id"])
gated = [p for p in P if p["gate"] and p["access"]]
seen = set()
k = 0
for p in gated:                                   # one driveway per front style, from 3 m, eye 1.5 m, on the carriageway
    if p["front"] in seen or k >= 8:
        continue
    seen.add(p["front"])
    m, nn = np.array(p["gate"]["m"]), np.array(p["gate"]["n"])
    tt = np.array([-nn[1], nn[0]])
    q = np.array(p["access"]["q"])
    add(f"r16_drive_{k}", q + nn * 2.2 + tt * 3.0, q - nn * 0.6, 1.5, 0.1, 62.0,
        f"ADR 0124: kerb drop of plot {p['id']} ({p['front']}, d_cw {p['access']['d_cw']}) from 3 m, eye 1.5 m")
    if k < 4:
        add(f"r16_cab_{k}", q + nn * 1.6 - tt * 16.0, q + tt * 10.0 - nn * 2.0, 2.5, 1.4, 60.0,
            f"ADR 0124: driver eye 2.5 m on the house street, 16 m before the driveway of plot {p['id']}")
        add(f"r16_kerb_{k}", q + nn * 0.8 - tt * 2.5, q + tt * 1.5, 0.6, 0.05, 55.0,
            f"ADR 0124: along the lowered kerb of plot {p['id']}, eye 0.6 m (kerb height / ramps)")
    k += 1
k = 0
for p in P:                                       # wicket -> door steps (fence clear of the steps)
    if not p.get("door") or not p.get("wicket") or k >= 4:
        continue
    d = p["door"][0]
    dp, dn = np.array(d[:2]), np.array(d[2:])
    wm = np.array(p["wicket"]["m"])                # r2: stand INSIDE the wicket (r1 stood behind the fence / in a wall)
    v = wm - dp
    dist = float(np.linalg.norm(v))
    if dist < 4.5 or inside_building(dp + v / dist * min(dist - 2.0, 6.0)):
        continue
    add(f"r16_door_{k}", dp + v / dist * min(dist - 2.0, 6.0), dp, 1.6, 1.1, 55.0,   # s12: 2 m inside the wicket (0.8 m stood in the hedge)
        f"ADR 0124: house door / steps of plot {p['id']} ({p['front']}) from inside the wicket, {min(dist - 2.0, 6.0):.1f} m")
    k += 1
k = 0
for p in P:                                       # garden close-ups (plants from 6-8 m, eye level)
    if k >= 5 or p["age"] != ("new", "prl", "old", "prl", "old")[k]:
        continue
    c = np.array(p["c"])
    if p["gate"]:
        nn = np.array(p["gate"]["n"])
        gm = np.array(p["gate"]["m"])               # r2: just inside the gate, looking over the garden at the house
        if inside_building(gm - nn * 1.0 + np.array([-nn[1], nn[0]]) * 0.8):
            continue
        add(f"r16_garden_{k}", gm - nn * 1.0 + np.array([-nn[1], nn[0]]) * 0.8, c, 1.7, 1.2, 65.0,
            f"ADR 0124: garden of plot {p['id']} ({p['age']}, {p['front']}) from just inside the gate, eye 1.7 m")
        k += 1
# ---- ADR 0132: the street as the reference frames show it (eye 1.6 m on the carriageway, along the street), one per
# road chain with gated plots, and two obliques from 30 m over the densest plot clusters (trees over the roofs)
chains = {}
for p in gated:
    chains.setdefault(p["access"]["chain"], []).append(p)
k = 0
for ch, pp in sorted(chains.items(), key=lambda kv: (-len(kv[1]), kv[0])):
    if k >= 6:
        break
    p = pp[len(pp) // 2]
    nn = np.array(p["gate"]["n"])
    tt = np.array([-nn[1], nn[0]])
    q = np.array(p["access"]["q"])
    for sg, tag in ((1.0, "a"), (-1.0, "b")):
        add(f"r17_street_{k}{tag}", q + nn * 1.4 - tt * (22.0 * sg), q + tt * (14.0 * sg) - nn * 1.0, 1.6, 1.8, 62.0,
            f"ADR 0132: along the house street of chain {ch} past plot {p['id']} (eye 1.6 m, {len(pp)} gated plots on the chain)")
    k += 1
C_ = np.array([p["c"] for p in P])
for k, (gx, gy) in enumerate(sorted({(int(c[0] // 200), int(c[1] // 200)) for c in C_}, key=lambda g: -int(((C_[:, 0] // 200 == g[0]) & (C_[:, 1] // 200 == g[1])).sum()))[:2]):
    sel = C_[(C_[:, 0] // 200 == gx) & (C_[:, 1] // 200 == gy)]
    c0 = sel.mean(0)
    add(f"r17_over_{k}", c0 + np.array([-55.0, -55.0]), c0, 34.0, 2.0, 55.0, f"ADR 0132: oblique over {len(sel)} plots (trees above the roofs)")
h2 = r10["r10_house_2"]
p0, l0 = np.array(h2["pos"][:2]), np.array(h2["look_at"][:2])
dv = (l0 - p0) / np.linalg.norm(l0 - p0)
add("r16_dist_200", l0 - dv * 200 + np.array([-dv[1], dv[0]]) * 25.0, l0, 6.0, 1.5, 60.0, "ADR 0124: the r10_house_2 plot from 200 m, eye 6 m (replaces r15_dist_250, which stood under the viaduct)")
out = dict(base)
out["cameras"] = cams
(HERE / "cams_r16.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print(len(cams), [c["id"] for c in cams if c["id"].startswith("r16_")])
