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
# Prawo o ruchu drogowym, t.j. Dz.U. 2024 poz. 1251 (najnowszy t.j. wg ELI 2026-11-16; text.pdf sha256 de6c1f33...fccb),
# art. 20 s. 24-25 (SOURCED): the general limits (passenger car) - the speed the sign rules of Z1 refer to
SPEED_BUILT_UP = 50.0      # art. 20 ust. 1
SPEED_LIVING = 20.0        # art. 20 ust. 2 (strefa zamieszkania)
SPEED_OUTSIDE = 90.0       # art. 20 ust. 3 pkt 1 lit. d (lorries > 3.5 t / combinations 70, pkt 2 lit. b)
SPEED_DUAL = 100.0         # art. 20 ust. 3 pkt 1 lit. c (dual carriageway, >= 2 lanes each way)
SPEED_MOTORWAY = 140.0     # art. 20 ust. 3 pkt 1 lit. a
DUAL_HIGHWAYS = ("motorway", "trunk", "primary", "secondary")   # WORKING_VALUE: oneway + >= 2 lanes = one carriageway
SETTLEMENT_LANDUSE = ("residential", "industrial", "commercial", "retail", "garages")  # OSM landuse = land of a place
OSM_SNAP_M = 15.0          # as signs_route.osm_signs: a mapped sign this near the carriageway belongs to it
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
    """Point test against a mask (low level; the rules use Zone.at, which also applies the run rules and OSM)."""
    return bool(a is not None and not a.is_empty and a.contains(shapely.Point(float(xy[0]), float(xy[1]))))


# --- ADR 0279 "A-7 z T-1 - klasyfikacja zabudowy" (D33): ONE classification of "obszar zabudowany" + permitted speed
# for every rule (D-42 / D-43, A-7 + T-1, A-8). Built-up = between D-42 and D-43 (art. 2 pkt 15 PoRD): OSM boundary
# signs where mapped, else the BDOT10k rule below. A kerb / footway of the GENERATED road is NOT evidence (the kerb
# comes from our own cross-section rules - ADR 0272 - and is drawn on minor roads outside places, too).

def default_speed(sec, built_up: bool) -> float:
    """Statutory permitted speed without a B-33 (Prawo o ruchu drogowym, t.j. Dz.U. 2024 poz. 1251, art. 20; the
    general limit = passenger car, which is what pkt 2.2.8 / 2.1.2 of Z1 mean by "dopuszczalna prędkość" of a road):
    ust. 2 strefa zamieszkania 20 (OSM highway=living_street = D-40); ust. 1 built-up 50; outside, ust. 3 pkt 1:
    lit. a motorway 140, lit. c dual carriageway with >= 2 lanes each way 100, lit. d other roads 90. Expressways
    (lit. b / c: 120 / 100) are not told apart in the graph (no motorroad tag) - they carry an OSM maxspeed anyway."""
    hw = getattr(sec, "highway", "") or ""
    if hw == "living_street":
        return SPEED_LIVING
    if built_up:
        return SPEED_BUILT_UP
    if hw in ("motorway", "motorway_link") or getattr(sec, "cls", "") == "A":
        return SPEED_MOTORWAY
    if getattr(sec, "oneway", False) and int(getattr(sec, "lanes", 1) or 1) >= 2 and hw in DUAL_HIGHWAYS:
        return SPEED_DUAL
    return SPEED_OUTSIDE


def legal_speed(sec, built_up: bool) -> float:
    """Permitted speed of a section: the OSM maxspeed when tagged, else the statutory default (art. 20)."""
    if sec.maxspeed and (getattr(sec, "maxspeed_src", None) or "osm") != "default":
        return float(sec.maxspeed)
    return default_speed(sec, built_up)


def kerbed(c, s):
    """Kerb / footway on either side of the generated cross-section. Informative only (QA) - NOT a built-up test."""
    for side in ("L", "R"):
        if FU.side_surface_offset(c, side, s)[0] != RURAL:
            return True
    return False


