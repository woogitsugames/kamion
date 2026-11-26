"""weathering-s24 evidence cameras (ADR 0238 / 0348 addendum): close views of roof weathering, block fences and the
wall-ground splash band on ul. Zlota (Tykocin). Adds them to generated/control_cameras.json and to the authored place
list (a later build_world keeps them). Height = NMT at the spot + eye.

    uv run --project tools/worldgen python tools/worldgen/qa/weathering_cameras.py
"""
import json
import math
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
NOTE = "weathering-s24 (ADR 0238/0348 addendum): roof weathering, block fences, wall-ground splash band"
# id, (E, N) region-local, heading deg, eye m, pitch deg, fov deg
CAMS = {
    "tykocin": [("wx_zlota_fence", (305.2, -115.3), 320.0, 1.6, -4.0, 55.0),
                ("wx_zlota_plinth", (295.0, -117.0), 345.0, 1.6, -6.0, 50.0),
                ("wx_roofs_low", (318.0, -123.0), 300.0, 9.0, -8.0, 55.0)],
}


def ground(region, e, n):
    t = json.loads((REPO / "Data/Regions" / region / "terrain.json").read_text(encoding="utf-8"))
    enc = t["encoding"]
    a = np.fromfile(REPO / enc["file"], dtype="<u2").reshape(t["samples"][1], t["samples"][0])
    x0, y0, x1, y1 = t["bbox"]
    ox, oy = (x0 + x1) / 2, (y0 + y1) / 2
    i, j = int(round(e + ox - x0)), int(round(y1 - (n + oy)))
    return enc["offset_m"] + float(a[j, i]) * enc["scale_m_per_unit"]


for region, cams in CAMS.items():
    gen = REPO / "Data/Regions" / region / "generated" / "control_cameras.json"
    doc = json.loads(gen.read_text(encoding="utf-8"))
    place = REPO / "Data/Regions" / region / "control_cameras_place.authored.json"
    pdoc = json.loads(place.read_text(encoding="utf-8")) if place.exists() else {"cameras": []}
    for cid, (e, n), hd, eye_m, pitch, fov in cams:
        z = ground(region, e, n) + eye_m
        d = (math.sin(math.radians(hd)), math.cos(math.radians(hd)))
        cam = {"fov_deg": fov, "id": cid, "look_at": [round(e + 100 * d[0], 3), round(n + 100 * d[1], 3),
                                                       round(z + 100 * math.tan(math.radians(pitch)), 3)],
               "note": f"place camera: {NOTE}", "pos": [e, n, round(z, 3)], "type": "persp"}
        doc["cameras"] = [c for c in doc["cameras"] if c["id"] != cid]
        doc["cameras"].insert(len(doc["cameras"]) - 1, cam)          # before ortho_tile
        pdoc["cameras"] = [c for c in pdoc["cameras"] if c["id"] != cid]
        pdoc["cameras"].append({"id": cid, "pos_en": [e, n], "heading_deg": hd, "eye_m": eye_m, "fov_deg": fov,
                                "pitch_deg": pitch, "note": NOTE})
    gen.write_text(json.dumps(doc, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    place.write_text(json.dumps(pdoc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(region, [c[0] for c in cams])
