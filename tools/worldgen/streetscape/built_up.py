"""ADR 0279 "P1 - wdrożenie" (D25): obszar zabudowany (built-up area) and the sign rules that depend on it.

Law. Prawo o ruchu drogowym (t.j. Dz.U. 2024 poz. 1251) art. 2 pkt 15: "obszar zabudowany - obszar oznaczony
odpowiednimi znakami drogowymi" = D-42 / D-43; art. 20 ust. 1: 50 km/h in it; ust. 3 pkt 1 lit. d: 90 km/h outside on
other roads (pkt 2 lit. b: 70 km/h for lorries > 3.5 t and combinations - the truck of the game).
Placement: Dz.U. 2019 poz. 2311 zał. 1 = [Z1] (PDF D20192311-c1.pdf, sha256 f94925ec...b550543, Dz.U. pages):
  pkt 5.2.48.1 (s. 244) D-42 on the right of the road into the place, at the boundary; on every boundary when the road
           alternates; NO D-42 / D-43 where the gap between an end and the next start would be < 300 m; 1200 x 700 mm;
  pkt 5.2.48.2 (s. 245) the boundary follows RESIDENTIAL buildings along the road (not commercial / industrial
           outskirts, not houses set back from the road), near "początek chodnika", gates, parking, junctions;
  pkt 5.2.49 (s. 245) D-43 on the right of the road, in the same cross-section as the D-42 of the other direction;
  pkt 2.2.8 (s. 64) A-7 on roads with v_dop > 60 km/h preceded 150-300 m before by A-7 + tabliczka T-1;
  pkt 3.2.21 (s. 126) B-20 on roads with v_dop > 60 km/h preceded 150-300 m before by A-7 + plate "Stop <m>";
  pkt 2.1.3 (s. 50) T-1: real distance to the dangerous place, to 10 m;
  pkt 2.2.9 in the wording of Dz.U. 2026 poz. 132 (text.pdf sha256 6b62d655...c3a6): A-8 before every roundabout
           signed with C-12, NOT where an E-1 board stands before it or where the roundabout lies in the built-up area
           and is visible from a sufficient distance; pkt 2.1.2 (s. 50) + 2310 § 3 ust. 2: 150-300 m (v > 60) / <= 100 m.

Data rule (no OSM D-42 / city_limit node): BDOT10k OT_PTZB_A "tereny zabudowy" of a residential RODZAJ within
ROADSIDE_M of the road axis, or a kerbed / footway edge of the generated road (pkt 5.2.48.2 "początek chodnika"),
mark a station as built-up. Runs shorter than the regulation's 300 m between built-up runs are built-up (no sign pair);
an isolated built-up run shorter than MIN_INSIDE_M is not a place. OSM signs win: no rule boundary within OSM_WINS_M of
a mapped D-42 / D-43 / city_limit. The boundary is ESTIMATED (the legal boundary is where the authority put the sign) -
an authored override (later) moves it; every rule sign is listed in report["built_up"] for the QA review.
"""

from __future__ import annotations

import numpy as np
import shapely
import shapely.affinity
import shapely.geometry

from roads import standards as S
from roads.network import RURAL

from . import furniture as FU
from . import sign_norms as SN

RESIDENTIAL = ("jednorodzinna", "wielorodzinna", "zagrodowa")   # BDOT10k OT_PTZB_A RODZAJ (pkt 5.2.48.2)
ROADSIDE_M = 60.0          # WORKING_VALUE: houses this near the road axis are "bezpośrednio związane z drogą"
MIN_OUTSIDE_M = 300.0      # pkt 5.2.48.1: an end-start gap below 300 m gets no D-43 / D-42 pair (SOURCED)
MIN_INSIDE_M = 100.0       # WORKING_VALUE: an isolated built-up run shorter than this is not a place
STEP_M = 5.0               # sampling of a chain
END_CLEAR_M = 15.0         # WORKING_VALUE: no rule sign within this of a junction trim / chain end
OSM_WINS_M = 300.0         # WORKING_VALUE: a mapped boundary sign this near replaces the rule boundary
RULE_CLASSES = ("GP", "G", "Z")     # WORKING_VALUE: roads into a place that get D-42 / D-43 by rule (L / D: OSM only)
SPEED_BUILT_UP = 50.0      # art. 20 ust. 1
SPEED_OUTSIDE = 90.0       # art. 20 ust. 3 pkt 1 lit. d (the road's permitted speed; lorries 70, pkt 2 lit. b)
FAST_KMH = 60.0            # pkt 2.2.8 / 3.2.21 / 2.1.2: "powyżej 60 km/h"
OSM_BOUNDARY = ("D-42", "D-43")


