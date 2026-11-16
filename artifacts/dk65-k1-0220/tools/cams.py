"""ADR 0220: control cameras over the K1 elements (bus bays, broken edge lines) in dk65-03/04/05, appended to
Data/Regions/<tile>/control_cameras_place.authored.json (replaced by id on re-run).

    uv run --project tools/worldgen python artifacts/dk65-k1-0220/tools/cams.py
"""
import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
from roads.route_km import km_to_region  # noqa: E402

CAMS = [
    # tile, id, km of the target, kind, note
    ("dk65-04", "k1_bay_1298_top", 12.980, "top", "ADR 0220: bus bay L km 12.948-13.010 + broken L edge line; pair = artifacts/dk65-k1-0220/evidence/dk65-04_km12.93-13.04_bay-L.jpg"),
    ("dk65-04", "k1_bay_1298_drive", 12.900, "drive", "ADR 0220: driver view towards the bus bay L km 12.95-13.01 (broken edge lines both sides before it)"),
    ("dk65-05", "k1_bay_1447_top", 14.473, "top", "ADR 0220: bus bay P km 14.440-14.506 + broken P edge line; pair = evidence/dk65-05_km14.40-14.55_bay-P.jpg"),
    ("dk65-05", "k1_bay_1447_drive", 14.400, "drive", "ADR 0220: driver view towards the bus bay P km 14.44-14.51"),
    ("dk65-03", "k1_dashed_1200_drive", 11.980, "drive", "ADR 0220: Ełcka with broken edge lines both sides (K1 km 12.00), lines 6.2 m apart"),
]


def main():
    by_tile = {}
    for tile, cid, km, kind, note in CAMS:
        q = km_to_region(tile, km, "P", 1.6)          # right lane of the direction of growing km
        tx, ty = q["tangent_en"]
        head = (math.degrees(math.atan2(tx, ty)) + 360.0) % 360.0
        if kind == "top":
            c = {"id": cid, "pos_en": [round(q["x"], 1), round(q["z"], 1)], "heading_deg": round(head, 1), "eye_m": 45,
                 "fov_deg": 50, "pitch_deg": -89.9, "note": note + " (top view, route up)"}
        else:
            c = {"id": cid, "pos_en": [round(q["x"], 1), round(q["z"], 1)], "heading_deg": round(head, 1), "eye_m": 2.5,
                 "fov_deg": 50, "pitch_deg": -4.0, "note": note}
        by_tile.setdefault(tile, []).append(c)
    for tile, cams in by_tile.items():
        f = REPO / "Data" / "Regions" / tile / "control_cameras_place.authored.json"
        d = json.loads(f.read_text(encoding="utf-8"))
        ids = {c["id"] for c in cams}
        d["cameras"] = [c for c in d["cameras"] if c["id"] not in ids] + cams
        f.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(tile, [c["id"] for c in cams])


if __name__ == "__main__":
    main()
