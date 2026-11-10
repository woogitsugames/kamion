"""Authored depot yard (override `kind: depot_yard`, ADR 0071 r10): what the orthophoto / open photos show inside a
private yard that neither OSM nor BDOT10k describe and the rules get wrong.

  no_parking_epsg2180   polygons where the rule car bays are suppressed (BDOT10k OT_KUKO_A "parking" drawn over a
                        truck manoeuvring yard filled it with rows of cars) - read by `no_parking()` before life.place
  clear_lamps_epsg2180  polygon whose rule lamps are removed (the rule lines them along the wrong side of the lane)
  lamps                 [{at: [x, y], face: [x, y], proto}] columns at the pole feet read off the orthophoto shadows,
                        arm toward `face`
  props                 [{proto, at: [x, y], yaw_deg | along: [dx, dy]}] containers and other static prototypes
Coordinates EPSG:2180. A prototype that the library does not know is reported in `stale`, never dropped silently.
"""

from __future__ import annotations

import math

import numpy as np
from shapely.geometry import Point, Polygon

KIND = "depot_yard"


def _yaw(f):
    return math.atan2(f[1], f[0]) - math.pi / 2


def no_parking(overrides, origin):
    """Local polygons of every `no_parking_epsg2180` ring."""
    o_ = np.asarray(origin, float)
    return [Polygon(np.asarray(r, float) - o_) for o in overrides if o.get("kind") == KIND
            for r in o.get("no_parking_epsg2180", [])]


def apply(pl, overrides, origin, known, report):
    rep = {"applied": [], "stale": []}
    o_ = np.asarray(origin, float)
    for o in overrides:
        if o.get("kind") != KIND:
            continue
        src = f"override:{o['id']}"
        removed = 0
        if o.get("clear_lamps_epsg2180"):
            poly = Polygon(np.asarray(o["clear_lamps_epsg2180"], float) - o_)
            keep = [it for it in pl.items if not (it["p"].startswith("lamp_") and poly.contains(Point(it["e"], it["n"])))]
            removed = len(pl.items) - len(keep)
            pl.items[:] = keep
        n_l = n_p = 0
        for L in o.get("lamps", []):
            proto = L.get("proto", "lamp_arc_9m")
            if known is not None and proto not in known:
                rep["stale"].append(f"{o['id']}:{proto}")
                continue
            p = np.asarray(L["at"], float) - o_
            f = np.asarray(L["face"], float) - o_ - p
            pl.add(proto, p, _yaw(f), src=f"{src}:lamp", group="lamp")
            n_l += 1
        for q in o.get("props", []):
            if known is not None and q["proto"] not in known:
                rep["stale"].append(f"{o['id']}:{q['proto']}")
                continue
            p = np.asarray(q["at"], float) - o_
            yaw = _yaw(q["along"]) if "along" in q else math.radians(q.get("yaw_deg", 0.0))
            pl.add(q["proto"], p, yaw, src=f"{src}:prop")
            n_p += 1
        rep["applied"].append({"id": o["id"], "lamps": n_l, "props": n_p, "rule_lamps_removed": removed})
    report["depot_yards"] = rep
    return rep
