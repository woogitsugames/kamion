"""Approach signs of a level crossing (ADR 0255): A-9 / A-10 with the G-1a...G-1f distance posts, the board
"Sygnalizacja automatyczna" and the U-1a / U-1b guide posts, one set per approach of every crossing of the opt-in rail
stage (streetscape.rail.Plan). Pure planning (positions, headings, codes): rail.json gets the list (`approach`),
streetscape.rail_props.place_approach turns it into prop instances.

Rules (all SOURCED unless marked):
  [R1] Dz.U. 2025 poz. 1105 (api.sejm.gov.pl/eli/acts/DU/2025/1105/text.pdf, SHA256 c3caeb07...7dd924):
       § 6 ust. 1 categories A-D; § 79 pkt 1 lit. a: A-9 before a crossing with barriers, A-10 without; pkt 3: G-1a-f;
       pkt 5 lit. a: U-1a / U-1b on approaches without barriers over 15-20 m from the outer rails, every 3 m, both sides
       of the road, the nearest 4 m from the outer rails; lit. b: outside the barriers when there are barriers;
       pkt 6: board "Sygnalizacja automatyczna" under A-9 / A-10 before categories B and C.
  [R2] Dz.U. 2019 poz. 2311 zał. 1 pkt 2.2.10 / 2.2.11 (api.sejm.gov.pl/eli/acts/DU/2019/2311/text.pdf, SHA256
       f94925ec...b550543): G-1a under the warning sign, G-1b at 2/3, G-1c at 1/3 of its distance; Tabela 2.2 distance
       ranges I / II / III (over 60 km/h: 150-300 / 100-200 / 50-100 m; up to 60 km/h: 50-100 / 35-70 / 20-35 m);
       shorter approaches: G-1b under the sign + G-1c at half (range II), G-1c under the sign + the sign with G-1f also
       on the left (range III); A-9 / A-10 with G-1d-f also on the left of one-way roads and where the crossing is seen
       from less than 100 m (> 60 km/h) - the generator does not know the visibility: override `left_side: true`;
       Tabela 1.11: G signs >= 2.00 m above the road (lower edge of G-1, the lowest plate).
Not modelled (ADR 0255 "Otwarte"): T-7 under A-10 at skew / curved C and D crossings, T-10 + A-30, B-20, the
pavement markings of § 79 pkt 4 (P-2 / P-4 / P-7b / P-12 / P-14) and the junction layouts of rys. 2.2.10.8 (a sign
that does not fit before a junction is reported, not moved onto the crossing road).
"""

from __future__ import annotations

import math

import numpy as np
from shapely.geometry import Point

from . import rail as RL

# Tabela 2.2 [R2]: (I, II, III) distance ranges of the warning sign / G-1 posts from the crossing, m
TABLE_2_2 = {"fast": ((150.0, 300.0), (100.0, 200.0), (50.0, 100.0)),       # over 60 km/h
             "slow": ((50.0, 100.0), (35.0, 70.0), (20.0, 35.0))}           # up to 60 km/h
# WORKING_VALUE: the generator's choice inside column I; 2/3 and 1/3 of it fall inside columns II and III
# (150 -> 100 / 50 m; 60 -> 40 / 20 m), so one number places the whole set.
SIGN_DIST_M = {"fast": 150.0, "slow": 60.0}
FAST_KMH = 60.0                 # [R2] Tabela 2.2 splits at 60 km/h
DEFAULT_KMH = None              # no maxspeed on the road line: treated as "over 60 km/h" (rural default, WORKING_VALUE)
END_CLEAR_M = 5.0               # WORKING_VALUE: a sign needs this much road line beyond it (junction / tile edge)
LOWER_EDGE_M = 2.00             # [R2] Tabela 1.11: G signs min. 2.00 m; the lowest plate of a set is a G-1
U1_FIRST_M = 4.0                # [R1] pkt 5 lit. a: nearest guide post 4 m from the outer rails
U1_STEP_M = 3.0                 # [R1] every 3 m
U1_SPAN_M = 16.0                # WORKING_VALUE inside the 15-20 m of [R1]: posts at 4, 7, 10, 13, 16 m
U1_AFTER_BARRIER_M = 3.0        # WORKING_VALUE: first post this far outside the barrier drive ([R1] lit. b: "na zewnątrz")
U1_LATERAL_M = 0.75             # WORKING_VALUE: post axis beyond the carriageway edge
CATEGORIES = ("A", "B", "C", "D")
WITH_BARRIERS = ("half", "double_half", "full", "gate", "yes")
G1_RIGHT = {1: "G-1c", 2: "G-1b", 3: "G-1a"}
G1_LEFT = {1: "G-1f", 2: "G-1e", 3: "G-1d"}


