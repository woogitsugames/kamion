"""Guide posts U-1a along rural sections of numbered roads (ADR 0324; critic s24 wave 6 # 3.5 / top-5 # 4).

Law / sources.
  Dz.U. 2019 poz. 2311 (t.j. rozporządzenia Ministra Infrastruktury z 3 lipca 2003 r. w sprawie szczegółowych warunków
  technicznych dla znaków i sygnałów drogowych oraz urządzeń bezpieczeństwa ruchu drogowego), załącznik nr 4
  "urządzenia bezpieczeństwa ruchu drogowego", słupki prowadzące U-1a / U-1b. The PDF of the annex is larger than the
  fetch limit of the tools here and WAS NOT READ (same note in streetscape.rail_props) - every dimension below that is
  not marked [GDDKiA] or [Commons] is WORKING_VALUE.
  [GDDKiA] gov.pl/web/gddkia-wroclaw/abc-oznakowania-drog---slupki-prowadzace (read 2026-11-21): "słupki ustawiane są
           standardowo co 100 m, a w przypadku łuków poziomych odpowiednio częściej"; red reflector = the rear lights
           of traffic in the same direction (right-hand side), white = oncoming headlights (left-hand side); the posts
           carry the kilometre / hectometre; used on national and voivodeship roads.
  [Commons] "PL urządzenie U-1a (prawy).svg" / "(lewy).svg" (public domain, Data/raw/refs/commons-u1a, docs/LICENSES.md):
           white post, a red band rising towards the carriageway, on it the reflector: red on the right-hand post,
           white on the left-hand post.

Rule (data, no survey):
  - only chains whose section is a numbered-road class (ROAD_CLASSES: trunk / primary / secondary + links), outside the
    built-up area (streetscape.built_up.Zone.at), on a kerbless side with a shoulder (roads.network.side_shoulder),
    not on a bridge deck, not on a roundabout, not within JUNCTION_CLEAR_M of the chain ends;
  - both sides at the same stations (a post pair), every SPACING_STRAIGHT_M [GDDKiA]; on curves by the radius table
    SPACING_CURVE (WORKING_VALUE: the table of the annex was not read);
  - the post stands on the ground shoulder, POST_INSIDE_EDGE_M inside its outer edge (WORKING_VALUE; never closer than
    MIN_FROM_CARRIAGEWAY_M to the carriageway edge);
  - no post within RAIL_CLEAR_M of a W-beam (on barrier sections the reflectors sit on the rail; U-1b not modelled) or
    within PROP_CLEAR_M of another pole / post already placed (signs, lamps, the U-1a of a level-crossing approach).
Prototype `guide_u1a_pl_r` / `guide_u1a_pl_l`: no collision mesh (a real U-1a is a hollow plastic post that folds under
a wheel; a rigid collider 0.2 m outside the shoulder would snag the trailer on every verge excursion).
"""
from __future__ import annotations

import math

import numpy as np

from . import props as PP

ROAD_CLASSES = ("trunk", "trunk_link", "primary", "primary_link", "secondary", "secondary_link")
SPACING_STRAIGHT_M = 100.0                 # [GDDKiA]
SPACING_CURVE = ((150.0, 20.0), (400.0, 33.0), (1250.0, 50.0))    # (radius below, spacing) WORKING_VALUE
JUNCTION_CLEAR_M = 20.0
POST_INSIDE_EDGE_M = 0.15
MIN_FROM_CARRIAGEWAY_M = 0.50
RAIL_CLEAR_M = 2.5
PROP_CLEAR_M = 1.5
H_M = 1.00                                 # post height above the ground, WORKING_VALUE
W_M, D_M = 0.12, 0.05                      # face width / depth, WORKING_VALUE
BAND_Z = (0.66, 0.90)                      # red band (lower edge at the low side, upper edge at the high side)
BAND_RISE_M = 0.06                         # the band rises this much across the face towards the carriageway [Commons]
REFL_W, REFL_H = 0.045, 0.16               # reflector on the band, WORKING_VALUE (read off the [Commons] drawing)

PROTOS = {}                                # prototype name -> (lod0, lod1, collision); read by props.build_all


def prototypes():
    return dict(PROTOS)


