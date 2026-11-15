"""ADR 0211: clearance check of the DK8 tunnel from the exported chunk GLBs (no phone run).
Along both tunnel carriageways (OSM axes, 60 m beyond each portal), every 1 m, lateral -3.5..+3.5 m:
road collision height r0 (road_collision / collision_asphalt), lowest triangle of ANY other material above it
(overhead clearance; vertical triangles are skipped by the point test, so walls are checked laterally below), and the
horizontal distance from the sample to the nearest wall collision triangle (collision_fence)."""
import json
import sys

import numpy as np

sys.path.insert(0, "tools/worldgen")
sys.path.insert(0, "tools/worldgen/qa")
import junction_topview as jt  # noqa: E402
from roads import pipeline  # noqa: E402

R = "bialystok-kleeberga"
reg = pipeline.load_region(R)
ox, oy = reg["origin"]["x"], reg["origin"]["y"]
jt.colour = lambda n: (0, 0, 0)
W = jt.load_world(R)
names = sorted({n for n, *_ in W})
print("materials:", len(names), [n for n in names if "collision" in n or "wall" in n or "soffit" in n])
g = json.load(open(f"Data/Regions/{R}/roads.graph.json", encoding="utf-8"))


def tri_z(tris, x, y):
    m = (tris[:, :, 0].min(1) <= x) & (tris[:, :, 0].max(1) >= x) & (tris[:, :, 1].min(1) <= y) & (tris[:, :, 1].max(1) >= y)
    out = []
    for t in tris[m]:
        (x1, y1), (x2, y2), (x3, y3) = t[:, :2]
        d = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
        if abs(d) < 1e-9:
            continue
        a = ((y2 - y3) * (x - x3) + (x3 - x2) * (y - y3)) / d
        b = ((y3 - y1) * (x - x3) + (x1 - x3) * (y - y3)) / d
        c = 1 - a - b
        if min(a, b, c) >= -1e-6:
            out.append(a * t[0, 2] + b * t[1, 2] + c * t[2, 2])
    return out


ROAD = {n for n in names if n in ("road_collision", "collision_asphalt")}
fence = np.concatenate([t for n, t, *_ in W if n == "collision_fence"]) if any(n == "collision_fence" for n, *_ in W) else None
worst_over, worst_wall, n_s, blocked = 99.0, 99.0, 0, []
for way in (23982181, 76073122):
    e = next(e for e in g["edges"] if e["osm_way"] == way)
    P = np.array(e["geometry"], float)
    s = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
    t = (P[-1] - P[0]) / np.hypot(*(P[-1] - P[0]))
    nr = np.array([-t[1], t[0]])
    for q in np.arange(-60, s[-1] + 60, 1.0):
        base = P[0] + q * t if q < 0 else (P[-1] + (q - s[-1]) * t if q > s[-1] else
                                            np.array([np.interp(q, s, P[:, 0]), np.interp(q, s, P[:, 1])]))
        for off in (-3.5, -1.75, 0.0, 1.75, 3.5):
            x, y = base + off * nr - (ox, oy)
            road = [z for nm, tr, lo, hi in W if nm in ROAD and lo[0] <= x <= hi[0] and lo[1] <= y <= hi[1]
                    for z in tri_z(tr, x, y)]
            if not road:
                continue
            r0 = min(road)
            n_s += 1
            over = [z - r0 for nm, tr, lo, hi in W if nm not in ROAD and not nm.startswith(("marking", "decal"))
                    and lo[0] <= x <= hi[0] and lo[1] <= y <= hi[1] for z in tri_z(tr, x, y) if 0.3 < z - r0 < 8.0]
            if over:
                worst_over = min(worst_over, min(over))
                if min(over) < 4.5:
                    blocked.append((way, round(q), off, round(min(over), 2)))
            if fence is not None and 0 <= q <= s[-1] and abs(off) == 3.5:
                c = fence.mean(1)
                d = np.hypot(c[:, 0] - x, c[:, 1] - y)
                k = d < 6
                if k.any():
                    # distance to the wall triangles' planes, horizontally (point-to-segment in plan of their base edge)
                    tt = fence[k]
                    a, b = tt[:, 0, :2], tt[:, 1, :2]
                    ab = b - a
                    l2 = np.maximum((ab ** 2).sum(1), 1e-9)
                    u = np.clip(((np.array([x, y]) - a) * ab).sum(1) / l2, 0, 1)
                    dd = np.hypot(*(a + ab * u[:, None] - (x, y)).T)
                    worst_wall = min(worst_wall, float(dd.min()))
print(f"samples {n_s}, min overhead above road collision {worst_over:.2f} m, below 4.5 m: {len(blocked)}")
for b in blocked[:30]:
    print("  ", b)
print(f"min horizontal distance from a lane-edge sample (axis +-3.5 m) to a wall collision: {worst_wall:.2f} m")