def category(c) -> str:
    """Category of a crossing (§ 6 ust. 1 [R1]) from its devices; an authored `category` wins.
    A: full barriers / gates or an attendant; B: automatic half barriers + signals; C: signals only; D: signs only."""
    cat = c.get("category")
    if cat is not None:
        if cat not in CATEGORIES:
            raise ValueError(f"rail_crossing category {cat!r} not in {CATEGORIES}")
        return cat
    if c.get("barrier") in ("full", "gate") or c.get("supervision") in ("attendant", "operator", "remote", "yes"):
        return "A"
    if c.get("barrier") in WITH_BARRIERS:
        return "B"
    if c.get("light"):
        return "C"
    return "D"


def warning_code(c) -> str:
    """A-9 before a crossing with barriers, A-10 without (§ 79 pkt 1 lit. a [R1])."""
    return "A-9" if c.get("barrier") in WITH_BARRIERS else "A-10"


def _road(plan, c):
    """(line, index) of the ground road centre line through the crossing (the one _find_crossings used), or None."""
    best = None
    for i, rl in enumerate(plan.road_lines):
        d = rl.distance(Point(c["p"]))
        if d <= RL.ROAD_SNAP_M and (best is None or d < best[0]):
            best = (d, i)
    return None if best is None else (plan.road_lines[best[1]], best[1])


def speed_class(plan, c, ri) -> tuple[str, float | None, str]:
    kmh = c.get("approach_kmh")
    src = "override"
    if kmh is None:
        kmh = plan.road_speeds[ri] if ri is not None and ri < len(plan.road_speeds) else None
        src = "osm maxspeed" if kmh is not None else "default (no maxspeed: over 60 km/h, WORKING_VALUE)"
    fast = kmh is None or float(kmh) > FAST_KMH
    return ("fast" if fast else "slow"), (None if kmh is None else float(kmh)), src


def layout(avail_m, cls):
    """Warning sign + G-1 posts of one side for an approach with `avail_m` metres of road before the crossing
    ([R2] pkt 2.2.10). [(distance from the outer rail m, stripes of the G-1 post, with the warning sign?)], the variant
    (I / II / III / None) and whether the set is repeated on the left verge (variant III)."""
    (i0, _), (ii0, ii1), (iii0, iii1) = TABLE_2_2[cls]
    d = SIGN_DIST_M[cls]
    if avail_m >= d:
        return [(d, 3, True), (d * 2 / 3, 2, False), (d / 3, 1, False)], "I", False
    if avail_m >= ii0:
        d2 = min(avail_m, ii1)
        return [(d2, 2, True), (d2 / 2, 1, False)], "II", False
    if avail_m >= iii0:
        return [(min(avail_m, iii1), 1, True)], "III", True
    return [], None, False


