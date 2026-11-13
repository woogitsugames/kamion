"""ADR 0162 probe cameras: shelters, lamp door/base, the G3 gantries (from the G3 camera poses), U-12a absence.

Writes artifacts/furn-0162/probes.json (cameras for visual-qa -Gate3) and sbs_subset.json (the sbs cameras whose
photos show the changed objects). z from the nearest instances' ground (instances_*.json of the derived world).
Run: uv run --project tools/worldgen python artifacts/furn-0162/tools/make_probes.py
"""
import glob
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
REG = ROOT / "Data" / "Regions" / "bialystok-industrial-c"
inst = []
for f in glob.glob(str(ROOT / "Data/raw/derived/bialystok-industrial-c/world/instances_*.json")):
    inst += json.loads(Path(f).read_text(encoding="utf-8"))["instances"]
P = np.array([[i["e"], i["n"]] for i in inst])
Z = np.array([i.get("z", 0.0) for i in inst])
ground = [k for k, i in enumerate(inst) if i["p"].startswith(("lamp_", "sign_post", "gantry_footing", "bus_shelter",
                                                                  "waste_bin", "signal_pole"))]


def zg(e, n):
    q = np.array([e, n])
    k = min(ground, key=lambda j: float(np.hypot(*(P[j] - q))))
    return float(Z[k])


def cam(cid, e, n, hdg, eye=1.5, fov=60.0, pitch=0.0, dist=30.0, note=""):
    z = zg(e, n) + eye
    a = math.radians(hdg)
    look = [e + math.sin(a) * dist, n + math.cos(a) * dist, z + math.tan(math.radians(pitch)) * dist]
    return {"id": cid, "type": "persp", "fov_deg": fov, "pos": [round(e, 3), round(n, 3), round(z, 3)],
            "look_at": [round(v, 3) for v in look], "seat": "file", "note": f"ADR 0162 probe. {note}"}


cams = []
# G3 camera poses (research/gptpro/3-s8-signs manifest: Mapillary geometry, heading = compass angle)
cams.append(cam("f162-p40-g3p001", -457.1, -21.0, 313.0, fov=50, pitch=8, note="G3-P001..P004 kino 2024 frame pose"))
cams.append(cam("f162-approach-g3p012", -242.4, -222.1, 314.0, fov=50, pitch=8, note="G3-P012/P013 kino 2024"))
cams.append(cam("f162-tys-e1-g3p009", -555.3, 331.6, 173.8, fov=50, pitch=8, note="G3-P009 strudel 2024 E-1"))
cams.append(cam("f162-tys-vms-g3p010", -552.2, 256.5, 181.5, fov=50, pitch=8, note="G3-P010 VMS"))
cams.append(cam("f162-tys-portal-g3p005", -556.3, 144.5, 187.3, fov=50, pitch=8, note="G3-P005..P008"))
# shelters: every bus_shelter* instance, three nearest the route corridor + one of each variant
sh = [i for i in inst if i["p"].startswith("bus_shelter")]
seen = set()
for i in sorted(sh, key=lambda i: (i["p"], i["e"])):
    if i["p"] in seen:
        continue
    seen.add(i["p"])
    yaw = i["yaw"]                       # rotates local +y (road side) onto the facing direction
    f = np.array([-math.sin(yaw), math.cos(yaw)])
    r = np.array([math.cos(yaw), math.sin(yaw)])
    eye = np.array([i["e"], i["n"]]) + f * 7.0 + r * 4.0
    hdg = math.degrees(math.atan2(-(f * 7.0 + r * 4.0)[0], -(f * 7.0 + r * 4.0)[1]))
    c = cam(f"f162-shelter-{i['p']}", float(eye[0]), float(eye[1]), hdg, eye=1.6, fov=55, pitch=-2,
            dist=8.0, note=f"{i['p']} at {i['e']:.1f},{i['n']:.1f}")
    cams.append(c)
# lamp door / grey base: a lamp_11m nearest the route start area, camera 3 m behind it (door side) at knee height
lamps = [i for i in inst if i["p"] == "lamp_11m"]
if lamps:
    i = min(lamps, key=lambda i: abs(i["e"] + 400) + abs(i["n"] + 100))
    yaw = i["yaw"]
    f = np.array([-math.sin(yaw), math.cos(yaw)])
    eye = np.array([i["e"], i["n"]]) - f * 2.6 + np.array([math.cos(yaw), math.sin(yaw)]) * 0.8
    d = np.array([i["e"], i["n"]]) - eye
    cams.append(cam("f162-lamp-door", float(eye[0]), float(eye[1]), math.degrees(math.atan2(d[0], d[1])), eye=1.2,
                    fov=45, pitch=-12, dist=3.0, note=f"lamp_11m at {i['e']:.1f},{i['n']:.1f}"))
out = ROOT / "artifacts" / "furn-0162"
(out / "probes.json").write_text(json.dumps({"cameras": cams}, indent=1), encoding="utf-8")
sbs = json.loads((REG / "sbs_cameras.json").read_text(encoding="utf-8"))
keep = ("275528677534382", "3281350541967811", "297817221966185", "339463879238809", "4312632558767412",
        "1801374876712141", "494288258686575", "468026894483428", "182011943700132")
sub = [c for c in sbs["cameras"] if any(c["id"].endswith(k) for k in keep)]
(out / "sbs_subset.json").write_text(json.dumps({"cameras": sub}, indent=1), encoding="utf-8")
print(len(cams), "probes;", len(sub), "sbs cameras;", sorted(seen))