def settlement(src, origin, res):
    """Land of a place: every BDOT10k OT_PTZB_A (any RODZAJ) + OSM landuse of SETTLEMENT_LANDUSE, buffered by
    ROADSIDE_M, keeping only the connected parts that contain residential land `res` (an industrial estate on its
    own is no place, pkt 5.2.48.2). Empty geometry when there is no residential land."""
    if res is None or res.is_empty:
        return shapely.Polygon()
    polys = []
    for f in (src.get("bdot10k") or {}).get("OT_PTZB_A", []) or []:
        polys.append(f.get("geometry") or {})
    for a in (src.get("osm") or {}).get("areas", []) or []:
        if (a.get("tags") or {}).get("landuse") in SETTLEMENT_LANDUSE:
            polys.append(a.get("geometry") or {})
    shp = []
    for g in polys:
        try:
            x = shapely.geometry.shape(g)
        except Exception:
            continue
        if not x.is_empty:
            shp.append(shapely.affinity.translate(shapely.make_valid(x), -float(origin[0]), -float(origin[1])))
    allz = shapely.union_all(shp + [res]).buffer(ROADSIDE_M) if shp else res
    parts = [g for g in getattr(allz, "geoms", [allz]) if g.intersects(res)]
    out = shapely.union_all(parts + [res]) if parts else res
    shapely.prepare(out)
    return out


def _osm_landuse_res(src, origin):
    out = []
    for a in (src.get("osm") or {}).get("areas", []) or []:
        if (a.get("tags") or {}).get("landuse") == "residential":
            try:
                x = shapely.geometry.shape(a.get("geometry") or {})
            except Exception:
                continue
            if not x.is_empty:
                out.append(shapely.affinity.translate(shapely.make_valid(x), -float(origin[0]), -float(origin[1])))
    return out


class Zone:
    """Built-up classification of one network (one tile). `at(c, s)` is THE test every sign rule uses; `speed(c, s)`
    the permitted speed there (OSM maxspeed, else art. 20). Runs per chain are cached; `osm` are the mapped boundary
    signs [(xy, dn_in, code)] with dn_in = +1 / -1 (built-up side along the chain's s after snapping) or 0 unknown."""

    def __init__(self, net, res, settle, osm=()):
        self.net, self.res, self.settle, self.osm = net, res, settle, list(osm)
        self._runs = {}
        self.osm_at = {}                         # chain id -> [s] of OSM boundary signs on it

    def runs(self, c):
        k = id(c)
        if k not in self._runs:
            self._runs[k] = runs(c, self.res, self.settle, self._osm_on(c))
        return self._runs[k]

    def _osm_on(self, c):
        if not hasattr(self, "_snap"):
            self._snap = [(FU.nearest_chain(self.net, xy, OSM_SNAP_M), travel, code) for xy, travel, code in self.osm]
        out = []
        for hit, travel, code in self._snap:
            if not hit or hit[1] is not c:
                continue
            _, _, s, lat = hit
            tang, _ = c.line.frame(s)
            dn = 0
            if isinstance(travel, tuple):          # forward / backward of the way = of the chain (as osm_signs)
                travel = tang * (1 if travel[1] == "forward" else -1)
            elif travel is None and abs(lat) > float(c.hw_at(s)) * 0.5:
                travel = tang if lat < 0 else -tang  # beside the road: right-hand traffic on the side it is mapped
            if travel is not None:
                t = 1 if float(np.dot(travel, tang)) >= 0 else -1
                dn = t if code == "D-42" else -t if code == "D-43" else 0   # D-42: the place lies ahead
            out.append((float(s), dn))
        self.osm_at[str(c.id)] = [s for s, _ in out]
        return out

    def at(self, c, s) -> bool:
        for inside, s0, s1 in self.runs(c):
            if s0 - 1e-6 <= s <= s1 + 1e-6:
                return inside
        return False

    def speed(self, c, s) -> float:
        return legal_speed(c.section(float(s), self.net.sec_list), self.at(c, s))

    def classify(self, c, s) -> dict:
        """QA record: built-up flag, permitted speed and where they come from."""
        sec = c.section(float(s), self.net.sec_list)
        bu = self.at(c, s)
        tagged = bool(sec.maxspeed and (getattr(sec, "maxspeed_src", None) or "osm") != "default")
        return {"built_up": bu, "v_kmh": legal_speed(sec, bu), "v_src": "osm maxspeed" if tagged else "art. 20 PoRD",
                "kerbed": kerbed(c, s)}


PLACES_FILE = __import__("pathlib").Path(__file__).with_name("built_up_places.json")


def places(origin, path=None):
    """Whole-city built-up areas (built_up_places.json, local metres): a tile deep inside a city has no D-42 of its
    own - the city's D-42 stand at its entries, outside the tile - so the BDOT rule (forests, rail yards, industrial
    land > 300 m) must not cut it into places. Empty geometry when the file is missing."""
    import json
    f = path or PLACES_FILE
    try:
        doc = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return shapely.Polygon()
    polys = [shapely.Polygon(np.asarray(pl["polygon"], float) - np.asarray(origin, float)[:2])
             for pl in doc.get("places", []) if len(pl.get("polygon", [])) >= 4]
    return shapely.union_all([shapely.make_valid(p) for p in polys]) if polys else shapely.Polygon()