def area(src, origin):
    """Residential built-up land (local metres) buffered by ROADSIDE_M, or an empty geometry."""
    polys = []
    for f in (src.get("bdot10k") or {}).get("OT_PTZB_A", []) or []:
        if str((f.get("props") or {}).get("rodzaj", "")).strip() not in RESIDENTIAL:
            continue
        g = f.get("geometry") or {}
        try:
            shp = shapely.geometry.shape(g)
        except Exception:                 # malformed geometry: skipped, never fatal
            continue
        if shp.is_empty:
            continue
        polys.append(shapely.affinity.translate(shp, -float(origin[0]), -float(origin[1])).buffer(0))
    if not polys:
        return shapely.Polygon()
    a = shapely.union_all(polys).buffer(ROADSIDE_M)
    shapely.prepare(a)
    return a


def area_for(net, src, origin):
    """Cached on the network object (one tile = one network)."""
    a = getattr(net, "_built_up_area", None)
    if a is None:
        a = area(src, origin)
        try:
            net._built_up_area = a
        except Exception:
            pass
    return a


def is_built_up(a, xy) -> bool:
    return bool(a is not None and not a.is_empty and a.contains(shapely.Point(float(xy[0]), float(xy[1]))))


def legal_speed(sec, built_up: bool) -> float:
    """Permitted speed of a section: the OSM maxspeed when tagged, else the statutory default (art. 20)."""
    if sec.maxspeed and (getattr(sec, "maxspeed_src", None) or "osm") != "default":
        return float(sec.maxspeed)
    return SPEED_BUILT_UP if built_up else SPEED_OUTSIDE


def kerbed(c, s):
    for side in ("L", "R"):
        if FU.side_surface_offset(c, side, s)[0] != RURAL:
            return True
    return False


def runs(c, a):
    """[(inside, s0, s1)] along chain c after the rules of pkt 5.2.48.1 (short gaps / isolated houses)."""
    L = float(c.length)
    if L < 2 * STEP_M:
        return []
    ss = np.arange(0.0, L + 1e-6, STEP_M)
    P = c.line.point(ss)
    inside = shapely.contains_xy(a, P[:, 0], P[:, 1]) if not a.is_empty else np.zeros(len(ss), bool)
    inside = np.asarray(inside, bool) | np.array([kerbed(c, float(s)) for s in ss])
    out = []
    k0 = 0
    for k in range(1, len(ss) + 1):
        if k == len(ss) or inside[k] != inside[k0]:
            out.append([bool(inside[k0]), float(ss[k0]), float(ss[k - 1])])
            k0 = k
    # boundaries sit between the samples
    for i in range(1, len(out)):
        m = (out[i - 1][2] + out[i][1]) / 2
        out[i - 1][2] = out[i][1] = m
    out[0][1], out[-1][2] = 0.0, L
    changed = True
    while changed and len(out) > 1:
        changed = False
        for i, r in enumerate(out):
            ln = r[2] - r[1]
            if not r[0] and ln < MIN_OUTSIDE_M:                      # pkt 5.2.48.1: < 300 m -> no pair
                r[0], changed = True, True
            elif r[0] and 0 < i < len(out) - 1 and ln < MIN_INSIDE_M:  # isolated houses
                r[0], changed = False, True
        merged = [out[0]]
        for r in out[1:]:
            if r[0] == merged[-1][0]:
                merged[-1][2] = r[2]
            else:
                merged.append(r)
        out = merged
    return [tuple(r) for r in out]


