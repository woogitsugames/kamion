"""ADR 0202: evidence cameras of the chain row -> artifacts/dojfix-0202/cameras.json (visual-qa -Gate3).

`bollards-photo-13m` keeps its id (ADR 0183) but is refitted: ADR 0183 put post 1 at 13 m because it assumed 0.80 m
posts. Here the pose is solved from the image columns of posts 1-4 in P11-063 (x = 630 / 750 / 858 / 966 of 1600 px,
review of cloud M58) and the built post positions (bay 2.0 m from the orthophoto), f = 1230 px (ASSUMED, hfov 66 deg);
the pixel height of the posts is then a CHECK of POST_H_M, not an input. Eye 1.5 m (WORKING_VALUE); pitch from the
foot of post 1 at y = 693 of 900 px.
"""
import glob
import json
import math

import numpy as np
from scipy.optimize import least_squares

it = []
for f in glob.glob("Data/raw/derived/bialystok-dojlidy/world/instances_*.json"):
    for i in json.load(open(f, encoding="utf-8"))["instances"]:
        if str(i.get("p", "")).startswith("bollard_rw"):
            it.append(i)
it.sort(key=lambda i: int(i["src"].rsplit(":", 1)[1]))
P = np.array([[i["e"], i["n"], i["z"]] for i in it])
assert len(P) == 8, len(P)
F, W, H = 1230.0, 1600, 900
X = np.array([630.0, 750.0, 858.0, 966.0])
t = (P[-1, :2] - P[0, :2]) / np.hypot(*(P[-1, :2] - P[0, :2]))
west = np.array([t[1], -t[0]])
if west[0] > 0:
    west = -west


def cols(q):
    cam, yaw = q[:2], q[2]
    d = P[:4, :2] - cam
    fwd = np.array([math.cos(yaw), math.sin(yaw)])
    right = np.array([fwd[1], -fwd[0]])
    return W / 2 + F * (d @ right) / (d @ fwd)


q0 = np.r_[P[0, :2] + west * 18.0 - t * 3.0, math.atan2(-west[1], -west[0])]
r = least_squares(lambda q: cols(q) - X, q0)
cam, yaw = r.x[:2], r.x[2]
dist = np.hypot(*(P[:, :2] - cam).T)
fwd = np.array([math.cos(yaw), math.sin(yaw)])
depth = (P[:, :2] - cam) @ fwd
z0 = float(P[0, 2])
eye = 1.5
# pitch (up) so the foot of post 1 falls at y = 693: y = H/2 - F * tan(elev - pitch)
elev = math.atan2(z0 - (z0 + eye), depth[0])
pitch = elev - math.atan((H / 2 - 693.0) / F)
look = np.r_[cam + fwd * 20.0, z0 + eye + 20.0 * math.tan(pitch)]
vfov = math.degrees(2 * math.atan(H / 2 / F))
print("fit residual px", np.round(cols(r.x) - X, 2), "cam", np.round(cam, 2), "yaw compass", round((90 - math.degrees(yaw)) % 360, 1),
      "pitch", round(math.degrees(pitch), 2))
print("post distance m", np.round(dist, 2))
print("post height px for 1.10 m (photo: 72 -> 64 on posts 1-4):", np.round(1.10 * F / depth[:4], 1),
      "; for 1.17 m:", np.round(1.17 * F / depth[:4], 1))
c = {"id": "bollards-photo-13m", "kind": "persp", "fov_deg": round(vfov, 2),
     "pos": [round(cam[0], 2), round(cam[1], 2), round(z0 + eye, 2)],
     "look_at": [round(look[0], 2), round(look[1], 2), round(look[2], 2)], "seat": "file",
     "note": "ADR 0202 refit of the P11-063 framing: posts 1-4 at x 630/750/858/966 of 1600 px, f 1230 px; post 1 at "
             f"{dist[0]:.1f} m (ADR 0183: 13 m for 0.80 m posts)"}
mid = P[3]
side = mid[:2] + west * 4.0
d = {"cameras": [c, {"id": "bollards-close-4m", "kind": "persp", "fov_deg": 40,
                     "pos": [round(side[0], 2), round(side[1], 2), round(float(mid[2]) + 1.6, 2)],
                     "look_at": [round(float(mid[0]), 2), round(float(mid[1]), 2), round(float(mid[2]) + 0.6, 2)], "seat": "file",
                     "note": "pedestrian eye 4 m west of post 4: chain colours per bay, bands, feet on the paving"}]}
json.dump(d, open("artifacts/dojfix-0202/cameras.json", "w", encoding="utf-8"), indent=1)
json.dump({"posts_enz": P.round(3).tolist(), "cam": cam.round(2).tolist(), "dist_m": dist.round(2).tolist()},
          open("artifacts/dojfix-0202/cams_fit.json", "w"), indent=1)
