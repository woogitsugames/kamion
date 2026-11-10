"""r6 W-N7 acceptance on a control camera: the 8 nearest parked vehicles inside the view frustum -> distinct bodies,
colours, identical neighbour pairs, free stalls between them (gap > 1.6 x the 2.5 m pitch along the row).

  uv run --project tools/worldgen python tools/worldgen/qa/cars_stretch_qa.py [--camera stretch_01] [--n 8]
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]


def main(region, camera, n, out=None):
    gen = REPO / "Data/Regions" / region / "generated"
    cam = next(c for c in json.loads((gen / "control_cameras.json").read_text(encoding="utf-8"))["cameras"]
               if c["id"] == camera)
    man = json.loads((gen / "world_manifest.json").read_text(encoding="utf-8"))
    cars = []
    for ch in man["chunks"]:
        cars += [i for i in json.loads((REPO / ch["instances"]["file"]).read_text(encoding="utf-8"))["instances"]
                 if i["p"].startswith(("car_", "van_"))]
    pos = np.array(cam["pos"][:2])
    look = np.array(cam["look_at"][:2]) - pos
    look /= np.linalg.norm(look)
    half = math.radians(cam.get("fov_deg", 60) * 2340 / 1080 / 2) * 0.95       # horizontal half angle (approx.)
    vis = []
    for c in cars:
        d = np.array([c["e"], c["n"]]) - pos
        r = float(np.linalg.norm(d))
        if r < 2 or math.acos(max(-1, min(1, float(d @ look) / r))) > min(half, math.radians(80)):
            continue
        vis.append((r, c))
    vis.sort(key=lambda t: t[0])
    near = [c for _, c in vis[:n]]

    def body(p):
        return p.split("_")[1] if p.startswith("car_") else "van"

    def colour(p):
        return p.split("_")[-1].rstrip("2")
    E = np.array([[c["e"], c["n"]] for c in near])
    pairs = 0
    gaps = 0
    for i, c in enumerate(near):
        d = np.hypot(*(E - E[i]).T)
        for j in np.flatnonzero((d > 0.5) & (d < 2.9)):
            if j > i and near[j]["p"] == c["p"]:
                pairs += 1
    # free stalls: along each car's row direction (perpendicular to the nose), the next car is > 4 m away
    for i, c in enumerate(near):
        row = np.array([math.cos(c["yaw"]), math.sin(c["yaw"])])
        others = [np.array([o["e"], o["n"]]) for o in cars if o is not c]
        O = np.array(others) - E[i]
        al, ac = O @ row, O @ np.array([-row[1], row[0]])
        for sgn in (1, -1):
            sel = (sgn * al > 0.5) & (np.abs(ac) < 1.5)
            if sel.any() and 4.0 < float(np.min(sgn * al[sel])) < 9.0:
                gaps += 1
    rep = {"camera": camera, "nearest": [(round(r, 1), c["p"]) for r, c in vis[:n]],
           "bodies": len({body(c["p"]) for c in near}), "colours": len({colour(c["p"]) for c in near}),
           "identical_neighbour_pairs": pairs, "free_stall_gaps": gaps // 1}
    rep["pass"] = rep["bodies"] >= 4 and rep["colours"] >= 4 and pairs == 0 and gaps >= 1
    txt = json.dumps(rep, indent=1)
    print(txt)
    if out:
        Path(out).write_text(txt, encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="bialystok-industrial-c")
    ap.add_argument("--camera", default="stretch_01")
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--out")
    a = ap.parse_args()
    main(a.region, a.camera, a.n, a.out)
