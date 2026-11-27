"""tykocin-plaza-s24: add the monument / furniture QA cameras to the authored place cameras of tile tykocin and (for the
'before' render only) to generated/control_cameras.json with the same formula as build_world (ground from a camera
that is already there). build_world rewrites the generated file from the authored one."""
import json
import math
from pathlib import Path

R = Path(__file__).resolve().parents[2] / "Data/Regions/tykocin"
NEW = [
    {"id": "czarniecki_figure_0320b", "pos_en": [438.6, -97.4], "heading_deg": 357, "eye_m": 1.6, "fov_deg": 27,
     "pitch_deg": 23,
     "note": "ADR 0320 dopisek QA: figure of the Czarniecki monument from the south, pedestrian eye 10.8 m away "
             "(pair = Commons 'Tykocin, pomnik Stefana Czarnieckiego, 1762 01')"},
    {"id": "czarniecki_34_0320b", "pos_en": [430.0, -95.6], "heading_deg": 41.5, "eye_m": 1.6, "fov_deg": 40,
     "pitch_deg": 13,
     "note": "ADR 0320 dopisek QA: whole monument from the south-west (pair = Commons 'Tykocin pomnik Stefana "
             "Czarnieckiego 08')"},
    {"id": "czarniecki_pedestal_0320b", "pos_en": [439.6, -93.4], "heading_deg": 346.5, "eye_m": 1.6, "fov_deg": 44,
     "pitch_deg": 14,
     "note": "ADR 0320 dopisek QA: pedestal, steps and fence from 7 m - weathering streaks (pair = Commons 'Tykocin "
             "pomnik Stefana Czarnieckiego 05')"},
    {"id": "plaza_furniture_0320b", "pos_en": [457.0, -100.6], "heading_deg": 287, "eye_m": 1.6, "fov_deg": 58,
     "pitch_deg": -7,
     "note": "ADR 0320 dopisek QA: benches, planters and bins along the south edge of the plaza, pedestrian eye"},
]
a = R / "control_cameras_place.authored.json"
d = json.loads(a.read_text(encoding="utf-8"))
ids = {c["id"] for c in d["cameras"]}
d["cameras"] += [c for c in NEW if c["id"] not in ids]
a.write_text(json.dumps(d, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
g = R / "generated/control_cameras.json"
gd = json.loads(g.read_text(encoding="utf-8"))
cams = gd["cameras"] if isinstance(gd, dict) else gd
ground = next(c for c in cams if c["id"] == "look_tykocin_plaza_cab_0325")["pos"][2] - 2.5
have = {c["id"] for c in cams}
for e in NEW:
    if e["id"] in have:
        continue
    hd = math.radians(e["heading_deg"])
    eye = ground + e["eye_m"]
    cams.append({"fov_deg": float(e["fov_deg"]), "id": e["id"],
                 "look_at": [round(e["pos_en"][0] + 100 * math.sin(hd), 3), round(e["pos_en"][1] + 100 * math.cos(hd), 3),
                             round(eye + 100 * math.tan(math.radians(e["pitch_deg"])), 3)],
                 "note": "place camera: " + e["note"], "pos": [e["pos_en"][0], e["pos_en"][1], round(eye, 3)],
                 "type": "persp"})
g.write_text(json.dumps(gd, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
print("ok", len(cams))
