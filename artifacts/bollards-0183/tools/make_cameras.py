"""ADR 0183 evidence cameras at the placed row (reads the built instances; local E, N, absolute U)."""
import glob, json, math, sys
import numpy as np
region = sys.argv[1] if len(sys.argv) > 1 else "bialystok-dojlidy"
items = []
for f in glob.glob(f"Data/raw/derived/{region}/world/instances_*.json"):
    d = json.load(open(f, encoding="utf-8"))
    for it in (d.get("instances") or d.get("items") or d if isinstance(d, list) else d.get("instances", [])):
        if isinstance(it, dict) and str(it.get("p", "")).startswith("bollard_rw"):
            items.append(it)
items.sort(key=lambda i: i["src"])
print(len(items), [(i["p"], i["e"], i["n"], i["z"], i["src"]) for i in items][:12])
P = np.array([[i["e"], i["n"], i["z"]] for i in items])
a, b = P[0], P[-1]
mid = (a + b) / 2
t = (b - a)[:2] / np.hypot(*(b - a)[:2])
nrm = np.array([-t[1], t[0]])              # left of the row direction
side = -1.0 if len(sys.argv) < 3 else float(sys.argv[2])     # carriageway side (-1 = right of the walk direction... set per site)
def cam(i, d, along, eye, fov, look_h=0.45, note=""):
    p = mid[:2] + side * nrm * d + t * along
    return {"id": i, "kind": "persp", "fov_deg": fov, "pos": [round(p[0], 2), round(p[1], 2), round(mid[2] + eye, 2)],
            "look_at": [round(mid[0], 2), round(mid[1], 2), round(mid[2] + look_h, 2)], "seat": "file", "note": note}
cams = [cam("bollards-close-5m", 5.0, -1.5, 1.6, 40, note="pedestrian eye, 5 m"),
        cam("bollards-detail-2m", 2.0, 0.6, 1.2, 40, note="detail of post / eyelets / links, 2 m"),
        cam("bollards-cab-20m", 20.0, -6.0, 2.4, 40, note="truck cab eye 2.4 m, 20 m"),
        cam("bollards-along-8m", 0.8, -(np.hypot(*(b - a)[:2]) / 2 + 8.0), 1.6, 40, note="along the row, 8 m before its start")]
json.dump({"cameras": cams}, open("artifacts/bollards-0183/cameras.json", "w", encoding="utf-8"), indent=1)
print(json.dumps(cams, indent=0)[:600])