def plan_crossing(plan, ci, c, z_at):
    """(items, qa) of one crossing. Items: {crossing, kind: approach_sign | delineator, approach (+1/-1 = travel along
    / against the road line), side R/L, e, n, z, heading_deg (the face looks at the oncoming driver), dist_m (along the
    road from the outer rail), parts (approach_sign, top first) | code (delineator)}."""
    cat = category(c)
    code = warning_code(c)
    qa = {"crossing": ci, "category": cat, "warning": code, "approaches": [], "skipped": []}
    if c.get("approach_signs") is False:
        qa["skipped"].append("approach_signs: false (override)")
        return [], qa
    hit = _road(plan, c)
    if hit is None:
        qa["skipped"].append("no road centre line through the crossing")
        return [], qa
    line, ri = hit
    cls, kmh, ksrc = speed_class(plan, c, ri)
    qa.update(speed_class=cls, kmh=kmh, kmh_src=ksrc)
    sr = line.project(Point(c["p"]))
    sin_t = c["sin"]
    t = plan.tracks[c["track"]]
    outer_rail = max(abs(o) for o in t.offsets) + t.gauge / 2 + RL.RAIL_HEAD_W / 2    # axis -> outer rail head, across
    rail_along = outer_rail / sin_t                                                # ... along the road
    half_road = c["road_w"] / 2
    plates_extra = ["SA"] if cat in ("B", "C") else []
    barriers = c.get("barrier") in WITH_BARRIERS
    items = []

    def put(kind, a, side, dist, lateral, **kw):
        s = sr - a * (rail_along + dist)
        if not (0.0 <= s <= line.length):
            return False
        p = np.asarray(line.interpolate(s).coords[0])
        q = np.asarray(line.interpolate(min(line.length, s + 1.0)).coords[0]) - np.asarray(
            line.interpolate(max(0.0, s - 1.0)).coords[0])
        tvec = q / max(np.linalg.norm(q), 1e-9)
        drive = a * tvec                                       # travel direction of this approach
        right = np.array([drive[1], -drive[0]])
        pos = p + (right if side == "R" else -right) * (half_road + lateral)
        if plan.tile_local is not None and not plan.tile_local.contains(Point(pos)):
            qa["skipped"].append(f"{kind} approach {a:+d} {side} {dist:.1f} m: outside the tile")
            return False
        if not plan.road_poly.is_empty and plan.road_poly.contains(Point(pos)):
            qa["skipped"].append(f"{kind} approach {a:+d} {side} {dist:.1f} m: on a carriageway (junction?)")
            return False
        items.append({"crossing": ci, "kind": kind, "approach": a, "side": side, "e": round(float(pos[0]), 2),
                      "n": round(float(pos[1]), 2), "z": round(float(z_at(np.array([pos[0]]), np.array([pos[1]]))[0]), 3),
                      "heading_deg": RL._heading(-drive), "dist_m": round(float(dist), 2), **kw})
        return True

    for a in (1, -1):
        avail = (sr if a > 0 else line.length - sr) - rail_along - END_CLEAR_M
        posts, variant, left_too = layout(avail, cls)
        left = left_too or bool(c.get("left_side"))
        ap = {"approach": a, "available_m": round(float(avail), 1), "variant": variant, "left": left}
        if variant is None:
            qa["skipped"].append(f"approach {a:+d}: {avail:.1f} m of road before the crossing < "
                                 f"{TABLE_2_2[cls][2][0]:.0f} m (junction / tile edge): no warning sign")
        for side in (("R", "L") if left else ("R",)):
            g1 = G1_RIGHT if side == "R" else G1_LEFT
            for dist, n, with_sign in posts:                 # the warning sign first: G-1 posts never stand alone
                parts = ([code] + plates_extra + [g1[n]]) if with_sign else [g1[n]]
                if not put("approach_sign", a, side, dist, RL.SIGN_LATERAL, parts=parts) and with_sign:
                    qa["skipped"].append(f"approach {a:+d} {side}: warning sign not placed, its G-1 posts dropped")
                    break
        # U-1 guide posts, both verges
        if barriers:
            d_bar = c["half_track"] / sin_t + RL.BARRIER_SETBACK - rail_along             # barrier drive from the rail
            first = d_bar + U1_AFTER_BARRIER_M
        else:
            first = U1_FIRST_M / sin_t                       # 4 m from the outer rail measured across the track
        n_u1 = int(math.floor((U1_SPAN_M - U1_FIRST_M) / U1_STEP_M + 1e-9)) + 1
        for k in range(n_u1):
            for side, ucode in (("R", "U-1a"), ("L", "U-1b")):
                put("delineator", a, side, first + k * U1_STEP_M, U1_LATERAL_M, code=ucode)
        qa["approaches"].append(ap)
    return items, qa


def plan_all(plan, z_at):
    """(items, qa) for every crossing of `plan`; qa carries the categories, variants, skips and the clearance of the
    items from the tracks (must exceed rail.CLEARANCE_HALF)."""
    items, qas = [], []
    for ci, c in enumerate(plan.crossings):
        it, qa = plan_crossing(plan, ci, c, z_at)
        items += it
        qas.append(qa)
    best = None
    for m in items:
        p = Point(m["e"], m["n"])
        for t in plan.tracks:
            d = t.line.distance(p) - max(abs(o) for o in t.offsets)
            best = d if best is None else min(best, d)
    counts = {}
    for m in items:
        k = "+".join(m["parts"]) if m["kind"] == "approach_sign" else m["code"]
        counts[k] = counts.get(k, 0) + 1
    return items, {"crossings": qas, "counts": dict(sorted(counts.items())),
                   "min_track_distance_m": None if best is None else round(best, 2)}