def zone_for(net, src, origin):
    """The Zone of a network, cached on the network object (one tile = one network)."""
    z = getattr(net, "_built_up_zone", None)
    if z is None:
        res = area_for(net, src, origin)
        osm_res = _osm_landuse_res(src, origin)
        city = places(origin)
        if osm_res or not city.is_empty:
            res = shapely.union_all([res, city] + [g.buffer(ROADSIDE_M) for g in osm_res])
            shapely.prepare(res)
        z = Zone(net, res, settlement(src, origin, res), osm_boundary_signs(src, origin))
        try:
            net._built_up_zone = z
        except Exception:
            pass
    return z


def osm_boundary_signs(src, origin):
    """OSM nodes at a built-up boundary: [(xy, travel or None, code)], code D-42 / D-43 / E-17a (city_name)."""
    from .signs_route import parse_traffic_sign, _bearing_dir     # local: signs_route imports this module
    out = []
    for nd in (src.get("osm") or {}).get("nodes", []) or []:
        t = nd.get("tags") or {}
        ts = str(t.get("traffic_sign", "")).strip()
        codes = [c for c in parse_traffic_sign(ts, t) if c in OSM_BOUNDARY] if ts else []
        if ts == "city_name":
            codes = ["E-17a"]
        if not codes:
            continue
        xy = np.asarray(nd["geometry"]["coordinates"], float)[:2] - np.asarray(origin, float)[:2]
        d = t.get("traffic_sign:direction") or t.get("direction")
        travel = None
        if d in ("forward", "backward"):
            travel = ("way", d)
        elif d is not None:
            try:
                travel = _bearing_dir(float(d))
            except ValueError:
                travel = None
        code = codes[0]
        out.append((xy, travel, code))
    return out


def runs(c, res, settle=None, osm=()):
    """[(inside, s0, s1)] along chain c: obszar zabudowany by the BDOT10k rule (pkt 5.2.48.1-2) corrected by the OSM
    boundary signs on the chain.

    1. a station is in a place when it lies in `settle` (all built-up land of a place, see settlement());
    2. where a place ends inside the chain, the boundary is pulled back to the last residential station (`res`):
       "not commercial / industrial outskirts" (pkt 5.2.48.2); a run with no residential station that does not
       reach both chain ends is not a place;
    3. a gap < 300 m between places is built-up (no sign pair, pkt 5.2.48.1); an isolated run < MIN_INSIDE_M is not;
    4. an OSM D-42 / D-43 / city_limit (osm = [(s, dn_in)]) moves the nearest rule boundary within OSM_WINS_M to it,
       or - with a known direction - splits the run there (the side dn_in built-up).
    The generated kerb is NOT used (ADR 0279 D33)."""
    L = float(c.length)
    if L < 2 * STEP_M:
        return [(False, 0.0, L)]
    if settle is None:
        settle = res
    ss = np.arange(0.0, L + 1e-6, STEP_M)
    P = c.line.point(ss)
    inside = np.asarray(shapely.contains_xy(settle, P[:, 0], P[:, 1]), bool) if not settle.is_empty \
        else np.zeros(len(ss), bool)
    resid = np.asarray(shapely.contains_xy(res, P[:, 0], P[:, 1]), bool) if not res.is_empty \
        else np.zeros(len(ss), bool)
    inside = inside | resid
    # 2. pull interior ends back to the residential land
    k0 = 0
    n = len(ss)
    while k0 < n:
        k1 = k0
        while k1 + 1 < n and inside[k1 + 1] == inside[k0]:
            k1 += 1
        if inside[k0]:
            rk = np.nonzero(resid[k0:k1 + 1])[0]
            left_open, right_open = k0 > 0, k1 < n - 1
            if len(rk) == 0:
                if left_open or right_open:
                    inside[k0:k1 + 1] = False
            else:
                if left_open:
                    inside[k0:k0 + rk[0]] = False
                if right_open:
                    inside[k0 + rk[-1] + 1:k1 + 1] = False
        k0 = k1 + 1
    out = []
    k0 = 0
    for k in range(1, n + 1):
        if k == n or inside[k] != inside[k0]:
            out.append([bool(inside[k0]), float(ss[k0]), float(ss[k - 1])])
            k0 = k
    for i in range(1, len(out)):                           # boundaries sit between the samples
        m = (out[i - 1][2] + out[i][1]) / 2
        out[i - 1][2] = out[i][1] = m
    out[0][1], out[-1][2] = 0.0, L
    out = _merge_short(out)
    for s_b, dn in sorted(osm):
        out = _apply_osm(out, s_b, dn)
    return [tuple(r) for r in out]


