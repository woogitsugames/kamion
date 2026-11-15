"""ADR 0268 (owner D71 p. 3): signs and markings of the approach to a level crossing, as data of the generator.

Rules (every number names its source; nothing here is read off a map service):

  Dz.U. 2025 poz. 1105 (rozporządzenie MI z 9.07.2025, skrzyżowania linii kolejowych z drogami) § 79:
    pkt 1 lit. a  A-9 "przejazd kolejowy z zaporami" before a crossing with barriers, A-10 "przejazd kolejowy bez
                  zapór" before a crossing without barriers; T-7 under A-10 at dangerous category C / D crossings
                  (angle below 60 deg, ...) - reported (`t7_required`), the plate is not built yet;
    pkt 3         G-1a / G-1b / G-1c posts on the right, G-1d / G-1e / G-1f on the left of the carriageway;
    pkt 4 lit. b  P-4 double continuous line on the approaches and on the crossing; lit. e: P-14 on category A-D;
    pkt 5 lit. a  guide posts U-1a / U-1b on approaches of crossings WITHOUT barriers over 15-20 m of road measured
                  from the outer rails, every 3 m on both sides, the nearest posts 4 m from the outer rails;
          lit. b  outside the barriers where the crossing has barriers (no numbers in the act);
    pkt 6         board "Sygnalizacja automatyczna" under A-9 / A-10 before category B and C crossings.
  Dz.U. 2019 poz. 2310 (t.j. rozporządzenia w sprawie znaków i sygnałów drogowych):
    § 3 ust. 2    a warning sign stands 150-300 m before the danger where the permitted speed exceeds 60 km/h and up
                  to 100 m on other roads;
    § 6 ust. 1-2  A-9 = barriers or half-barriers, A-10 = neither;
    § 78 ust. 2   the three-bar post under A-9 / A-10, the two-bar post at 2/3 and the one-bar post at 1/3 of the
                  distance of the warning sign from the crossing;
    § 78 ust. 3   sign closer than § 3 ust. 2 allows: two-bar post under the sign, one-bar post at 1/2; sign right
                  at the crossing: only the one-bar post, under the sign.
  Dz.U. 2019 poz. 2311 zał. 2 pkt 4.2.5 (as already cited by roads.standards.P14_BEFORE_SIGNAL): P-14 at least 2.0 m
    before a signal beside the carriageway.

Choices inside the sourced ranges and everything the acts do not give are WORKING_VALUE constants below. NOT read
(the PDF of Dz.U. 2019 poz. 2311 cz. 1 is larger than the fetch limit): sizes of G-1 / G-2 / U-1a, mounting heights
of G-1, the conditions for the left-hand posts G-1d-f - UNVERIFIED, see the constants.

Three consumers share one list of crossings (streetscape.rail.Plan.crossings):
  attach()   before the road ribbons are meshed (roads.pipeline side_edit): kerbs / ditches flush over the crossing
             panels (REVIEW s22 0217 visual P0-1) + the stations the markings need (chain.meta["rail_xings"]);
  roads.markings reads chain.meta["rail_xings"]: P-4 on the approaches, P-14 before the devices;
  plan()     the positioned signs / posts (rail.json `approach`), placed by rail_props.place.
"""

from __future__ import annotations

import math

import numpy as np
from shapely.geometry import Point

from . import rail as RL

# ------------------------------------------------------------------------------------------------ constants
SPEED_FAST_KMH = 60.0        # Dz.U. 2019 poz. 2310 § 3 ust. 2: "dopuszczalna prędkość pojazdów przekracza 60 km/h"
SIGN_DIST_FAST_M = 150.0     # § 3 ust. 2: 150-300 m; WORKING_VALUE choice: the lower bound
SIGN_DIST_SLOW_M = 100.0     # § 3 ust. 2: "do 100 m"; WORKING_VALUE choice: the upper bound
SIGN_DIST_MIN_SLOW_M = 60.0  # WORKING_VALUE: below this the three posts would stand < 20 m apart -> § 78 ust. 3
SIGN_NEAR_M = 30.0           # WORKING_VALUE for "w bezpośredniej bliskości przejazdu" (§ 78 ust. 3 zd. 2)
SIGN_END_CLEAR_M = 2.0       # WORKING_VALUE: sign this far inside the end of the road / the tile edge
DEFAULT_SPEED_KMH = 50.0     # road without maxspeed: as roads.markings (`sec.maxspeed or 50`)
U1_FIRST_M = 4.0             # § 79 pkt 5 lit. a: nearest posts 4 m from the outer rails
U1_STEP_M = 3.0              # § 79 pkt 5 lit. a: every 3 m
U1_LAST_M = 19.0             # § 79 pkt 5 lit. a: over 15-20 m of road from the outer rails -> 4, 7, ... 19 m (span 15 m)
U1_BARRIER_GAP_M = 1.0       # WORKING_VALUE: first post this far outside the devices (§ 79 pkt 5 lit. b: no numbers)
U1_LATERAL_M = 0.75          # WORKING_VALUE: post axis behind the carriageway edge (Dz.U. 2019 poz. 2311 zał. 4 not read)
G1_BOTTOM_Z_M = 1.00         # WORKING_VALUE: lower edge of a G-1 plate above the ground (UNVERIFIED)
PLATE_GAP_M = 0.05           # as furniture.sign_assembly
P4_LEN_M = 50.0              # WORKING_VALUE: P-4 on each approach, from the outer rail (§ 79 pkt 4 lit. b: no length)
KERB_CUT_MARGIN_M = 1.0      # WORKING_VALUE: kerb flush this far past the panel footprint, then ramps up
KERB_RAMP_M = 1.0            # as plots.DROP_RAMP_M
WITH_BARRIERS = ("half", "double_half", "full", "gate", "yes", "chain")