def boundaries(net, a):
    """Rule boundaries: [(chain, s, dn_in)] - dn_in = +1 when the built-up side lies at larger s."""
    res = []
    if a is None or a.is_empty:
        return res
    for c in net.chains:
        if c.meta.get("absorbed") or c.roundabout or c.length < MIN_OUTSIDE_M:
            continue
        rr = runs(c, a)
        for r0, r1 in zip(rr, rr[1:]):
            s = r0[2]
            if s < c.t_a + END_CLEAR_M or s > c.length - c.t_b - END_CLEAR_M:
                continue
            if c.section(s, net.sec_list).cls not in RULE_CLASSES or c.bridge[c.idx(s)]:
                continue
            res.append((c, float(s), 1 if r1[0] else -1))
    return res


def _place(pl, c, s, dn, code, src, codes, rep):
    """Sign `code` for the traffic travelling dn (+1 along s) at station s, on its right, facing it."""
    tang, _ = c.line.frame(s)
    side = "R" if dn > 0 else "L"
    kind, _h, w, ext = FU.side_surface_offset(c, side, s)
    off = float(c.hw_at(s)) + (S.KERB_TOP_W + S.SIGN_LATERAL if kind != RURAL else ext + 0.5)
    p = c.line.offset_point(s, -dn * off)
    if pl.near("sign", p, 1.5):
        rep["skipped_near_sign"] = rep.get("skipped_near_sign", 0) + 1
        return None
    for cd in FU.sign_assembly(pl, p, -tang * dn, code if isinstance(code, list) else [code], src, sidewalk=w > 0.5):
        codes.add(cd)
        rep["placed"][cd] = rep["placed"].get(cd, 0) + 1
    pl.pts.setdefault("sign", []).append((p[0], p[1]))
    return p


def rule_signs(pl, net, src, origin, juncs, report, codes):
    """D-42 / D-43 by rule + the advance A-7 + T-1 / "Stop" plates (pkt 2.2.8, 3.2.21). report["built_up"]."""
    rep = {"placed": {}, "boundaries": [], "osm_boundary_nodes": 0, "advance": [], "advance_dropped": []}
    a = area_for(net, src, origin)
    osm_pts = []
    from .signs_route import parse_traffic_sign            # local: signs_route imports this module
    for nd in (src.get("osm") or {}).get("nodes", []):
        ts = str(nd["tags"].get("traffic_sign", "")).strip()
        # city_name (E-17a, the place-name board) stands at the boundary too: no rule pair next to it
        if ts == "city_name" or any(c in OSM_BOUNDARY for c in parse_traffic_sign(ts, nd["tags"])):
            osm_pts.append(np.asarray(nd["geometry"]["coordinates"], float) - origin)
    rep["osm_boundary_nodes"] = len(osm_pts)
    for c, s, dn_in in boundaries(net, a):
        p0 = c.line.point(s)
        if any(np.hypot(*(p0 - q)) < OSM_WINS_M for q in osm_pts):
            continue
        sgn = np.sign(c.dirn[c.idx(s)])
        srcid = f"rule:built_up:{c.id}:{s:.0f}"
        placed = []
        if sgn == 0 or sgn == dn_in:
            if _place(pl, c, s, dn_in, "D-42", srcid, codes, rep) is not None:
                placed.append("D-42")
        if sgn == 0 or sgn == -dn_in:
            if _place(pl, c, s, -dn_in, "D-43", srcid, codes, rep) is not None:
                placed.append("D-43")
        rep["boundaries"].append({"chain": str(c.id), "s": round(s, 1), "e": round(float(p0[0]), 1),
                                  "n": round(float(p0[1]), 1), "signs": placed, "basis": "ESTIMATED BDOT10k OT_PTZB_A"})
    advance_signs(pl, net, juncs, a, rep, codes)
    report["built_up"] = rep