def _merge(out):
    merged = [out[0]]
    for r in out[1:]:
        if r[0] == merged[-1][0]:
            merged[-1][2] = r[2]
        else:
            merged.append(r)
    return merged


def _merge_short(out):
    changed = True
    while changed and len(out) > 1:
        changed = False
        for i, r in enumerate(out):
            ln = r[2] - r[1]
            if not r[0] and ln < MIN_OUTSIDE_M and 0 < i < len(out) - 1:   # pkt 5.2.48.1: < 300 m -> no pair
                r[0], changed = True, True
            elif r[0] and 0 < i < len(out) - 1 and ln < MIN_INSIDE_M:    # isolated houses
                r[0], changed = False, True
        out = _merge(out)
    return out


def _apply_osm(out, s_b, dn):
    """Mapped boundary sign at s_b (dn = built-up side along s, 0 unknown) - OSM wins over the rule."""
    bnd = [(abs(out[i][2] - s_b), i) for i in range(len(out) - 1)]
    near = min(bnd) if bnd else None
    if near is not None and near[0] <= OSM_WINS_M:
        i = near[1]
        out[i][2] = out[i + 1][1] = s_b
        if dn:
            out[i][0], out[i + 1][0] = dn < 0, dn > 0
        out = [r for r in out if r[2] - r[1] > 1e-6]
        return _merge(out)
    if not dn:
        return out
    for i, r in enumerate(out):
        if r[1] <= s_b <= r[2]:
            a, b = [dn < 0, r[1], s_b], [dn > 0, s_b, r[2]]
            out = out[:i] + [x for x in (a, b) if x[2] - x[1] > 1e-6] + out[i + 1:]
            break
    return _merge(out)


def boundaries(net, zone):
    """Rule boundaries: [(chain, s, dn_in)] - dn_in = +1 when the built-up side lies at larger s. Boundaries that sit
    on a mapped OSM sign are left out (osm_signs builds those)."""
    res = []
    if zone is None:
        return res
    if not isinstance(zone, Zone):                       # a bare mask (tests, tools): rule only, no OSM
        zone = Zone(net, zone, zone)
    if zone.res.is_empty and not zone.osm:
        return res
    for c in net.chains:
        if c.meta.get("absorbed") or c.roundabout or c.length < MIN_OUTSIDE_M:
            continue
        rr = zone.runs(c)
        osm_s = zone.osm_at.get(str(c.id), [])
        for r0, r1 in zip(rr, rr[1:]):
            s = r0[2]
            if any(abs(s - q) < 1.0 for q in osm_s):
                continue
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
    road_cls = c.section(float(np.clip(s, 0.5, c.length - 0.5)), net.sec_list).cls
    for cd in FU.sign_assembly(pl, p, -tang * dn, code if isinstance(code, list) else [code], src, sidewalk=w > 0.5, road_cls=road_cls):
        codes.add(cd)
        rep["placed"][cd] = rep["placed"].get(cd, 0) + 1
    pl.pts.setdefault("sign", []).append((p[0], p[1]))
    return p


def rule_signs(pl, net, src, origin, juncs, report, codes):
    """D-42 / D-43 by rule + the advance A-7 + T-1 / "Stop" plates (pkt 2.2.8, 3.2.21). report["built_up"]."""
    rep = {"placed": {}, "boundaries": [], "osm_boundary_nodes": 0, "advance": [], "advance_dropped": [],
           "classification": "ADR 0279 D33: D-42..D-43 (OSM, else BDOT10k rule); kerb not used"}
    zone = zone_for(net, src, origin)
    osm_pts = [xy for xy, _t, _c in zone.osm]
    rep["osm_boundary_nodes"] = len(osm_pts)
    for c, s, dn_in in boundaries(net, zone):
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
    advance_signs(pl, net, juncs, zone, rep, codes)
    report["built_up"] = rep


