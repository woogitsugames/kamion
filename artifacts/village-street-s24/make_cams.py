"""Extra control cameras of ADR 0349 (visual-qa -Gate3 file): cab-height and street-level views of DW671 in Krypno.
usage (repo root): uv run --project tools/worldgen python artifacts/village-street-s24/make_cams.py
-> artifacts/village-street-s24/cams_<region>.json. Heights = road surface of the generated profile (+ eye height);
the runner re-seats them on the road collision."""
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
from roads import pipeline as P  # noqa: E402

# (region, id, kind, E, N of the axis point, lateral offset right of travel [m], look-ahead [m], look lateral [m], note)
SPOTS = [
    ("dw671-tykocin-03", "vs_cab_t2590", "driver_eye", 205.0, -600.0, 1.9, 70.0, 0.0, "frame t2590 of build #8 (Krypno Wielkie), right lane"),
    ("dw671-tykocin-03", "vs_street_left_t2590", "exterior_3q", 215.0, -575.0, -3.2, 45.0, -1.5, "left kerb, along the street"),
    ("dw671-tykocin-03", "vs_street_right_t2590", "exterior_3q", 215.0, -575.0, 3.2, 45.0, 1.5, "right kerb, along the street"),
    ("dw671-tykocin-03", "vs_above_t2590", "rondo_above", 215.0, -575.0, 0.0, 28.0, 0.0, "cross-section from 45 m"),
    ("dw671-tykocin-03", "vs_cab_koscielne", "driver_eye", 800.0, 480.0, 1.9, 70.0, 0.0, "Krypno Koscielne, way 145989268 (was ground shoulder)"),
    ("dw671-tykocin-03", "vs_cab_village_start", "driver_eye", 925.0, 730.0, 1.9, 70.0, 0.0, "ground shoulder -> kerbed street at node 2133817368"),
    ("dw671-tykocin-03", "vs_cab_seam_04", "driver_eye", 75.0, -930.0, 1.9, 70.0, 0.0, "towards the seam with dw671-tykocin-04"),
    ("dw671-tykocin-04", "vs_cab_seam_03", "driver_eye", 30.0, 1000.0, 1.9, 70.0, 0.0, "just south of the seam with dw671-tykocin-03"),
    ("dw671-tykocin-04", "vs_cab_village_end", "driver_eye", -5.0, 915.0, 1.9, 70.0, 0.0, "end of the sidewalks (node 1123401728)"),
    ("dw671-tykocin-04", "vs_above_village_end", "rondo_above", -15.0, 890.0, 0.0, 28.0, 0.0, "end of the sidewalks from 45 m"),
]
EYE = {"driver_eye": 2.5, "exterior_3q": 2.2, "rondo_above": 45.0}


def main():
    out = {}
    for rid in sorted({s[0] for s in SPOTS}):
        w = P.build(rid, collision=False)
        cams = []
        for _rid, cid, kind, e, n, right, ahead, look_lat, note in [s for s in SPOTS if s[0] == rid]:
            pt = np.array([e, n])
            best = None
            for c in w.net.chains:
                sec = w.net.sec_list[int(c.sec_idx[len(c.sec_idx) // 2])]
                if sec.ref != "671":
                    continue
                d = np.hypot(*(c.line.p - pt).T)
                i = int(d.argmin())
                if best is None or d[i] < best[0]:
                    best = (float(d[i]), c, i)
            _, c, i = best
            t = c.line.t[i]
            if t[1] > 0:                       # travel direction of the recorded run: towards Tykocin (south-west)
                t = -t
            rn = np.array([t[1], -t[0]])       # right of travel
            z = float(c.z[i])
            p = c.line.p[i] + rn * right
            la = c.line.p[i] + t * ahead + rn * (right * 0.4 + look_lat)
            eye = EYE[kind]
            cams.append({"id": cid, "type": "persp", "kind": kind, "pos": [round(float(p[0]), 2), round(float(p[1]), 2), round(z + eye, 2)],
                         "look_at": [round(float(la[0]), 2), round(float(la[1]), 2), round(z + (1.2 if kind != "rondo_above" else 0.0), 2)],
                         "fov_deg": 60.0, "note": note,
                         "heading_deg": round(float(np.degrees(np.arctan2(t[0], t[1])) % 360.0), 1)})
        out[rid] = cams
        f = Path(__file__).with_name(f"cams_{rid}.json")
        f.write_text(json.dumps({"schema": "truck-sim-pl/gate3-cameras/1", "region": rid, "cameras": cams}, indent=1) + "\n",
                     encoding="utf-8", newline="\n")
        print(f, len(cams))
        for cm in cams:
            print("  ", cm["id"], cm["pos"], cm["heading_deg"])


if __name__ == "__main__":
    main()