def has_barriers(c) -> bool:
    return c.get("barrier") in WITH_BARRIERS


def outer_rail_m(c) -> float:
    """Crossing centre -> outer rail, measured along the road."""
    return (c["half_track"] - RL.PANEL_HALF + RL.GAUGE_DEFAULT_MM / 2000.0) / c["sin"]


def device_line_m(c) -> float:
    """Crossing centre -> the posts of the crossing devices (signal / G-3), along the road."""
    return c["half_track"] / c["sin"] + RL.SIGN_SETBACK


# ------------------------------------------------------------------------------------------------ rule (pure)
def rule(c, speed_kmh, avail_m, left=False, speed_src=None) -> dict:
    """What stands on ONE approach of crossing `c`: distances are metres along the road from the outer rail.
    avail_m: road available upstream of the outer rail (to the end of the road / the tile edge).
    speed_src: where speed_kmh comes from ("osm" tag, "authored_override", ...); "default" = the graph has no maxspeed
    tag (low confidence) - reported so, never as a known limit."""
    v = float(speed_kmh or DEFAULT_SPEED_KMH)
    fast = v > SPEED_FAST_KMH
    code = "A-9" if has_barriers(c) else "A-10"
    top = [code] + (["T-SA"] if c.get("category") in ("B", "C") else [])
    nominal = SIGN_DIST_FAST_M if fast else SIGN_DIST_SLOW_M
    lo = nominal if fast else SIGN_DIST_MIN_SLOW_M
    room = float(avail_m) - SIGN_END_CLEAR_M
    min_room = device_line_m(c) - outer_rail_m(c) + 5.0          # the sign never stands among the crossing devices
    out = {"sign": code, "board": "T-SA" in top, "speed_kmh": v, "speed_src": (speed_src or "maxspeed") if speed_kmh else "default",
           "nominal_m": nominal, "posts": [], "dropped": []}
    g = (lambda k: f"G-1{'def'[k] if left else 'abc'[k]}")        # k: 0 = three bars, 1 = two, 2 = one
    if room >= lo:
        d = min(nominal, room)
        out.update(case="§ 78 ust. 2", dist_m=round(d, 1),
                   basis="Dz.U. 2019 poz. 2310 § 3 ust. 2 + § 78 ust. 2; Dz.U. 2025 poz. 1105 § 79 pkt 1, 3, 6")
        out["posts"] = [(d, top + [g(0)]), (2 * d / 3, [g(1)]), (d / 3, [g(2)])]
    elif room >= max(SIGN_NEAR_M, min_room):
        d = room
        out.update(case="§ 78 ust. 3 zd. 1", dist_m=round(d, 1),
                   basis="Dz.U. 2019 poz. 2310 § 78 ust. 3 (sign closer than § 3 ust. 2): two-bar post under the "
                         "sign, one-bar post at 1/2")
        out["posts"] = [(d, top + [g(1)]), (d / 2, [g(2)])]
    elif room >= min_room:
        d = room
        out.update(case="§ 78 ust. 3 zd. 2", dist_m=round(d, 1),
                   basis="Dz.U. 2019 poz. 2310 § 78 ust. 3 (sign right at the crossing): one-bar post under the sign")
        out["posts"] = [(d, top + [g(2)])]
    else:
        out.update(case="no room", dist_m=None, basis="road shorter than the crossing devices + 5 m")
        out["dropped"].append({"what": code, "why": f"only {round(float(avail_m), 1)} m of road before the crossing"})
    # § 79 pkt 1 lit. a: T-7 under A-10 at dangerous category C / D crossings (angle below 60 deg); not built
    out["t7_required"] = bool(code == "A-10" and c.get("category") in ("C", "D")
                              and c["sin"] < math.sin(math.radians(60.0)))
    # § 79 pkt 5: U-1a guide posts
    if has_barriers(c):
        first = device_line_m(c) - outer_rail_m(c) + U1_BARRIER_GAP_M      # past the barrier and the signal mast
        out["guide_basis"] = "Dz.U. 2025 poz. 1105 § 79 pkt 5 lit. b (outside the barriers; spacing WORKING_VALUE)"
    else:
        first = U1_FIRST_M
        out["guide_basis"] = "Dz.U. 2025 poz. 1105 § 79 pkt 5 lit. a (4 m from the outer rail, every 3 m, 15 m)"
    n = int(round((U1_LAST_M - U1_FIRST_M) / U1_STEP_M)) + 1
    out["guide_m"] = [round(first + k * U1_STEP_M, 2) for k in range(n) if first + k * U1_STEP_M <= float(avail_m)]
    return out