def advance_signs(pl, net, juncs, zone, rep, codes):
    """pkt 2.2.8 / 3.2.21: on a minor approach signed A-7 / B-20 by furniture.junction_signs (j.minor_signs) with a
    permitted speed above 60 km/h, a second post 150-300 m before the junction: A-7 + T-1 "<d> m" (A-7 approach) or
    A-7 + "Stop <d> m" (B-20 approach). Placed at the first clear station from 150 m; dropped (reported) when the
    approach chain is shorter.

    Which road's speed: the MINOR one (the approach the A-7 stands on). Z1 pkt 2.2.8 (s. 64): "Znak A-7 ... umieszcza
    się na drodze podporządkowanej"; "nie dalej niż 50 m - na drogach o dopuszczalnej prędkości powyżej 60 km/h";
    "Na drogach o dopuszczalnej prędkości powyżej 60 km/h znak A-7 należy poprzedzić ... znakiem A-7 z tabliczką
    T-1"; rys. 2.2.8.2 draws both advance posts on the minor road and none on the major one (A-6 / D-1 only). The
    speed is read at the advance station (built-up from `zone`, never from the kerb)."""
    if not isinstance(zone, Zone):                       # a bare mask (tests, tools)
        zone = Zone(net, zone if zone is not None else shapely.Polygon(), zone if zone is not None else shapely.Polygon())
    lo, hi = SN.A7_ADVANCE_T1_RANGE_M
    for j in juncs:
        for arm_i, code in getattr(j, "minor_signs", ()) or ():
            arm = j.arms[arm_i]
            c = arm.chain
            trim = c.t_a if arm.end == "a" else c.t_b
            d_sign = trim + 3.0                     # station of the junction sign (junction_signs.put)
            ok = False
            why = "approach shorter than 150 m or no clear post"
            for extra in np.arange(lo, hi + 1e-6, 10.0):
                d = d_sign + float(extra)
                if d > arm.L - END_CLEAR_M:
                    break
                s = float(arm.s(d))
                v = zone.speed(c, s)
                if v <= FAST_KMH:
                    why = f"{v:.0f} km/h at {extra:.0f} m (built-up)" if zone.at(c, s) else f"{v:.0f} km/h at {extra:.0f} m"
                    break
                if c.bridge[c.idx(s)]:
                    continue
                dist = int(round((d - trim) / 10.0)) * 10          # pkt 2.1.3: to the junction, to 10 m
                plate = f"T-1S_{dist}" if code == "B-20" else f"T-1_{dist}"
                dn = -1 if arm.end == "a" else 1                  # inbound travel along s
                p = _place(pl, c, s, dn, ["A-7", plate], f"rule:advance:{j.id}", codes, rep)
                if p is not None:
                    rep["advance"].append({"junction": str(j.id), "code": code, "plate": plate, "d_m": round(d, 1),
                                           "v_kmh": v, "chain": str(c.id), "e": round(float(p[0]), 1),
                                           "n": round(float(p[1]), 1), "kerbed": kerbed(c, s)})
                    ok = True
                    break
            if not ok:
                s0 = float(arm.s(min(d_sign, arm.L)))
                v0 = zone.speed(c, s0)
                if v0 > FAST_KMH:
                    rep["advance_dropped"].append({"junction": str(j.id), "code": code, "arm_m": round(float(arm.L), 1),
                                                   "v_kmh": v0, "why": why})


def a8_distance_m(v_kmh: float) -> float:
    """A-8 before a roundabout (pkt 2.1.2): the lower end of the recommended range, within the allowed one."""
    lo_ok, hi_ok = SN.warning_distance_m(v_kmh)
    lo_rec, _ = SN.warning_recommended_m(v_kmh)
    return float(min(max(lo_rec, lo_ok), hi_ok))


def needs_a8(built_up: bool, sec, has_e1: bool) -> tuple[bool, str]:
    """Dz.U. 2026 poz. 132 (pkt 2.2.9): A-8 unless an E-1 stands before the roundabout or the roundabout lies in the
    built-up area and is visible from far enough. No sight-distance data -> visibility is ASSUMED only where the
    approach speed is the built-up default (<= 50 km/h); a faster approach in a built-up area gets the A-8.
    `built_up` = Zone.at of the entry (D-42..D-43; the kerb does not count since ADR 0279 D33)."""
    if has_e1:
        return False, "E-1 before the roundabout"
    v = legal_speed(sec, built_up)
    if not built_up:
        return True, "outside the built-up area"
    if v > SPEED_BUILT_UP:
        return True, f"built-up, approach {v:.0f} km/h > 50 (visibility not verified)"
    return False, "built-up, <= 50 km/h: assumed visible (UNVERIFIED, no sight-distance data)"


__all__ = ["area", "area_for", "settlement", "Zone", "zone_for", "is_built_up", "kerbed", "default_speed", "legal_speed",
           "runs", "boundaries", "rule_signs", "advance_signs", "a8_distance_m", "needs_a8"]
