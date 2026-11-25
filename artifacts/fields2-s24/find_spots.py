"""fields2-s24: side / cab cameras on strips of a chosen use beside the control route (visual-qa -Gate3 file).
Usage: python find_spots.py <tile> -> artifacts/fields2-s24/cams_<tile>.json"""
import glob
import json
import sys
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, "tools/worldgen")
from streetscape import sources as SR  # noqa: E402
from streetscape import vegetation as VG  # noqa: E402

tile = sys.argv[1]
d = Path("Data/Regions") / tile
r = yaml.safe_load((d / "region.yaml").read_text(encoding="utf-8"))
ox, oy = r["origin"]["x"], r["origin"]["y"]
src = SR.load(tile)
polys = {}
for f in (src.get("bdot10k") or {}).get("OT_PTTR_A") or []:
    g = VG.shapely.make_valid(VG.PV._poly_local(f["geometry"]["coordinates"], (ox, oy)))
    polys.setdefault((f.get("props") or {}).get("rodzaj"), []).append(g)
arable = VG.shapely.union_all(polys.get("uprawa na gruntach ornych", []))
grass = VG.shapely.union_all(polys.get("roślinność trawiasta", []))
cams = json.loads((d / "generated/control_cameras.json").read_text(encoding="utf-8"))
cams = cams["cameras"] if isinstance(cams, dict) else cams
inst = []
for f in glob.glob(f"Data/raw/derived/{tile}/world/instances_*.json"):
    inst += [(i["e"], i["n"], i["z"]) for i in json.load(open(f, encoding="utf8"))["instances"]]
inst = np.array(inst)


tj = json.loads((d / 'terrain.json').read_text(encoding='utf-8'))
hm = np.fromfile(tj['encoding']['file'], dtype='<u2').reshape(tj['samples'][1], tj['samples'][0])


def ground(e, n, z0=None):
    i_ = int(round(e + ox - tj['bbox'][0])); j_ = int(round(tj['bbox'][3] - (n + oy)))
    if not (0 <= i_ < hm.shape[1] and 0 <= j_ < hm.shape[0]):
        return z0
    return float(tj['encoding']['offset_m'] + hm[j_, i_] * tj['encoding']['scale_m_per_unit'])


def ploughed(L):
    z = np.zeros(L["fid"].shape)
    return VG._u01(VG._h32(L["fid"].astype(np.float64), z, 995)) < 0.5


want = ("disked", "stubble", "stubble_baled", "cereal_ripe", "meadow_mown", "meadow_hay")
out, seen = [], {}
for c in cams:
    if c.get("type") != "persp" or not str(c["id"]).startswith(("route_", "drive_")):
        continue
    p, la = np.array(c["pos"][:2]), np.array(c["look_at"][:2])
    h = (la - p) / max(np.hypot(*(la - p)), 1e-6)
    side = np.array([h[1], -h[0]])
    for sg in (1.0, -1.0):
        for lat in np.arange(10.0, 46.0, 4.0):
            for fwd in (10.0, 25.0):
                q = p + side * sg * lat + h * fwd
                ar = bool(VG.shapely.contains_xy(arable, q[0], q[1]))
                gr = bool(VG.shapely.contains_xy(grass, q[0], q[1]))
                if not (ar or gr):
                    continue
                L = VG.field_layout(np.array([q[0] + ox]), np.array([q[1] + oy]))
                u = VG.FIELD_USES[int(VG.field_use(L, ar)[0])]
                name = "ploughed" if u == "disked" and ploughed(L)[0] else u
                e = float(min(L["across"][0], L["w"][0] - L["across"][0]))
                key = (name, c["id"])
                if name.split("_")[0] in ("ploughed", "disked", "stubble", "cereal", "meadow") and key not in seen and name in want + ("ploughed",):
                    seen[key] = 1
                    z = c["pos"][2]
                    zg = ground(q[0], q[1], z - 2.5)
                    out.append({"id": f"f2_cab_{c['id']}_{name}", "type": "persp", "kind": "driver_eye",
                                "pos": [round(float(p[0]), 2), round(float(p[1]), 2), z],
                                "look_at": [round(float(q[0]), 2), round(float(q[1]), 2), round(zg, 2)], "fov_deg": 60.0,
                                "note": f"cab eye, field of use {name} {lat:.0f} m beside the route; strip edge {e:.1f} m, block edge {float(L['block_edge'][0]):.0f} m"})
                    # side camera standing at the field edge (1.7 m), looking along the rows over the strip edge
                    th = float(L["th"][0])
                    al = np.array([-np.sin(th), np.cos(th)])
                    if al @ h < 0:
                        al = -al
                    qs = q - al * 6.0
                    out.append({"id": f"f2_side_{c['id']}_{name}", "type": "persp", "kind": "field_side",
                                "pos": [round(float(qs[0]), 2), round(float(qs[1]), 2), round(zg + 1.7, 2)],
                                "look_at": [round(float(q[0] + al[0] * 14.0), 2), round(float(q[1] + al[1] * 14.0), 2), round(zg, 2)],
                                "fov_deg": 60.0, "note": f"standing in a {name} strip, looking along its rows"})