# ------------------------------------------------------------------------------------------------ road paths
class StraightPath:
    """Approach along the straight road direction of the crossing (tests / no road network)."""

    def __init__(self, c, a, speed_kmh=None, avail_m=1e9, oneway=False):
        self.c, self.a = c, a
        self.drive = a * np.asarray(c["rdir"], float)
        self.right = np.array([self.drive[1], -self.drive[0]])
        self.pc = np.asarray(c["p"], float)
        self.speed_kmh, self.avail_m, self.oneway = speed_kmh, float(avail_m), oneway
        self.speed_src = None
        self.marked = True

    def at(self, d_centre, side, off):
        """Point `off` m behind the carriageway edge on `side` (+1 right, -1 left of travel), d_centre m before the
        crossing centre; returns (p, travel direction)."""
        p = self.pc - self.drive * d_centre + self.right * side * (self.c["road_w"] / 2 + off)
        return p, self.drive

    def sign_off(self, d_centre, side):
        return RL.SIGN_LATERAL


class NetPath:
    """Approach along the road network: the chain under the crossing, continued through junctions along the
    straightest arm (deflection <= 40 deg) until `need` metres are collected."""

    MAX_TURN_DEG = 40.0

    def __init__(self, net, c, a, need=SIGN_DIST_FAST_M + 60.0):
        from .furniture import nearest_chain
        self.c, self.a, self.net = c, a, net
        drive = a * np.asarray(c["rdir"], float)
        hit = nearest_chain(net, np.asarray(c["p"], float), maxd=6.0)
        self.legs = []                       # (chain, s at d0, trav (+1: travel towards +s), d0)
        self.avail_m = 0.0
        self.speed_kmh, self.oneway, self.marked = None, False, False
        self.speed_src = None
        if hit is None:
            return
        _, ch, s, _ = hit
        t, _ = ch.line.frame(s)
        trav = 1.0 if float(np.dot(t, drive)) >= 0 else -1.0
        sec = ch.section(s, net.sec_list)
        self.speed_kmh = float(sec.maxspeed) if sec.maxspeed else None
        self.speed_src = getattr(sec, "maxspeed_src", None) if sec.maxspeed else None
        self.oneway = bool(sec.oneway)
        from roads import markings as MK
        self.marked = bool(sec.highway in MK.MARKED) and not MK.unmarked(sec)
        if self.oneway and float(np.mean(ch.dirn)) * trav < 0:
            return                            # nobody approaches against a one-way carriageway
        d0, seen = 0.0, {ch.id}
        while True:
            self.legs.append((ch, s, trav, d0))
            run = (s - ch.t_a) if trav > 0 else (ch.length - ch.t_b - s)
            end_s = 0.0 if trav > 0 else ch.length
            d0 += max(run, 0.0)
            if d0 >= need or ch.closed:
                break
            node = ch.node_a if trav > 0 else ch.node_b
            t_end, _ = ch.line.frame(end_s)
            back = -np.asarray(t_end) * trav                      # direction we keep walking (away from the crossing)
            best = None
            for o in net.chains:
                if o.id in seen or o.meta.get("absorbed") or o.roundabout or len(o.line.p) < 2:
                    continue
                for end, s_o, sgn in (("a", 0.0, 1.0), ("b", o.length, -1.0)):
                    if (o.node_a if end == "a" else o.node_b) != node:
                        continue
                    t_o, _ = o.line.frame(s_o)
                    cosang = float(np.dot(np.asarray(t_o) * sgn, back))
                    if cosang >= math.cos(math.radians(self.MAX_TURN_DEG)) and (best is None or cosang > best[0]):
                        best = (cosang, o, end)
            if best is None:
                break
            _, o, end = best
            gap = (ch.t_a if trav > 0 else ch.t_b) + (o.t_a if end == "a" else o.t_b)     # junction patch
            d0 += gap
            ch, trav = o, (-1.0 if end == "a" else 1.0)           # walking away from the crossing = against travel
            s = o.t_a if end == "a" else o.length - o.t_b
            seen.add(o.id)
        self.avail_m = d0

    def _leg(self, d):
        leg = self.legs[0]
        for L in self.legs:
            if d >= L[3]:
                leg = L
        ch, s0, trav, d0 = leg
        return ch, float(np.clip(s0 - trav * (d - d0), 0.0, ch.length)), trav

    def at(self, d_centre, side, off):
        ch, s, trav = self._leg(d_centre)
        lat = -side * trav * (float(ch.hw_at(s)) + off)           # chain frame: left of +s is positive
        t, _ = ch.line.frame(s)
        return np.asarray(ch.line.offset_point(s, lat), float), np.asarray(t, float) * trav

    def sign_off(self, d_centre, side):
        """Lateral offset of a sign post behind the carriageway edge - the rule of furniture.speed_signs."""
        from roads import standards as S
        from roads.network import RURAL
        from .furniture import side_surface_offset
        ch, s, trav = self._leg(d_centre)
        letter = "R" if side * trav > 0 else "L"
        kind, _h, _w, ext = side_surface_offset(ch, letter, s)
        return (S.KERB_TOP_W + S.SIGN_LATERAL) if kind != RURAL else ext + 0.5

    def on_bridge(self, d_centre):
        ch, s, _ = self._leg(d_centre)
        return bool(ch.bridge[ch.idx(s)])


