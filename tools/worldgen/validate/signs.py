"""Check 4 (M37): signs.

  sign_facing_away   a generated route sign whose face does NOT point at the driver on the G3 route
                     (streetscape_qa.json furniture.route_signs[].faces_route_driver = false) - the sign
                     exists but the driver on that carriageway never sees its face;
  sign_height_rule   the generator's sign bottom-edge heights (roads.standards SIGN_H_MIN / SIGN_H_SIDEWALK /
                     SIGN_H_OVERHEAD) must stay inside the regulatory band 1.8-2.2 m over the carriageway /
                     sidewalk (rozporzadzenie o znakach: dolna krawedz 2.0 m w terenie zabudowanym,
                     2.2 m nad chodnikiem; WORKING_VALUE band). One finding if the rule is broken;
  sign_occluded      a sign on/near the G3 route whose line of sight from a driver position (eye 2.5 m,
                     sampled every 10 m along route_start) within the recognition distance is blocked by a
                     tree crown or a lamp (2D corridor test - geometry 2.5D: crowns carry a radius, lamps a
                     fixed pole radius).

Per-sign heights are not in the committed JSON (they live in the instance files under Data/raw, not in git),
so the height check validates the generator rule constant; documented as a limitation in the report.
"""

from __future__ import annotations

import math

import numpy as np
import shapely
from shapely.geometry import LineString, Point

from .common import DRIVER_EYE_M, RECOG_DIST_M, Finding, World

SIGN_BOTTOM_BAND_M = (1.80, 2.20)   # WORKING_VALUE regulatory band for the sign bottom edge above ground
LAMP_BLOCK_R_M = 0.35               # WORKING_VALUE: lamp pole radius for the occlusion corridor
ROUTE_SAMPLE_M = 10.0                # WORKING_VALUE: driver sampling step along the route


def _driver_positions(w: World) -> list[Point]:
    if len(w.route) < 2:
        return []
    line = LineString(w.route)
    n = max(2, int(line.length / ROUTE_SAMPLE_M) + 1)
    return [line.interpolate(i / (n - 1), normalized=True) for i in range(n)]


def check(w: World) -> list[Finding]:
    findings: list[Finding] = []

    # ---- orientation on the route
    for s in w.signs:
        if s.get("faces_route_driver") is False:
            findings.append(Finding("sign_facing_away", s["e"], s["n"], s["id"],
                                    f"sign {s.get('code')} faces away from the route driver "
                                    f"(offset {s.get('offset_m')} m)", severity="error",
                                    extra={"code": s.get("code"), "offset_m": s.get("offset_m"),
                                           "src": s.get("src")}))

    # ---- bottom-edge height rule (generator constants vs the regulatory band)
    from roads import standards as S
    for name, val in (("SIGN_H_MIN", S.SIGN_H_MIN), ("SIGN_H_SIDEWALK", S.SIGN_H_SIDEWALK),
                      ("SIGN_H_OVERHEAD", S.SIGN_H_OVERHEAD)):
        lo, hi = SIGN_BOTTOM_BAND_M if name != "SIGN_H_OVERHEAD" else (4.5, 5.5)  # overhead gantry band, WORKING_VALUE
        if not (lo <= float(val) <= hi):
            findings.append(Finding("sign_height_rule", 0.0, 0.0, f"standards.{name}",
                                    f"{name}={val} outside the allowed band [{lo}, {hi}] m", severity="error",
                                    extra={"value_m": float(val)}))

    # ---- occlusion of route signs by trees / lamps (2D corridor from driver positions)
    drivers = _driver_positions(w)
    blockers = [Point(t["e"], t["n"]).buffer(t["r"]) for t in w.trees]
    blockers += [Point(l["e"], l["n"]).buffer(LAMP_BLOCK_R_M) for l in w.lamps]
    blocker_tree = shapely.STRtree(blockers) if blockers else None
    for s in w.signs:
        sp = Point(s["e"], s["n"])
        best = None
        for d in drivers:
            dist = float(d.distance(sp))
            if dist > RECOG_DIST_M:
                continue
            if best is None or dist < best[0]:
                best = (dist, d)
        if best is None:
            continue
        dist, d = best
        corridor = LineString([d, sp]).buffer(max(0.4, dist * math.tan(math.radians(2.0))))  # ~2 deg half-angle
        if blocker_tree is not None:
            _pi, ti = blocker_tree.query([corridor], predicate="intersects")
            for b in set(np.atleast_1d(ti).tolist()):
                blk = blockers[b]
                if blk.contains(sp) or blk.distance(sp) < 0.3:
                    continue  # the blocker IS the sign post area; not an occlusion
                who = (f"tree:{w.trees[b]['id']}" if b < len(w.trees)
                       else f"lamp:{w.lamps[b - len(w.trees)]['id']}")
                findings.append(Finding("sign_occluded", s["e"], s["n"], s["id"],
                                        f"sign {s.get('code')} occluded by {who} from the route at {dist:.0f} m "
                                        f"(< recognition {RECOG_DIST_M:.0f} m)", severity="warn",
                                        extra={"code": s.get("code"), "blocker": who, "dist_m": round(dist, 1)}))
                break
    return findings
