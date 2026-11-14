"""ADR 0183: camera matched to P11-063 framing (post 1 ~13 m, eye 1.5 m, hfov ~66 deg = f 1230 px / 1600 px, posts
1-8 across x ~630-1310 px). Appends `bollards-photo-13m` to artifacts/bollards-0183/cameras.json."""
import glob, json, math
import numpy as np
it = []
for f in glob.glob("Data/raw/derived/bialystok-dojlidy/world/instances_*.json"):
    for i in json.load(open(f, encoding="utf-8"))["instances"]:
        if str(i.get("p", "")).startswith("bollard_rw"):
            it.append(i)
it.sort(key=lambda i: int(i["src"].rsplit(":", 1)[1]))
P = np.array([[i["e"], i["n"], i["z"]] for i in it])
t = (P[-1, :2] - P[0, :2]) / np.hypot(*(P[-1, :2] - P[0, :2]))
nE = np.array([t[1], -t[0]])                        # toward the carriageway (row walks NW->SE; road is west)
if nE @ np.array([-1.0, 0.0]) < 0:
    nE = -nE
cam = P[0, :2] + nE * 12.7 - t * 3.6   # r4: 0.6 m further, a sign post hid post 5 (review P2-4)
f = 1230.0
a0 = math.atan2(*(P[0, :2] - cam)[::-1]); a7 = math.atan2(*(P[-1, :2] - cam)[::-1])
# image x = 800 + f tan(yaw - a): post 1 at 630, post 8 at 1310 -> solve yaw on the mean
yaw = (a0 + math.atan((630 - 800) / f) + a7 + math.atan((1310 - 800) / f)) / 2
look = cam + 20 * np.array([math.cos(yaw), math.sin(yaw)])
z = float(P[:, 2].mean())
vfov = math.degrees(2 * math.atan(math.tan(math.radians(66) / 2) * 9 / 16))
c = {"id": "bollards-photo-13m", "kind": "persp", "fov_deg": round(vfov, 1),
     "pos": [round(cam[0], 2), round(cam[1], 2), round(z + 1.5, 2)],
     "look_at": [round(look[0], 2), round(look[1], 2), round(z + 0.4, 2)], "seat": "file",
     "note": "P11-063 framing: post 1 ~13 m, hfov 66 deg"}
d = json.load(open("artifacts/bollards-0183/cameras.json", encoding="utf-8"))
d["cameras"] = [x for x in d["cameras"] if x["id"] != c["id"]] + [c]
json.dump(d, open("artifacts/bollards-0183/cameras.json", "w", encoding="utf-8"), indent=1)
print(c, "dist post1", round(float(np.hypot(*(P[0, :2] - cam))), 2), "post8", round(float(np.hypot(*(P[-1, :2] - cam))), 2))