# ------------------------------------------------------------------------------------------------ markers
def plan(rail_plan, net=None, speed_kmh=None, avail_m=None, devices=None) -> dict:
    """Signs and guide posts of every approach of every crossing of `rail_plan` (streetscape.rail.Plan).
    Returns {"markers": [...], "rules": [...], "outside_tile": [...]}; marker kinds:
      approach    one post with plates (top first), `plates`, `bottom_z_m` (lower edge of the lowest plate);
      guide_post  U-1a guide post, `style` (override `guide_post`, default "u1a").
    heading_deg = compass direction the face looks to (towards the oncoming driver)."""
    markers, rules, outside = [], [], []
    tile = rail_plan.tile_local
    road = rail_plan.road_poly
    devs = devices if devices is not None else rail_plan.report.get("markers", [])

    def keep(m, lst=markers):
        if tile is not None and not tile.contains(Point(m["e"], m["n"])):
            outside.append(m)
            return False
        lst.append(m)
        return True

    for ci, c in enumerate(rail_plan.crossings):
        rail_d = outer_rail_m(c)
        style = c.get("guide_post") or "u1a"
        for a in (1, -1):
            path = NetPath(net, c, a) if net is not None else StraightPath(c, a, speed_kmh, avail_m or 1e9)
            if net is not None and not path.legs:
                rules.append({"crossing": ci, "approach": a, "case": "no approach (one-way against, or no chain)"})
                continue
            avail = path.avail_m - rail_d
            if tile is not None:                                   # the tile edge ends the approach
                d = 0.0
                while d < min(avail, SIGN_DIST_FAST_M + 20.0):
                    p, _ = path.at(rail_d + d + 1.0, 1, 0.0)
                    if not tile.contains(Point(p)):
                        break
                    d += 1.0
                avail = min(avail, d)
            left = bool(path.oneway)
            # permitted speed where the warning sign stands: authored fact of the crossing > graph (tag or default)
            v, v_src = path.speed_kmh, getattr(path, "speed_src", None)
            if c.get("approach_speed_kmh"):
                v, v_src = float(c["approach_speed_kmh"]), "authored_override"
            r = rule(c, v, avail, left=False, speed_src=v_src)
            r.update(crossing=ci, approach=a, avail_m=round(avail, 1), marked=bool(path.marked),
                     left_posts=left, left_posts_basis="G-1d-f only on one-way carriageways: WORKING_VALUE, the "
                     "condition in Dz.U. 2019 poz. 2311 zał. 1 was not read (UNVERIFIED)")
            sides = [(1, r["posts"])] + ([(-1, rule(c, v, avail, left=True)["posts"])] if left else [])
            for side, posts in sides:
                for d, plates in posts:
                    if side < 0:
                        plates = [q for q in plates if q.startswith("G-1")]      # the warning sign stands on the right
                    dc = rail_d + d
                    p, drive = path.at(dc, side, path.sign_off(dc, side))
                    if getattr(path, "on_bridge", lambda _d: False)(dc):
                        r["dropped"].append({"what": plates, "why": "on a bridge"})
                        continue
                    m = {"crossing": ci, "kind": "approach", "approach": a, "side": "right" if side > 0 else "left",
                         "e": round(float(p[0]), 2), "n": round(float(p[1]), 2), "heading_deg": RL._heading(-drive),
                         "dist_m": round(d, 1), "plates": plates,
                         "bottom_z_m": G1_BOTTOM_Z_M if plates[-1].startswith("G-1") else None}
                    if not keep(m):
                        r["dropped"].append({"what": plates, "why": "outside the tile"})
            for d in r.pop("guide_m"):
                dc = rail_d + d
                for side in (1, -1):
                    p, drive = path.at(dc, side, U1_LATERAL_M)
                    q = Point(p)
                    # never on another carriageway (side road at the crossing) and never on a crossing device
                    if road is not None and not road.is_empty and road.buffer(-0.05).contains(q):
                        continue
                    if any(math.hypot(mm["e"] - p[0], mm["n"] - p[1]) < 1.0 for mm in devs):
                        continue
                    keep({"crossing": ci, "kind": "guide_post", "approach": a, "side": "right" if side > 0 else "left",
                          "e": round(float(p[0]), 2), "n": round(float(p[1]), 2), "heading_deg": RL._heading(-drive),
                          "dist_m": d, "style": style})
            r["posts"] = [{"dist_m": round(d, 1), "plates": pl} for d, pl in r["posts"]]
            rules.append(r)
    return {"markers": markers, "rules": rules, "outside_tile": outside}


