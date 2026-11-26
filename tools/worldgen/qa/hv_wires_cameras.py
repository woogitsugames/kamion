"""ADR 0351 evidence cameras: add driver-eye views of the HV line at the tile edge to generated/control_cameras.json
(and the authored place list, so a later build_world keeps them). Height = NMT at the spot + eye.

    uv run --project tools/worldgen python tools/worldgen/qa/hv_wires_cameras.py
"""
import json
import math
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
CAMS = {
    # knyszyn-w: the HV line leaves the tile through the north edge at E 738 / 792 (seam supports): tile spans,
    # seam towers and the far-field spans beyond them in one frame
    "knyszyn-w": [("hv0351_seam_n", (640.0, 760.0), 18.0, 2.6, 3.0),
                  ("hv0351_far_ne", (900.0, 600.0), 40.0, 2.6, 2.0)],
    # dk65-07: the only ring HV line runs 2.7 km east of the tile (far field only)
    "dk65-07": [("hv0351_far_e", (990.0, 650.0), 70.0, 2.6, 1.5)],
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
    for cid, (e, n), hd, eye_m, pitch in cams:
        z = ground(region, e, n) + eye_m
        d = (math.sin(math.radians(hd)), math.cos(math.radians(hd)))
        note = "ADR 0351 (hv-wires-s24): HV towers + conductors across the tile edge / far field"
        cam = {"fov_deg": 60.0, "id": cid, "look_at": [round(e + 100 * d[0], 3), round(n + 100 * d[1], 3),
                                                        round(z + 100 * math.tan(math.radians(pitch)), 3)],
               "note": f"place camera: {note}", "pos": [e, n, round(z, 3)], "type": "persp"}
        doc["cameras"] = [c for c in doc["cameras"] if c["id"] != cid]
        doc["cameras"].insert(len(doc["cameras"]) - 1, cam)          # before ortho_tile
        pdoc["cameras"] = [c for c in pdoc["cameras"] if c["id"] != cid]
        pdoc["cameras"].append({"id": cid, "pos_en": [e, n], "heading_deg": hd, "eye_m": eye_m, "fov_deg": 60,
                                "pitch_deg": pitch, "note": note})
    gen.write_text(json.dumps(doc, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    place.write_text(json.dumps(pdoc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(region, [c[0] for c in cams])