# tile-wide: the roomiest strip of each furrowed use, a standing camera along its rows and an oblique one above
hw = r['bbox']['width_m'] / 2 - 120
gx, gy = np.meshgrid(np.arange(-hw, hw, 12.0), np.arange(-hw, hw, 12.0))
G = np.column_stack([gx.ravel(), gy.ravel()])
G = G[VG.shapely.contains_xy(arable.buffer(-25.0), G[:, 0], G[:, 1])]
if len(G):
    L = VG.field_layout(G[:, 0] + ox, G[:, 1] + oy)
    u = VG.field_use(L, True)
    pl = ploughed(L)
    room = np.minimum(np.minimum(L['across'], L['w'] - L['across']), L['block_edge'] - 20.0)
    for name, m in (('ploughed', (u == VG.FIELD_USES.index('disked')) & pl), ('disked', (u == VG.FIELD_USES.index('disked')) & ~pl),
                    ('stubble', u == VG.FIELD_USES.index('stubble')), ('maize', u == VG.FIELD_USES.index('maize'))):
        if not m.any():
            continue
        b = int(np.argmax(np.where(m, room, -1e9)))
        q = G[b]; th = float(L['th'][b]); al = np.array([-np.sin(th), np.cos(th)]); nr = np.array([np.cos(th), np.sin(th)])
        zg = ground(q[0], q[1])
        qs = q - al * 6.0
        out.append({'id': f'f2_rows_{name}', 'type': 'persp', 'kind': 'field_side', 'pos': [round(float(qs[0]), 2), round(float(qs[1]), 2), round(ground(qs[0], qs[1]) + 1.7, 2)],
                    'look_at': [round(float(q[0] + al[0] * 14), 2), round(float(q[1] + al[1] * 14), 2), round(zg, 2)], 'fov_deg': 60.0, 'note': f'standing in a {name} strip, along its rows'})
        qc = q - nr * 22.0 - al * 10.0
        out.append({'id': f'f2_cross_{name}', 'type': 'persp', 'kind': 'field_side', 'pos': [round(float(qc[0]), 2), round(float(qc[1]), 2), round(ground(qc[0], qc[1]) + 2.5, 2)],
                    'look_at': [round(float(q[0] + nr[0] * 10), 2), round(float(q[1] + nr[1] * 10), 2), round(zg, 2)], 'fov_deg': 60.0, 'note': f'cab height 2.5 m, looking across the strips towards a {name} strip 22 m away'})
        qo = q - nr * 45.0 - al * 45.0
        out.append({'id': f'f2_obl_{name}', 'type': 'persp', 'kind': 'field_side', 'pos': [round(float(qo[0]), 2), round(float(qo[1]), 2), round(zg + 38.0, 2)],
                    'look_at': [round(float(q[0]), 2), round(float(q[1]), 2), round(zg, 2)], 'fov_deg': 60.0, 'note': f'oblique 38 m above a {name} strip'})
    # a headland: arable point 4 m inside a block border
    hd = np.abs(L['block_edge'] - 4.0) < 1.5
    if hd.any():
        b = int(np.flatnonzero(hd)[len(np.flatnonzero(hd)) // 2])
        q = G[b]; zg = ground(q[0], q[1])
        out.append({'id': 'f2_obl_headland', 'type': 'persp', 'kind': 'field_side', 'pos': [round(float(q[0] - 30), 2), round(float(q[1] - 30), 2), round(zg + 30.0, 2)],
                    'look_at': [round(float(q[0]), 2), round(float(q[1]), 2), round(zg, 2)], 'fov_deg': 60.0, 'note': 'oblique 30 m above a block border (headland / field track)'})
print(len(out), "cameras")
for o in out:
    print(o["id"], o["note"])
Path(f"artifacts/fields2-s24/cams_{tile}.json").write_text(json.dumps({"schema": "truck-sim-pl/gate3-cameras/1", "region": tile, "cameras": out}, indent=1), encoding="utf-8")