# ------------------------------------------------------------------------------------------------ road stage
def attach(net, rail_plan) -> dict:
    """Before the ribbons are meshed: (1) kerbs / ditches of the road flush over the crossing panels (+ margin): the
    kerb of DW671 ran through the panels and over the rails (REVIEW s22 0217 visual P0-1); (2) the stations of the
    crossing on its chain for roads.markings (chain.meta["rail_xings"]). Returns a report."""
    from roads import network as NW
    from .furniture import nearest_chain
    from .plots import DITCH_FILL_M
    rep = {"crossings": 0, "kerb_cut_m": 0.0, "missed": []}
    for ci, c in enumerate(rail_plan.crossings):
        hit = nearest_chain(net, np.asarray(c["p"], float), maxd=6.0)
        if hit is None:
            rep["missed"].append(ci)
            continue
        _, ch, s_c, _ = hit
        cot = math.sqrt(max(0.0, 1.0 - c["sin"] ** 2)) / c["sin"]
        pm = float(c.get("panel_margin_m", RL.PANEL_MARGIN))
        half = c["half_track"] / c["sin"] + (c["road_w"] / 2 + pm) * cot + KERB_CUT_MARGIN_M
        s = np.asarray(ch.line.s)
        k = np.clip((np.abs(s - s_c) - half) / KERB_RAMP_M, 0.0, 1.0)             # 0 over the panels, 1 outside
        sel = k < 1.0
        for side in "LR":
            d = ch.side[side]
            kind = np.asarray(d["kind"])
            h = np.asarray(d["h"], float)
            urban = sel & (kind == NW.URBAN) & (np.asarray(d["mat"]) != NW.MAT_FLUSH_ROAD) & (h > 0.0)
            h[urban] = h[urban] * k[urban]
            rural = sel & (kind == NW.RURAL)
            he = np.where((h > 0.05) & (h < 1.5), h, DITCH_FILL_M)
            h[rural] = np.minimum(he[rural], DITCH_FILL_M + (he[rural] - DITCH_FILL_M) * k[rural])
            d["h"] = h
            if urban.any():
                rep["kerb_cut_m"] += float(np.ptp(s[urban]))
        ch.meta.setdefault("rail_xings", []).append({
            "ci": ci, "s": float(s_c), "rail_d": outer_rail_m(c), "device_d": device_line_m(c),
            "category": c.get("category"), "src": c["src"]})
        rep["crossings"] += 1
    rep["kerb_cut_m"] = round(rep["kerb_cut_m"], 1)
    return rep