def post(side="right"):
    """U-1a. Local axes: +y = the face seen by the driver the post belongs to, +z up; the carriageway lies towards +x
    for the right-hand post and towards -x for the left-hand one (the band rises towards it)."""
    m = PP.Mesh()
    hx, hy = W_M / 2, D_M / 2
    m.box("paint_white_reflective", [0, 0, (H_M - 0.05) / 2], hx, hy, (H_M + 0.05) / 2)
    road = 1.0 if side == "right" else -1.0
    zl0, zl1 = BAND_Z[0], BAND_Z[1] - BAND_RISE_M           # away from the road
    zh0, zh1 = BAND_Z[0] + BAND_RISE_M, BAND_Z[1]           # towards the road
    for face, refl in ((1.0, "paint_ral3020" if side == "right" else "paint_white_reflective"),
                       (-1.0, "paint_white_reflective" if side == "right" else "paint_ral3020")):
        y = face * (hy + 0.002)
        xa, xb = -road * hx, road * hx                       # away -> towards the road
        V = np.array([[xa, y, zl0], [xb, y, zh0], [xb, y, zh1], [xa, y, zl1]])
        T = [(0, 1, 2), (0, 2, 3)] if face * road > 0 else [(0, 2, 1), (0, 3, 2)]
        m.add("paint_ral3020", V, T)
        zc = (BAND_Z[0] + BAND_Z[1]) / 2
        m.box(refl, [0, face * (hy + 0.004), zc], REFL_W / 2, 0.002, REFL_H / 2)
    # the band also wraps the two narrow sides
    for sx, z0, z1 in ((-road, zl0, zl1), (road, zh0, zh1)):
        m.box("paint_ral3020", [sx * (hx + 0.001), 0, (z0 + z1) / 2], 0.001, hy, (z1 - z0) / 2)
    return m, m, None


def spacing(radius_m: float) -> float:
    for r, sp in SPACING_CURVE:
        if radius_m < r:
            return sp
    return SPACING_STRAIGHT_M


def stations(c):
    """Post stations of one chain: marching from JUNCTION_CLEAR_M with the spacing of the local radius."""
    s0, s1 = float(c.t_a) + JUNCTION_CLEAR_M, float(c.length) - float(c.t_b) - JUNCTION_CLEAR_M
    out = []
    s = s0
    while s <= s1:
        out.append(s)
        k = abs(float(np.asarray(c.line.curvature(np.array([s]))).ravel()[0]))
        s += spacing(1.0 / k if k > 1e-6 else float("inf"))
    return out


def place(pl, net, zone, report, rails=()):
    """Instances of the posts in the Placer `pl`. zone: built_up.Zone (None = nowhere built-up); rails: polylines
    (n, 2) of the W-beams already built (lin.rail_runs)."""
    from scipy.spatial import cKDTree
    from roads import network as NW
    from .furniture import yaw_of
    PROTOS.clear()
    rp = [np.asarray(r, float)[:, :2] for r in rails if len(r)]
    kd_rail = cKDTree(np.concatenate(rp)) if rp else None
    have = np.array([[it["e"], it["n"]] for it in pl.items]) if pl.items else np.zeros((0, 2))
    kd_have = cKDTree(have) if len(have) else None
    n = {"right": 0, "left": 0}
    skipped = {"built_up": 0, "kerb_or_bridge": 0, "rail": 0, "prop": 0, "class": 0}
    for c in net.chains:
        if c.meta.get("absorbed") or c.roundabout or c.length < 2 * JUNCTION_CLEAR_M + 10.0:
            continue
        for s in stations(c):
            sec = c.section(float(s), net.sec_list)
            if sec is None or getattr(sec, "highway", None) not in ROAD_CLASSES:
                skipped["class"] += 1
                continue
            if zone is not None and zone.at(c, s):
                skipped["built_up"] += 1
                continue
            t, _ = c.line.frame(s)
            t = np.asarray(t, float)
            for letter, sgn in (("R", -1.0), ("L", 1.0)):
                sh = NW.side_shoulder(c, letter, s)
                if sh is None or bool(c.bridge[c.idx(s)]):
                    skipped["kerb_or_bridge"] += 1
                    continue
                off = max(float(sh[0]) + float(sh[1]) - POST_INSIDE_EDGE_M, MIN_FROM_CARRIAGEWAY_M)
                p = np.asarray(c.line.offset_point(s, sgn * (float(c.hw_at(s)) + off)), float)
                if kd_rail is not None and kd_rail.query(p)[0] < RAIL_CLEAR_M:
                    skipped["rail"] += 1
                    continue
                if kd_have is not None and kd_have.query(p)[0] < PROP_CLEAR_M:
                    skipped["prop"] += 1
                    continue
                # the driver the post belongs to: travelling +s on the right-hand side of +s, -s on the other
                dn = 1.0 if letter == "R" else -1.0
                two_way = not ((c.dirn > 0).mean() >= 0.99 or (c.dirn < 0).mean() >= 0.99)
                if two_way:
                    side = "right"
                else:                                   # one-way carriageway: the far side is a left-hand post
                    fwd = (c.dirn > 0).mean() >= 0.5
                    side = "right" if (letter == "R") == fwd else "left"
                    dn = 1.0 if fwd else -1.0
                name = "guide_u1a_pl_" + side[0]
                if name not in PROTOS:
                    PROTOS[name] = post(side)
                z = None
                if getattr(pl, "surf", None) is not None:
                    zt = pl.surf.top(float(p[0]), float(p[1]))
                    z = float(zt) if math.isfinite(zt) else None
                pl.add(name, p, yaw_of(-t * dn), z=z, src=f"rule:u1a:{c.id}:{letter}:{s:.0f}")
                n[side] += 1
    report["guide_posts_u1a"] = {**n, "skipped": skipped}
    return n["right"] + n["left"]
