"""Roadside tree rows (szpalery, aleje) laid out along source lines with a rhythm, a legal set-back from the
carriageway edge and sight-triangle cuts at junctions and accesses (ADR 0222, owner D64/D65, research K1).

Opt-in per region: a region uses this rule only when it has authored data - `Data/Regions/<id>/tree_rows.yaml`
(`tree_rows: [...]`, preferred, like lamp_rows.json of ADR 0133) or an entry `kind: tree_rows` in overrides.yaml.
Regions without it (C, Dojlidy, ...) keep the default BDOT10k row rule of vegetation.place (8 m spacing) unchanged.

Sources of the row lines (all region-local E/N after `- origin`):
  BDOT10k OT_OIPR_L rodzaj "rząd drzew"            (streetscape_sources.json, GUGiK)
  OSM natural=tree_row                              (streetscape_sources.json + tree_rows_osm.json, ODbL)
  authored `lines: [{line_epsg2180: [...]}]`        (rows read on the orthophoto but missing from BDOT / OSM)
Only lines within `corridor_m` of a "major" road (`major_highways`) are taken over; the others stay with the default
rule. OSM natural=tree points are single trees and are not touched (single trunks are not obstacles of a sight
field: Dz.U. 2022 poz. 1518 § 82 ust. 4; Dz.U. 2016 poz. 124 zał. 3 ust. 3.2).

Legal values (quoted in docs/adr/0222-szpalery-dk65.md; exact text checked 2026-11-15):
  MIN_TRUNK_EDGE_M  3.0 m  - Dz.U. 2016 poz. 124 (t.j. rozporządzenia MTiGM z 2.03.1999, uchylonego 21.09.2022 przez
                             Dz.U. 2022 poz. 1518) § 53 ust. 3: "Odległość pnia drzewa od krawędzi jezdni nie powinna być
                             mniejsza niż 3,0 m". The 2022 regulation has no number (§ 26: strefa bez przeszkód when
                             the speed limit is > 50 km/h; § 113 ust. 2 pkt 2: vegetation must not intrude into the
                             skrajnia or limit visibility); the trees of the existing DK65 grew under the 1999 rule.
  SIGHT_OBS_M       3.0 m  - same act, zał. 3 ust. 5: observation point >= 3.0 m from the edge of the carriageway
                             with priority, for the start from a stop at a minor approach AND at an access (zjazd).
  SIGHT_L2          table  - zał. 3 ust. 5 (L2 along the road with priority, by speed).
  SIGHT_L1          table  - zał. 3 ust. 4.1 (L1, approach to a junction on the minor road), depth 20 m (minor road
                             GP / G) or 10 m (Z / L / D), outside built-up areas (ust. 4.1 pkt 1).
  The 2022 regulation keeps the requirement itself (§ 81 ust. 1 pkt 2 lit. a-b junction, pkt 6 lit. b zjazd) and
  leaves the values to the guidelines (WR-D); the WR-D junction guideline could not be fetched (gov.pl reset), so
  the 1999 values are used - they are what the existing roadside trees were maintained against.
Everything else (rhythm, mix, missing trees, culvert / level-crossing clearances) is WORKING_VALUE, see ADR 0222.
Deterministic: one numpy Generator per row line, seeded by the line key; every random draw is made for every
candidate before any cut, so an edited cut never shifts the trees elsewhere on the line (as ADR 0173).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import shapely
import yaml
from shapely.geometry import LineString, Point, Polygon

REPO = Path(__file__).resolve().parents[3]
REGIONS = REPO / "Data" / "Regions"

MIN_TRUNK_EDGE_M = 3.0
SIGHT_OBS_M = 3.0
SIGHT_L2 = {30: 40, 40: 60, 50: 70, 60: 90, 70: 100, 80: 120, 90: 160, 100: 180}
SIGHT_L1 = {30: 60, 40: 80, 50: 100, 60: 120, 70: 140, 80: 160, 90: 180, 100: 210}
APPROACH_DEPTH_M = {"major": 20.0, "minor": 10.0}       # zał. 3 ust. 4.1 pkt 1 lit. a (GP, G) / lit. b (Z, L, D)
GP_G = {"motorway", "trunk", "primary"}                 # OSM classes taken as GP / G for the approach depth
# WR-D-22-1 (projekt, wersja do konsultacji 2025-07, tab. 11.4.1) "dopuszczalna na drogach istniejących" LSBP0 [m] by
# speed and SDRR class - reported only (existing rows are reproduced, not cleared out of the zone).
LSBP0_EXISTING = {60: (1.5, 2.0, 2.5, 3.0), 70: (2.0, 3.0, 4.0, 6.0), 90: (3.0, 4.0, 5.0, 7.0), 100: (6.0, 6.0, 7.0, 8.0)}
SDRR_CLASSES = ("<2000", "2000-5000", "5000-10000", ">10000")

DEFAULTS = {
    "major_highways": ["primary", "secondary", "tertiary"],
    "corridor_m": 40.0,            # mean distance of a row line to a major centre line to take it over
    "spacing_m": [12.0, 18.0],     # K1-133: ~15 m (km 14.6); K1-132: 20-25 m (km 11.7) - per-row value in the data
    "missing_share": 0.12,         # gaps of fallen / felled trees, orthophoto T_km11_7 / T_km14_6 (WORKING_VALUE)
    "lateral_sd_m": 0.5,           # trunk scatter across the row line (WORKING_VALUE)
    "species": {"maple": 0.35, "linden": 0.30, "birch": 0.20, "alder": 0.15},   # UNVERIFIED (K1: no source)
    "dominant_share": 0.7,         # one species dominates a row (planted rows), the rest from the mix (WORKING_VALUE)
    "height_m": [11.0, 19.0],      # crowns 6-9 m wide on the orthophoto, WORKING_VALUE
    "min_edge_offset_m": MIN_TRUNK_EDGE_M,
    "sight_obs_m": SIGHT_OBS_M,
    "default_speed_kmh": 90,       # maxspeed missing on a major road outside built-up areas (WORKING_VALUE)
    "track_mouth_m": [3.0, 25.0],  # no tree within 3 m of an OSM track for 25 m from the road (WORKING_VALUE)
    "culvert_clear_m": [5.0, 25.0],   # no tree within 5 m of a culvert line for 25 m from the road (WORKING_VALUE)
    "level_crossing_clear_m": 20.0,   # WORKING_VALUE (§ 81 ust. 1 pkt 9 Dz.U. 2022 poz. 1518; no value there)
    "sdrr_class": "5000-10000",    # UNVERIFIED (GPR not in the repo) - only for the LSBP0 report
    "replace_m": 8.0,              # a BDOT / OSM line with mean distance <= this to an authored line is replaced by it
}


def _seed(key: str) -> int:
    return int(hashlib.sha1(key.encode()).hexdigest()[:8], 16)


def _table(tab: dict, v: float) -> float:
    """Value for the smallest tabulated speed >= v (clamped to the table)."""
    ks = sorted(tab)
    for k in ks:
        if v <= k:
            return float(tab[k])
    return float(tab[ks[-1]])


def lsbp0_existing(v: float, sdrr_class: str) -> float:
    k = 60 if v <= 60 else 70 if v <= 70 else 90 if v <= 90 else 100
    return LSBP0_EXISTING[k][SDRR_CLASSES.index(sdrr_class)]


@dataclass
class Road:
    line: LineString
    half_w: float
    vmax: float
    highway: str
    osm_way: int | None
    eid: str


def roads_from_graph(graph: dict, origin, overrides=(), default_speed=90.0) -> list[Road]:
    """Graph edges in region-local coordinates; width from a way-level override `set: {width}` (as the road
    generator) else the graph attribute, else 6.0 m (WORKING_VALUE)."""
    o = np.asarray(origin, float)[:2]
    wset = {}
    for ov in overrides or ():
        w = (ov.get("set") or {}).get("width")
        ways = (ov.get("target") or {}).get("osm_way")
        if w is not None and ways:
            for wid in ways if isinstance(ways, list) else [ways]:
                wset[int(wid)] = float(w)
    out = []
    for e in graph["edges"]:
        a = e["attrs"]
        g = np.asarray(e["geometry"], float)[:, :2] - o
        if len(g) < 2:
            continue
        w = wset.get(e.get("osm_way")) or (a.get("width") or {}).get("v") or 6.0
        v = (a.get("maxspeed") or {}).get("v")
        try:
            v = float(v)
        except (TypeError, ValueError):
            v = float(default_speed)
        out.append(Road(LineString(g), float(w) / 2.0, v, (a.get("highway") or {}).get("v") or "", e.get("osm_way"), e["id"]))
    return out


def edge_distance(roads: list[Road], P: np.ndarray):
    """(distance of each point to the nearest carriageway edge [m, < 0 = on the carriageway], index of that road)."""
    P = np.asarray(P, float).reshape(-1, 2)
    if not len(P) or not roads:
        return np.full(len(P), np.inf), np.full(len(P), -1)
    pts = shapely.points(P)
    D = np.stack([shapely.distance(r.line, pts) - r.half_w for r in roads], axis=1)
    i = np.argmin(D, axis=1)
    return D[np.arange(len(P)), i], i


def _dir_out(line: LineString, at_start: bool, d=8.0):
    L = line.length
    a = np.array(line.interpolate(0.0 if at_start else L).coords[0])
    b = np.array(line.interpolate(min(d, L) if at_start else max(L - d, 0.0)).coords[0])
    v = b - a
    return a, v / max(np.hypot(*v), 1e-9)


def junctions(graph: dict, roads: list[Road], majors) -> list[dict]:
    """Minor approaches of the major roads: graph nodes of degree >= 3 with a major through pair (the two major
    edges closest to straight); every other edge at the node is a minor approach. kind: 'access' for highway=service
    (zjazd), else 'junction'."""
    by_id = {r.eid: r for r in roads}
    inc = {}
    for e in graph["edges"]:
        if e["id"] not in by_id:
            continue
        inc.setdefault(e["from"], []).append((e["id"], True))
        inc.setdefault(e["to"], []).append((e["id"], False))
    out = []
    for nid, lst in inc.items():
        if len(lst) < 3:
            continue
        dirs = {eid: _dir_out(by_id[eid].line, st) for eid, st in lst}
        maj = [eid for eid, _ in lst if by_id[eid].highway in majors]
        if len(maj) < 2:
            continue
        best = min(((a, b) for i, a in enumerate(maj) for b in maj[i + 1:]),
                   key=lambda ab: float(np.dot(dirs[ab[0]][1], dirs[ab[1]][1])))
        through = shapely.line_merge(shapely.union(by_id[best[0]].line, by_id[best[1]].line))
        if through.geom_type != "LineString":
            through = max(getattr(through, "geoms", [through]), key=lambda g: g.length)
        tr = [by_id[best[0]], by_id[best[1]]]
        for eid, st in lst:
            if eid in best:
                continue
            m = by_id[eid]
            out.append({"node": nid, "p": dirs[eid][0], "through": through,
                        "half_w": max(r.half_w for r in tr), "vmax": max(r.vmax for r in tr),
                        "minor": m.line if st else LineString(m.line.coords[::-1]), "minor_highway": m.highway,
                        "kind": "access" if m.highway == "service" else "junction"})
    return out


def track_accesses(tracks: list[LineString], roads: list[Road], majors, reach=6.0) -> list[dict]:
    """OSM highway=track lines (not in the road graph) whose end lies within half width + `reach` of a major centre
    line: field / forest accesses (zjazdy)."""
    out = []
    mroads = [r for r in roads if r.highway in majors]
    for t in tracks:
        for st in (True, False):
            p, _ = _dir_out(t, st)
            best = min(mroads, key=lambda r: r.line.distance(Point(p)), default=None)
            if best is None or best.line.distance(Point(p)) > best.half_w + reach:
                continue
            minor = t if st else LineString(t.coords[::-1])
            q = np.array(best.line.interpolate(best.line.project(Point(p))).coords[0])
            out.append({"node": None, "p": q, "through": best.line, "half_w": best.half_w, "vmax": best.vmax,
                        "minor": LineString([q] + list(minor.coords)), "minor_highway": "track", "kind": "access"})
    return out


def _point_at_offset(minor: LineString, through: LineString, off: float):
    """First point of the minor centre line at >= `off` from the through centre line (0.5 m steps, <= 80 m), else
    the point at `off` straight along the first segment."""
    for s in np.arange(0.0, min(minor.length, 80.0) + 0.25, 0.5):
        q = minor.interpolate(s)
        if through.distance(q) >= off:
            return np.array(q.coords[0])
    a, v = _dir_out(minor, True, 3.0)
    return a + v * off


def sight_polygons(j: dict, prm: dict) -> list[Polygon]:
    """Sight fields of one minor approach (both directions of the road with priority):
    start from a stop (zał. 3 ust. 5): observer at half_w + sight_obs_m on the minor axis, target L2 along the road on
    the lane of the approaching vehicle (right-hand traffic); approach to a junction (ust. 4.1, kind 'junction' only):
    observer at half_w + 10 / 20 m, target L1. Field = triangle (observer, lane axis at the junction, target)."""
    T = j["through"]
    s0 = T.project(Point(j["p"]))
    hw = j["half_w"]
    cases = [(hw + prm["sight_obs_m"], _table(SIGHT_L2, j["vmax"]))]
    if j["kind"] == "junction":
        depth = APPROACH_DEPTH_M["major" if j["minor_highway"] in GP_G else "minor"]
        cases.append((hw + depth, _table(SIGHT_L1, j["vmax"])))
    polys = []
    for off, L in cases:
        obs = _point_at_offset(j["minor"], T, off)
        for d in (+1, -1):
            s1 = float(np.clip(s0 + d * L, 0.0, T.length))
            if abs(s1 - s0) < 1.0:
                continue
            pts = []
            for s in (s0, s1):
                a = np.array(T.interpolate(max(s - 0.5, 0.0)).coords[0])
                b = np.array(T.interpolate(min(s + 0.5, T.length)).coords[0])
                t = (b - a) / max(np.hypot(*(b - a)), 1e-9)
                n = np.array([-t[1], t[0]])
                pts.append(np.array(T.interpolate(s).coords[0]) + d * n * hw / 2.0)
            poly = Polygon([obs, pts[0], pts[1]])
            if poly.is_valid and poly.area > 0.5:
                polys.append(poly)
    return polys


def layout_line(line: LineString, prm: dict, key: str):
    """Stations along `line` with the row rhythm: start phase U(0, spacing hi), step U(spacing lo, hi), lateral
    N(0, lateral_sd), a share of missing trees; species: a dominant one per row (drawn from the mix) with
    `dominant_share`, else from the mix. Returns (P [k, 2], species [k], keep [k]) - `keep` False = missing tree; all
    draws are made for every station."""
    rng = np.random.default_rng(_seed(key))
    lo, hi = (float(v) for v in prm["spacing_m"])
    names = list(prm["species"])
    w = np.array([prm["species"][k] for k in names], float)
    w /= w.sum()
    dom = names[int(rng.choice(len(names), p=w))]
    L = line.length
    s = float(rng.uniform(0.0, hi))
    P, S, K = [], [], []
    while s < L:
        lat = float(rng.normal(0.0, prm["lateral_sd_m"]))
        miss = float(rng.uniform()) < prm["missing_share"]
        sp = dom if float(rng.uniform()) < prm["dominant_share"] else names[int(rng.choice(len(names), p=w))]
        a = np.array(line.interpolate(max(s - 0.5, 0.0)).coords[0])
        b = np.array(line.interpolate(min(s + 0.5, L)).coords[0])
        t = (b - a) / max(np.hypot(*(b - a)), 1e-9)
        P.append(np.array(line.interpolate(s).coords[0]) + np.array([-t[1], t[0]]) * lat)
        S.append(sp)
        K.append(not miss)
        s += float(rng.uniform(lo, hi))
    return np.array(P, float).reshape(-1, 2), S, np.array(K, bool)


def _push_out(P, roads, dmin):
    """Trunks closer than dmin to a carriageway edge are moved straight away from the nearest road to dmin; a trunk
    that is still too close (between two roads) is dropped. Returns (P, ok, moved)."""
    d, ix = edge_distance(roads, P)
    P = P.copy()
    moved = np.zeros(len(P), bool)
    for k in np.nonzero(d < dmin)[0]:
        r = roads[ix[k]]
        q = np.array(r.line.interpolate(r.line.project(Point(P[k]))).coords[0])
        v = P[k] - q
        nv = np.hypot(*v)
        if nv < 1e-6:
            continue
        P[k] = q + v / nv * (r.half_w + dmin + 0.05)
        moved[k] = True
    d2, _ = edge_distance(roads, P)
    return P, d2 >= dmin - 1e-6, moved


def _clip(out, tile):
    """Lines clipped to the tile (the neighbour tile lays out its own part: no duplicate trunks on a seam)."""
    if tile is None:
        return out
    res = []
    out = [x if len(x) == 4 else (*x, {}) for x in out]
    for key, ln, s, lp in out:
        g = shapely.intersection(ln, tile)
        parts = [x for x in getattr(g, "geoms", [g]) if x.geom_type == "LineString" and x.length >= 1.0]
        res += [(key if len(parts) == 1 else f"{key}#{k}", x, s, lp) for k, x in enumerate(parts)]
    return res


def row_lines(src: dict, origin, osm_probe: dict | None, entry: dict, tile=None) -> list[tuple[str, LineString, str]]:
    """(key, line, source) of every candidate row line: BDOT10k rows, OSM tree_row ways (snapshot + live probe,
    deduplicated by way id), authored lines of the entry; clipped to `tile` (region-local polygon) when given."""
    o = np.asarray(origin, float)[:2]
    out = []
    for f in src.get("bdot10k", {}).get("OT_OIPR_L", []):
        if f["props"].get("rodzaj") == "rząd drzew":
            out.append((f"bdot:{f['id']}", LineString(np.asarray(f["geometry"]["coordinates"], float)[:, :2] - o), "bdot", {}))
    seen = set()
    for w in src.get("osm", {}).get("ways", []):
        if w["tags"].get("natural") == "tree_row" and w["geometry"]["type"] == "LineString":
            seen.add(w["osm_way"])
            out.append((f"osm:way/{w['osm_way']}:{w.get('part', 0)}",
                        LineString(np.asarray(w["geometry"]["coordinates"], float) - o), "osm", {}))
    for w in (osm_probe or {}).get("tree_row", []):
        if w["osm_way"] not in seen:
            out.append((f"osm:way/{w['osm_way']}", LineString(np.asarray(w["line_epsg2180"], float) - o), "osm", {}))
    for k, ln in enumerate(entry.get("lines", [])):
        lp = {q: v for q, v in ln.items() if q in DEFAULTS}       # per-line rhythm / mix read on the orthophoto
        out.append((f"override:{entry['id']}:{k}", LineString(np.asarray(ln["line_epsg2180"], float) - o), "authored", lp))
    return _clip(out, tile)


def plan(lines, roads: list[Road], prm: dict, *, tracks=(), culverts=(), crossings=(), graph=None) -> dict:
    """Lay out the rows. lines: [(key, LineString, source)]. Returns {"rows": [{key, P, species, source}],
    "handled": set(keys taken over), "cuts": [polygons], "report": {...}}."""
    prm = {**DEFAULTS, **prm}
    majors = set(prm["major_highways"])
    mroads = [r for r in roads if r.highway in majors]
    rep = {"lines_total": len(lines), "lines_taken": 0, "length_taken_m": 0.0, "stations": 0, "missing": 0,
           "cut_sight": 0, "cut_track_mouth": 0, "cut_culvert": 0, "cut_level_crossing": 0, "moved_to_min_offset": 0,
           "dropped_too_close": 0, "trees": 0, "in_lsbp0_existing": 0, "junctions": 0, "accesses": 0,
           "sight_fields": 0, "by_source": {}}
    if not mroads:
        return {"rows": [], "handled": set(), "cuts": [], "report": rep}
    J = junctions(graph, roads, majors) if graph is not None else []
    J += track_accesses(list(tracks), roads, majors)
    rep["junctions"] = sum(1 for j in J if j["kind"] == "junction")
    rep["accesses"] = sum(1 for j in J if j["kind"] == "access")
    sight = [p for j in J for p in sight_polygons(j, prm)]
    rep["sight_fields"] = len(sight)
    sight_u = shapely.union_all(sight) if sight else Polygon()
    near_road = shapely.union_all([r.line for r in mroads])
    mouth = shapely.union_all([shapely.intersection(t, near_road.buffer(prm["track_mouth_m"][1])).buffer(prm["track_mouth_m"][0])
                               for t in tracks]) if tracks else Polygon()
    culv = [c for c in culverts if c.distance(near_road) <= 8.0]
    culv_u = shapely.union_all([shapely.intersection(c, near_road.buffer(prm["culvert_clear_m"][1])).buffer(prm["culvert_clear_m"][0])
                                for c in culv]) if culv else Polygon()
    lc = [p for p in crossings if min(r.line.distance(p) for r in roads) <= 15.0]
    lc_u = shapely.union_all([p.buffer(prm["level_crossing_clear_m"]) for p in lc]) if lc else Polygon()
    rows, handled = [], set()
    lines = [x if len(x) == 4 else (*x, {}) for x in lines]
    authored = [x[1] for x in lines if x[2] == "authored"]
    rep["replaced_by_authored"] = 0
    for key, line, source, lprm in lines:
        if line.length < 1.0:
            continue
        if source != "authored" and authored:
            vv = shapely.points(np.asarray(line.coords))
            if min(float(np.mean(shapely.distance(a, vv))) for a in authored) <= prm["replace_m"]:
                handled.add(key.split("#")[0])  # the orthophoto trace replaces this row (ADR 0222)
                rep["replaced_by_authored"] += 1
                continue
        verts = shapely.points(np.asarray(line.coords))
        if float(np.mean(shapely.distance(near_road, verts))) > prm["corridor_m"]:
            continue
        handled.add(key.split("#")[0])
        rep["lines_taken"] += 1
        rep["length_taken_m"] += line.length
        P, S, K = layout_line(line, {**prm, **lprm}, f"treerow:{key}")
        rep["stations"] += len(P)
        rep["missing"] += int((~K).sum())
        if not len(P):
            continue
        P, ok, moved = _push_out(P, roads, float(prm["min_edge_offset_m"]))
        c_s = shapely.contains_xy(sight_u, P[:, 0], P[:, 1]) if not sight_u.is_empty else np.zeros(len(P), bool)
        c_m = shapely.contains_xy(mouth, P[:, 0], P[:, 1]) if not mouth.is_empty else np.zeros(len(P), bool)
        c_c = shapely.contains_xy(culv_u, P[:, 0], P[:, 1]) if not culv_u.is_empty else np.zeros(len(P), bool)
        c_l = shapely.contains_xy(lc_u, P[:, 0], P[:, 1]) if not lc_u.is_empty else np.zeros(len(P), bool)
        live = K & ok
        rep["dropped_too_close"] += int((K & ~ok).sum())
        rep["moved_to_min_offset"] += int((live & moved).sum())
        for name, c in (("cut_sight", c_s), ("cut_track_mouth", c_m), ("cut_culvert", c_c), ("cut_level_crossing", c_l)):
            rep[name] += int((live & c).sum())
            live &= ~c
        d, ix = edge_distance(roads, P)
        lz = np.array([lsbp0_existing(roads[i].vmax, prm["sdrr_class"]) if roads[i].highway in majors else 0.0 for i in ix])
        rep["in_lsbp0_existing"] += int((live & (d < lz)).sum())
        rows.append({"key": key, "source": source, "P": P[live], "species": [s for s, k in zip(S, live) if k]})
        rep["trees"] += int(live.sum())
        rep["by_source"][source] = rep["by_source"].get(source, 0) + int(live.sum())
    rep["length_taken_m"] = round(rep["length_taken_m"], 1)
    return {"rows": rows, "handled": handled, "cuts": sight, "report": rep}


def load_entries(rid: str, overrides=()) -> list[dict]:
    """`kind: tree_rows` entries of the region: Data/Regions/<id>/tree_rows.yaml (`tree_rows: [...]`) + overrides."""
    out = []
    p = REGIONS / rid / "tree_rows.yaml"
    if p.exists():
        d = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        out += [dict(e, kind="tree_rows") for e in d.get("tree_rows", []) or []]
    out += [o for o in overrides or () if o.get("kind") == "tree_rows"]
    return out


def region_plan(rid: str, overrides, src: dict, graph: dict, origin) -> dict | None:
    """Plan of a region, or None when the region did not opt in (no tree_rows entry)."""
    entries = load_entries(rid, overrides)
    if not entries:
        return None
    probe_p = REGIONS / rid / "tree_rows_osm.json"
    probe = json.loads(probe_p.read_text(encoding="utf-8")) if probe_p.exists() else None
    o = np.asarray(origin, float)[:2]
    tracks = [LineString(np.asarray(t["line_epsg2180"], float) - o) for t in (probe or {}).get("track", [])]
    culverts = [LineString(np.asarray(t["line_epsg2180"], float) - o) for t in (probe or {}).get("culvert", [])]
    crossings = [Point(np.asarray(t["xy_epsg2180"], float) - o) for t in (probe or {}).get("level_crossing", [])]
    bb = yaml.safe_load((REGIONS / rid / "region.yaml").read_text(encoding="utf-8"))["bbox"]
    tile = shapely.box(bb["xmin"] - o[0], bb["ymin"] - o[1], bb["xmax"] - o[0], bb["ymax"] - o[1])
    res = {"rows": [], "handled": set(), "cuts": [], "report": {}, "height_m": {}}
    for e in entries:
        prm = {k: v for k, v in e.items() if k in DEFAULTS}
        prm_full = {**DEFAULTS, **prm}
        roads = roads_from_graph(graph, origin, overrides, prm_full["default_speed_kmh"])
        lines = [x for x in row_lines(src, origin, probe, e, tile) if x[0] not in res["handled"]]
        r = plan(lines, roads, prm, tracks=tracks, culverts=culverts, crossings=crossings, graph=graph)
        for row in r["rows"]:
            row["key"] = f"treerow:{row['key']}"
            res["height_m"][row["key"]] = tuple(float(v) for v in prm_full["height_m"])
        res["rows"] += r["rows"]
        res["handled"] |= r["handled"]
        res["cuts"] += r["cuts"]
        res["report"][e["id"]] = r["report"]
    return res