def advance_signs(pl, net, juncs, a, rep, codes):
    """pkt 2.2.8 / 3.2.21: on a minor approach signed A-7 / B-20 by furniture.junction_signs (j.minor_signs) with a
    permitted speed above 60 km/h, a second post 150-300 m before the junction: A-7 + T-1 "<d> m" (A-7 approach) or
    A-7 + "Stop <d> m" (B-20 approach). Placed at the first clear station from 150 m; dropped (reported) when the
    approach chain is shorter."""
    lo, hi = SN.A7_ADVANCE_T1_RANGE_M
    for j in juncs:
        for arm_i, code in getattr(j, "minor_signs", ()) or ():
            arm = j.arms[arm_i]
            c = arm.chain
            trim = c.t_a if arm.end == "a" else c.t_b
            d_sign = trim + 3.0                     # station of the junction sign (junction_signs.put)
            ok = False
            for extra in np.arange(lo, hi + 1e-6, 10.0):
                d = d_sign + float(extra)
                if d > arm.L - END_CLEAR_M:
                    break
                s = float(arm.s(d))
                sec = c.section(s, net.sec_list)
                v = legal_speed(sec, kerbed(c, s) or is_built_up(a, c.line.point(s)))
                if v <= FAST_KMH:
                    break
                if c.bridge[c.idx(s)]:
                    continue
                dist = int(round((d - trim) / 10.0)) * 10          # pkt 2.1.3: to the junction, to 10 m
                plate = f"T-1S_{dist}" if code == "B-20" else f"T-1_{dist}"
                dn = -1 if arm.end == "a" else 1                  # inbound travel along s
                p = _place(pl, c, s, dn, ["A-7", plate], f"rule:advance:{j.id}", codes, rep)
                if p is not None:
                    rep["advance"].append({"junction": str(j.id), "code": code, "plate": plate, "d_m": round(d, 1),
                                           "v_kmh": v})
                    ok = True
                    break
            if not ok:
                sec0 = c.section(float(arm.s(min(d_sign + 1.0, arm.L))), net.sec_list)
                s0 = float(arm.s(min(d_sign, arm.L)))
                v0 = legal_speed(sec0, kerbed(c, s0) or is_built_up(a, c.line.point(s0)))
                if v0 > FAST_KMH:
                    rep["advance_dropped"].append({"junction": str(j.id), "code": code, "arm_m": round(float(arm.L), 1),
                                                   "v_kmh": v0, "why": "approach shorter than 150 m or no clear post"})


def a8_distance_m(v_kmh: float) -> float:
    """A-8 before a roundabout (pkt 2.1.2): the lower end of the recommended range, within the allowed one."""
    lo_ok, hi_ok = SN.warning_distance_m(v_kmh)
    lo_rec, _ = SN.warning_recommended_m(v_kmh)
    return float(min(max(lo_rec, lo_ok), hi_ok))


def needs_a8(entry_xy, sec, a, has_e1: bool, kerbed: bool = False) -> tuple[bool, str]:
    """Dz.U. 2026 poz. 132 (pkt 2.2.9): A-8 unless an E-1 stands before the roundabout or the roundabout lies in the
    built-up area and is visible from far enough. No sight-distance data -> visibility is ASSUMED only where the
    approach speed is the built-up default (<= 50 km/h); a faster approach in a built-up area gets the A-8."""
    if has_e1:
        return False, "E-1 before the roundabout"
    bu = kerbed or is_built_up(a, entry_xy)          # a kerbed street counts as built-up (as in runs())
    v = legal_speed(sec, bu)
    if not bu:
        return True, "outside the built-up area"
    if v > SPEED_BUILT_UP:
        return True, f"built-up, approach {v:.0f} km/h > 50 (visibility not verified)"
    return False, "built-up, <= 50 km/h: assumed visible (UNVERIFIED, no sight-distance data)"


__all__ = ["area", "area_for", "is_built_up", "kerbed", "legal_speed", "runs", "boundaries", "rule_signs", "advance_signs",
           "a8_distance_m", "needs_a8"]
