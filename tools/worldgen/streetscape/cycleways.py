"""Cycle tracks (droga dla rowerów, DDR) as their own surface (ADR 0188).

Source: OSM (© OpenStreetMap contributors, ODbL 1.0), written once per region to
Data/Regions/<id>/generated/osm_cycleways.json (small, committed) so the generator runs without the raw extract:

  highway=cycleway                                   -> DDR
  highway=path|footway|pedestrian + bicycle=designated + segregated=yes
                                                     -> DDR + footway side by side (C-13/C-16 with the vertical bar)
  ... + segregated=no / missing                      -> shared path: NOT built here (BDOT10k OT_SKRP_L keeps it, paved.py)
  surface / cycleway:surface / footway:surface, colour / surface:colour, width / cycleway:width, oneway(:bicycle)

What is built (set-back tracks; a track glued to the kerb stays the road's own 2 m sidewalk, see "open" in the ADR):
  * the DDR strip: `cycle_asphalt_red` (asphalt / paved / untagged), `cycle_red` (red paving blocks) or `path_asphalt`
    (a `colour` tag that says grey / black); unpaved surfaces are not built
  * the footway strip of a segregated path (`sidewalk_paving`, or `path_asphalt` when footway:surface says asphalt)
  * a flush concrete edging between the two (obrzeże 8 cm, 1 cm proud) and the raised edging on the outer edges (paved.py)
  * paint on the DDR: centre line on two-way tracks, the edge line beside the footway, P-23 after carriageway crossings
  * kerb drops where a track crosses a kerbed carriageway (plots.apply_drops), red surfacing + P-11 at crossing nodes
    (roads.markings reads `net.cycle_items`)

Widths are not in OSM for either region (no `width` on any cycle way): BDOT10k OT_SKRP_L SZEROKOSC of the line that runs
along the way, else the defaults below. Which half of a segregated path is the DDR is not in OSM either: road side by
default (WORKING_VALUE), `kind: cycleway` in overrides.yaml where a photo shows otherwise:

  - id: ...            kind: cycleway      target: {osm_way: [212811563]}
    cycle_side: left | right (of the OSM way direction) | road | away      total_w_m, cycle_w_m      colour: red | grey
    p23: false         centre_line: false      build: false        source / note (evidence)
"""

from __future__ import annotations

import json
import math
import zlib
from pathlib import Path

import numpy as np
import shapely
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon

from roads import standards as S

SCHEMA = "truck-sim-pl/osm-cycleways/1"
REPO = Path(__file__).resolve().parents[3]
KEEP = ("highway", "bicycle", "foot", "segregated", "surface", "cycleway:surface", "footway:surface", "colour",
        "surface:colour", "cycleway:surface:colour", "oneway", "oneway:bicycle", "width", "cycleway:width",
        "footway:width", "footway", "cycleway", "path", "crossing", "crossing:markings", "bridge", "tunnel", "layer")
PATHS = ("path", "footway", "pedestrian")
UNPAVED = {"dirt", "ground", "gravel", "compacted", "sand", "unpaved", "fine_gravel", "grass", "earth", "mud", "woodchips"}
BLOCKS = {"paving_stones", "sett", "bricks", "paving_stones:30", "unhewn_cobblestone", "cobblestone"}
GREY = {"grey", "gray", "black", "dark", "#000000", "#808080"}

MAT_RED = "cycle_asphalt_red"
MAT_CROSSING = "cycle_crossing_red"
# Widths (m). No Polish source read for these in this task -> WORKING_VALUE (the usual design values: two-way track
# 2.0 m, one-way 1.5 m, footway 2.0 m = standards.SIDEWALK_W); a region's BDOT10k SZEROKOSC wins where it exists.
DDR_W_TWO_WAY, DDR_W_ONE_WAY = 2.0, 1.5
DDR_W_MIN, DDR_W_MAX = 1.5, 3.5
SEG_TOTAL_DEFAULT, SEG_TOTAL_MIN = 4.0, 3.5
SEG_CYCLE_MIN, SEG_CYCLE_MAX, SEG_FOOT_MIN = 1.5, 3.0, 1.5
BDOT_ALONG_M = 3.0          # a BDOT path line within this distance of the OSM way describes the same path
BDOT_REPLACED_FRAC = 0.6    # ... and is replaced by the OSM-built strips when this much of it runs along cycle ways
DIVIDER_W, DIVIDER_LIFT = S.EDGING_W, 0.01
# Paint. P-23 "rower" [ZNAKI-Z2] rys. 5.2.9.1 (Dz.U. 2019 poz. 2311 str. 596; read in research M52, branch
# research/mistral-p2-surfaces-2): length 2.00 m / height 1.10 m / line 0.10 m, small variant 1.30 / 0.715 / 0.065 m.
# The long axis lies along the direction of travel. The pictogram itself is drawn by eye from the same figure
# (two wheels, diamond frame, handlebar, saddle): WORKING_VALUE shape inside SOURCED outer dimensions.
P23 = {"len": 2.00, "h": 1.10, "line": 0.10}
P23_SMALL = {"len": 1.30, "h": 0.715, "line": 0.065}
P23_AFTER_CROSSING_M = 3.0  # WORKING_VALUE: tail of the symbol this far behind the carriageway edge
LINE_W = S.LINE_W_NARROW    # 0.12 m
# centre line of a two-way track: dash 1 m, gap 3 m - read off owner photo P11-001 (Kuronia, dash : gap about 1 : 3
# in the receding perspective). WORKING_VALUE.
CENTRE_DASH = (1.0, 3.0)
EDGE_INSET = 0.10           # edge line beside the footway: inner edge this far from the edging (photo P11-001)


def is_cycle(t: dict) -> bool:
    hw = t.get("highway")
    return hw == "cycleway" or (hw in PATHS and t.get("bicycle") == "designated")


# --------------------------------------------------------------------------------------------- extract
def extract(region: dict, pbf: Path | None = None) -> dict:
    import osmium
    from pyproj import Transformer
    if pbf is None:
        import sys
        sys.path.insert(0, str(REPO / "tools" / "worldgen"))
        from fetch_osm import download
        pbf = download()
    b = region["bbox"]
    bbox = (b["xmin"], b["ymin"], b["xmax"], b["ymax"])
    tr = Transformer.from_crs("EPSG:4326", "EPSG:2180", always_xy=True)
    inv = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)
    lo = inv.transform(bbox[0] - 50, bbox[1] - 50)
    hi = inv.transform(bbox[2] + 50, bbox[3] + 50)
    tile = shapely.box(*bbox)
    ways = []
    fp = osmium.FileProcessor(str(pbf)).with_locations().with_filter(osmium.filter.KeyFilter("highway"))
    for obj in fp:
        if not obj.is_way():
            continue
        t = {x.k: x.v for x in obj.tags}
        if not is_cycle(t):
            continue
        try:
            pts = [(n.location.lon, n.location.lat) for n in obj.nodes]
        except osmium.InvalidLocationError:
            continue
        if len(pts) < 2 or not any(lo[0] <= x <= hi[0] and lo[1] <= y <= hi[1] for x, y in pts):
            continue
        g = shapely.transform(LineString(pts), lambda xy: np.column_stack(tr.transform(xy[:, 0], xy[:, 1])))
        g = g.intersection(tile)
        for k, part in enumerate(getattr(g, "geoms", [g])):
            if part.geom_type != "LineString" or part.length < 1.0:
                continue
            ways.append({"osm_way": obj.id, "part": k, "tags": {key: t[key] for key in KEEP if key in t},
                         "geometry": [[round(x, 2), round(y, 2)] for x, y in part.simplify(0.1).coords]})
    ways.sort(key=lambda d: (d["osm_way"], d["part"]))
    return {"schema": SCHEMA, "crs": "EPSG:2180", "bbox": list(bbox), "ways": ways,
            "license": "ODbL 1.0, © OpenStreetMap contributors"}


def path_of(region_id: str) -> Path:
    return REPO / "Data" / "Regions" / region_id / "generated" / "osm_cycleways.json"


def write(region_id: str, data: dict) -> Path:
    p = path_of(region_id)
    p.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
                 encoding="utf-8", newline="\n")
    return p


def load(region_id: str) -> dict | None:
    p = path_of(region_id)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


# --------------------------------------------------------------------------------------------- classify
def _surface_mat(surface, colour, cycle: bool):
    """Material of a strip, or None when it is not a built surface (forest track)."""
    if surface in UNPAVED:
        return None
    if surface in BLOCKS:
        return "cycle_red" if cycle else "sidewalk_paving"
    if not cycle:
        return "path_asphalt" if surface in ("asphalt", "concrete") else "sidewalk_paving"
    if colour and colour.lower() in GREY:
        return "path_asphalt"
    return MAT_RED


def classify(t: dict) -> dict | None:
    """{kind: ddr | segregated | shared, mat_cycle, mat_foot, two_way, crossing} or None (not a cycle way)."""
    if not is_cycle(t):
        return None
    hw = t.get("highway")
    seg = t.get("segregated")
    if hw == "cycleway":
        kind = "segregated" if seg == "yes" and t.get("foot") in ("designated", "yes") else "ddr"
    else:
        kind = "segregated" if seg == "yes" else "shared"
    colour = t.get("cycleway:surface:colour") or t.get("surface:colour") or t.get("colour")
    surf = t.get("surface")
    c_surf = t.get("cycleway:surface") or (surf if surf != "paved" else None)
    f_surf = t.get("footway:surface") or (surf if surf not in ("paved", None) and kind != "segregated" else None)
    one = (t.get("oneway:bicycle") or t.get("oneway")) in ("yes", "-1", "1", "true")
    return {"kind": kind, "mat_cycle": _surface_mat(c_surf, colour, True),
            "mat_foot": _surface_mat(f_surf, None, False) if kind == "segregated" else None,
            "two_way": not one,
            "crossing": "crossing" in (t.get("footway"), t.get("cycleway"), t.get("path"))}


def _num(v):
    try:
        return float(str(v).replace(",", ".").split()[0])
    except (TypeError, ValueError, IndexError):
        return None


def widths(cls: dict, tags: dict, bdot_w: float | None, ov: dict | None = None) -> tuple[float, float]:
    """(cycle width, footway width) in metres."""
    ov = ov or {}
    if cls["kind"] == "ddr":
        w = _num(ov.get("cycle_w_m")) or _num(tags.get("cycleway:width")) or _num(tags.get("width")) or bdot_w or \
            (DDR_W_TWO_WAY if cls["two_way"] else DDR_W_ONE_WAY)
        return float(np.clip(w, DDR_W_MIN, DDR_W_MAX)), 0.0
    total = _num(ov.get("total_w_m")) or _num(tags.get("width")) or bdot_w or SEG_TOTAL_DEFAULT
    total = max(float(total), SEG_TOTAL_MIN)
    cw = _num(ov.get("cycle_w_m")) or _num(tags.get("cycleway:width")) or         max(total - S.SIDEWALK_W, DDR_W_TWO_WAY if cls["two_way"] else DDR_W_ONE_WAY)
    cw = float(np.clip(cw, SEG_CYCLE_MIN, min(SEG_CYCLE_MAX, total - SEG_FOOT_MIN)))
    return cw, total - cw


# --------------------------------------------------------------------------------------------- plan
def _offset(line: LineString, d: float):
    """Parallel of `line` at signed distance d (+ = left of the direction); the longest part when it splits."""
    if abs(d) < 1e-6:
        return line
    o = line.offset_curve(d, join_style="mitre", mitre_limit=2.0)
    parts = [g for g in getattr(o, "geoms", [o]) if g.geom_type == "LineString" and g.length > 0.5]
    if not parts:
        return None
    o = max(parts, key=lambda g: g.length)
    a, b = np.asarray(line.coords[0]), np.asarray(o.coords[0])
    c = np.asarray(o.coords[-1])
    return o if np.hypot(*(a - b)) <= np.hypot(*(a - c)) else o.reverse()


def _band(line: LineString, d0: float, d1: float):
    """Strip between the parallels d0 and d1 of `line` (flat ends)."""
    mid = _offset(line, 0.5 * (d0 + d1))
    if mid is None:
        return Polygon()
    return mid.buffer(abs(d1 - d0) / 2, cap_style="flat", join_style="mitre", mitre_limit=2.0)


def _road_side(line: LineString, road_lines, tree) -> float:
    """+1 when the nearest carriageway axis lies left of the way direction, -1 right, 0 when none within 30 m."""
    if tree is None:
        return 0.0
    votes = 0.0
    n = max(2, int(line.length / 10.0))
    for u in np.linspace(0.05, 0.95, n):
        p = line.interpolate(u, normalized=True)
        q = line.interpolate(min(u + 0.02, 1.0), normalized=True)
        t = np.array([q.x - p.x, q.y - p.y])
        if np.hypot(*t) < 1e-6:
            continue
        k = tree.nearest(p)
        g = road_lines[int(k)]
        if g.distance(p) > 30.0:
            continue
        r = g.interpolate(g.project(p))
        v = np.array([r.x - p.x, r.y - p.y])
        if np.hypot(*v) < 0.5:
            continue
        votes += math.copysign(1.0, t[0] * v[1] - t[1] * v[0])
    return 0.0 if votes == 0 else math.copysign(1.0, votes)


def plan(data: dict | None, origin, overrides: list, bdot_skrp: list, road_lines: list, report: dict | None = None):
    """Cycle items of a region, in region-local metres.

    Returns [{id, osm_way, kind, line, total, w_cycle, w_foot, side (+1 = DDR left of the way), d_cycle (signed
    offsets of the DDR strip), d_foot, d_div (offset of the edging between them or None), mat_cycle, mat_foot,
    two_way, p23, centre_line, crossing}]. `bdot_replaced` in the report lists the BDOT10k path ids these replace."""
    report = report if report is not None else {}
    if not data:
        return []
    o = np.asarray(origin, float)
    ovs = {}
    stale = []
    for ov in overrides or []:
        if ov.get("kind") != "cycleway":
            continue
        hit = False
        for wid in (ov.get("target") or {}).get("osm_way", []):
            ovs[int(wid)] = ov
            hit = hit or any(w["osm_way"] == int(wid) for w in data["ways"])
        if not hit:
            stale.append(ov.get("id"))
    blines = []
    for f in bdot_skrp or []:
        if f["props"].get("materialnawierzchni") in (None, "grunt naturalny"):
            continue
        blines.append((f["id"], LineString(np.asarray(f["geometry"]["coordinates"], float) - o),
                       _num(f["props"].get("szerokosc")), f["props"].get("rodzaj"), f["props"].get("materialnawierzchni")))
    btree = shapely.STRtree([b[1] for b in blines]) if blines else None
    rtree = shapely.STRtree(road_lines) if road_lines else None
    items, skipped = [], {"shared": 0, "unpaved": 0, "override": 0}
    for w in data["ways"]:
        cls = classify(w["tags"])
        ov = ovs.get(int(w["osm_way"]))
        if cls is None or len(w["geometry"]) < 2:
            continue
        if ov is not None and ov.get("build") is False:
            skipped["override"] += 1
            continue
        if cls["kind"] == "shared":
            skipped["shared"] += 1
            continue
        if cls["mat_cycle"] is None:
            skipped["unpaved"] += 1
            continue
        if ov is not None and ov.get("colour") in ("red", "grey"):
            cls = dict(cls, mat_cycle=MAT_RED if ov["colour"] == "red" else "path_asphalt")
        line = LineString(np.asarray(w["geometry"], float) - o)
        bw, bmat = None, None
        if btree is not None:
            best = 0.0
            zone = line.buffer(BDOT_ALONG_M)
            for k in btree.query(zone):
                bid, bl, bwid, brodz, bm = blines[int(k)]
                # a lone DDR takes its width only from a BDOT "droga dla rowerów" (an "aleja" beside it is the
                # footway + track together, mapped as two ways in OSM); a segregated path from any path line
                if cls["kind"] == "ddr" and brodz != "droga dla rowerów":
                    continue
                ln = bl.intersection(zone).length
                if bwid and ln > max(best, min(20.0, 0.3 * line.length)):
                    best, bw, bmat = ln, bwid, bm
        if cls["kind"] == "segregated" and "footway:surface" not in w["tags"] and bmat == "masa bitumiczna":
            cls = dict(cls, mat_foot="path_asphalt")       # BDOT10k: the whole path is bituminous
        cw, fw = widths(cls, w["tags"], bw, ov)
        total = cw + fw
        side = 0.0
        if cls["kind"] == "segregated":
            want = (ov or {}).get("cycle_side", "road")
            rs = _road_side(line, road_lines, rtree)
            side = {"left": 1.0, "right": -1.0, "road": rs or 1.0, "away": -(rs or -1.0)}.get(want, rs or 1.0)
        if fw > 0:
            d_cycle = (side * (total / 2 - cw), side * total / 2)
            d_foot = (-side * total / 2, side * (total / 2 - cw))
            d_div = side * (total / 2 - cw)
        else:
            d_cycle, d_foot, d_div = (-cw / 2, cw / 2), None, None
        items.append({"id": f"osm:way/{w['osm_way']}:{w['part']}", "osm_way": int(w["osm_way"]), "kind": cls["kind"],
                      "line": line, "total": total, "w_cycle": cw, "w_foot": fw, "side": side, "d_cycle": d_cycle,
                      "d_foot": d_foot, "d_div": d_div, "mat_cycle": cls["mat_cycle"],
                      "mat_foot": cls["mat_foot"] if fw > 0 else None, "two_way": cls["two_way"],
                      "p23": (ov or {}).get("p23", True) is not False,
                      "centre_line": (ov or {}).get("centre_line", True) is not False,
                      "crossing": cls["crossing"], "bdot_w": bw,
                      "provenance": "authored_override" if ov is not None else "osm"})
    # BDOT10k path lines that run along a built cycle way are the same path: the OSM strips replace them
    replaced = []
    if items and blines:
        zone = shapely.union_all([it["line"].buffer(max(BDOT_ALONG_M, it["total"] / 2 + 1.0)) for it in items])
        shapely.prepare(zone)
        for bid, bl, *_ in blines:
            if bl.length > 0 and bl.intersection(zone).length >= BDOT_REPLACED_FRAC * bl.length:
                replaced.append(bid)
    report.update({"ways": len(data["ways"]), "built": len(items), "skipped": skipped,
                   "planned_m2": round(sum(it["line"].length * it["total"] for it in items)),
                   "by_kind": {k: sum(1 for it in items if it["kind"] == k) for k in ("ddr", "segregated")},
                   "length_m": round(sum(it["line"].length for it in items), 1),
                   "bdot_replaced": sorted(replaced), "overrides_stale": stale,
                   "overrides_applied": sorted({it["osm_way"] for it in items if it["provenance"] == "authored_override"})})
    return items


def candidates(items: list) -> list:
    """(id, polygon, material, source, parking) tuples for paved.collect: the DDR strip first, then the footway."""
    out = []
    for it in items:
        cyc = _band(it["line"], *it["d_cycle"])
        if not cyc.is_empty:
            out.append((it["id"] + ":ddr", cyc, it["mat_cycle"], "osm_cycleway", False))
        if it["d_foot"] is not None:
            foot = _band(it["line"], *it["d_foot"]).difference(cyc)
            if not foot.is_empty:
                out.append((it["id"] + ":foot", foot, it["mat_foot"], "osm_cycleway", False))
    return out


# --------------------------------------------------------------------------------------------- kerb drops
def crossing_drops(net, items: list) -> list:
    """plots.apply_drops entries: both kerbs of every carriageway a cycle way crosses are lowered over its width."""
    from streetscape.plots import DROP_RAMP_M
    if not items:
        return []
    lines = [it["line"] for it in items]
    tree = shapely.STRtree(lines)
    drops = []
    for c in net.chains:
        if c.meta.get("absorbed"):
            continue
        cl = LineString(c.line.p)
        for k in tree.query(cl, predicate="intersects"):
            it = items[int(k)]
            x = cl.intersection(lines[int(k)])
            for g in getattr(x, "geoms", [x]):
                if g.geom_type != "Point":
                    continue
                s, _ = c.line.project(np.array([g.x, g.y]))
                for side in "LR":
                    drops.append({"chain": c.id, "side": side, "s": float(s),
                                  "half": it["total"] / 2 + 0.4 + DROP_RAMP_M, "src": it["id"]})
    return drops


# --------------------------------------------------------------------------------------------- paint
def p23_glyph(small: bool = True):
    """P-23 as a polygon: x = direction of travel (0 .. len), y = left (-h/2 .. h/2). A bicycle seen from the side,
    standing 'up' along the direction of travel and stretched along it: a bicycle is about 1.75 times as long as it
    is high, the symbol is `h` across and `len` along, so heights are stretched by 1.75 * len / h (3.18)."""
    d = P23_SMALL if small else P23
    L, H, lw = d["len"], d["h"], d["line"]
    k = L / (H / 1.75)                            # stretch of the natural height (bicycle length = H)

    def pt(u, v):                                 # natural side view: u along the bicycle (-0.5 .. 0.5), v up
        return (min(v * H * k, L - lw / 2), u * (H - lw))

    r = 0.19                                      # wheel radius / bicycle length
    parts = []
    for u in (-0.5 + r, 0.5 - r):
        cx, cy = r * H * k + lw / 2, u * (H - lw)
        outer = affinity.translate(affinity.scale(Point(0, 0).buffer(1.0, 32), r * H * k + lw / 2, r * (H - lw) + lw / 2,
                                                  origin=(0, 0)), cx, cy)
        parts.append(outer.difference(outer.buffer(-lw)))
    hub_r, hub_f = (r * H * k + lw / 2, (-0.5 + r) * (H - lw)), (r * H * k + lw / 2, (0.5 - r) * (H - lw))
    bb, seat, head = pt(-0.04, 0.17), pt(-0.14, 0.47), pt(0.19, 0.47)
    for a_, b_ in ((hub_r, seat), (hub_r, bb), (bb, seat), (bb, head), (seat, head), (head, hub_f),
                   (pt(-0.22, 0.50), pt(-0.07, 0.50)),            # saddle
                   (head, pt(0.17, 0.55)), (pt(0.10, 0.55), pt(0.27, 0.55))):      # stem, handlebar
        parts.append(LineString([a_, b_]).buffer(lw / 2, cap_style="square"))
    return shapely.union_all(parts).intersection(shapely.box(0, -H / 2, L, H / 2)).buffer(0)


class _PavedTop:
    """z of the built cycle surfaces at plan points (same call shape as roads.through_lines._Top)."""

    def __init__(self, parts, mats):
        from streetscape.furniture import SurfaceTop
        self.t = SurfaceTop([p for p in parts if p.layer == "paved" and p.mat in mats and not p.src.endswith(":edge")],
                            layers=("paved",))

    def z(self, P, zref=None):
        return np.array([self.t.top(float(e), float(n), None) for e, n in np.asarray(P, float).reshape(-1, 2)])


def _ribbon(buf, top, Q, w, src, layer, mat, lift, uv1y=None):
    """Draped ribbon of width w along polyline Q; segments with a vertex off the cycle surface are dropped."""
    if Q is None or len(Q) < 2:
        return 0.0
    d = np.gradient(Q, axis=0)
    d /= np.maximum(np.hypot(d[:, 0], d[:, 1]), 1e-9)[:, None]
    nrm = np.column_stack([-d[:, 1], d[:, 0]])
    A, B = Q - nrm * (w / 2), Q + nrm * (w / 2)
    za, zb = top.z(A), top.z(B)
    ok = np.isfinite(za) & np.isfinite(zb)
    s = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(Q, axis=0).T))])
    V = np.concatenate([np.column_stack([A, np.nan_to_num(za) + lift])[:, None],
                        np.column_stack([B, np.nan_to_num(zb) + lift])[:, None]], axis=1).reshape(-1, 3)
    T, built = [], 0.0
    for i in range(len(Q) - 1):
        if ok[i] and ok[i + 1]:
            T += [(2 * i, 2 * i + 2, 2 * i + 3), (2 * i, 2 * i + 3, 2 * i + 1)]
            built += float(s[i + 1] - s[i])
    if not T:
        return 0.0
    uv = np.column_stack([np.repeat(s, 2), np.tile([0.0, 1.0], len(Q))])
    uv1 = None
    if uv1y is not None:           # paint wear payload as roads.authored_paint (no wheel path, age by hash)
        age = (zlib.crc32(src.encode()) % 1000) / 1000.0 * 0.98
        uv1 = np.column_stack([np.full(len(V), 0.5), np.full(len(V), uv1y + age)])
    buf.add(layer, mat, V, uv, np.array(T), src=src, UV1=uv1)
    return built


def _resample(line: LineString, step=1.0, s0=0.0, s1=None):
    s1 = line.length if s1 is None else s1
    if s1 - s0 < 0.2:
        return None
    u = np.linspace(s0, s1, max(2, int(math.ceil((s1 - s0) / step)) + 1))
    return np.array([line.interpolate(float(x)).coords[0] for x in u])


def paint(buf, items: list, carriage, report: dict):
    """Edging between DDR and footway, centre / edge lines and P-23 on the built cycle surfaces."""
    from roads.authored_paint import _drape_polygon
    mats = {it["mat_cycle"] for it in items} | {it["mat_foot"] for it in items if it["mat_foot"]}
    top = _PavedTop(buf.parts, mats)
    rep = {"divider_m": 0.0, "centre_line_m": 0.0, "edge_line_m": 0.0, "p23": 0, "p23_off_surface": 0}
    for it in items:
        line = it["line"]
        if it["d_div"] is not None:
            dl = _offset(line, it["d_div"])
            if dl is not None:
                rep["divider_m"] += _ribbon(buf, top, _resample(dl), DIVIDER_W, it["id"] + ":divider", "paved",
                                            "curb_concrete", DIVIDER_LIFT)
                el = _offset(line, it["d_div"] + it["side"] * (DIVIDER_W / 2 + EDGE_INSET + LINE_W / 2))
                if el is not None and it["mat_cycle"] != "cycle_red":
                    rep["edge_line_m"] += _ribbon(buf, top, _resample(el), LINE_W, f"DDR-edge@{it['id']}", "markings",
                                                  "marking_white", S.MARKING_LIFT, uv1y=0.2)
        mid = _offset(line, 0.5 * (it["d_cycle"][0] + it["d_cycle"][1]))
        if mid is None:
            continue
        if it["two_way"] and it["centre_line"] and it["w_cycle"] >= 2.0 and it["mat_cycle"] != "cycle_red":
            dash, gap = CENTRE_DASH
            s = gap / 2
            while s + dash <= mid.length:
                rep["centre_line_m"] += _ribbon(buf, top, _resample(mid, 0.5, s, s + dash), LINE_W,
                                                f"DDR-centre@{it['id']}", "markings", "marking_white", S.MARKING_LIFT,
                                                uv1y=0.2)
                s += dash + gap
        if not it["p23"] or carriage is None or carriage.is_empty or it["mat_cycle"] == "cycle_red":
            continue
        # P-23 behind every carriageway the track crosses or ends at, in the lane that leaves the crossing
        lane_w = it["w_cycle"] / 2 if it["two_way"] and it["w_cycle"] >= 2.0 else it["w_cycle"]
        small = lane_w < P23["h"] + 0.3
        g = p23_glyph(small)
        gl = (P23_SMALL if small else P23)["len"]
        if lane_w < (P23_SMALL if small else P23)["h"] + 0.1:
            continue
        for end, sgn in ((0.0, 1.0), (mid.length, -1.0)):
            pt = mid.interpolate(end)
            if carriage.distance(pt) > 1.5 or mid.length < 2 * (P23_AFTER_CROSSING_M + gl) + 2.0:
                continue
            sa = end + sgn * P23_AFTER_CROSSING_M
            a, b = mid.interpolate(sa), mid.interpolate(sa + sgn * gl)
            t = np.array([b.x - a.x, b.y - a.y])
            t /= max(float(np.hypot(*t)), 1e-9)
            nl = np.array([-t[1], t[0]])
            # travel direction t; in a two-way track the lane leaving the crossing is the right half (Polish traffic)
            off = -lane_w / 2 if it["two_way"] and it["w_cycle"] >= 2.0 else 0.0
            ring = shapely.transform(g, lambda xy: np.asarray([a.x, a.y]) + np.outer(xy[:, 0], t) +
                                     np.outer(xy[:, 1] + off, nl))
            n, lost = _drape_polygon(buf, top, ring, f"P-23@{it['id']}", uv1y=0.2)
            rep["p23"] += 1 if n else 0
            rep["p23_off_surface"] += 1 if lost and not n else 0
    report.update({k: (round(v, 1) if isinstance(v, float) else v) for k, v in rep.items()})


def main():
    import argparse
    import yaml
    ap = argparse.ArgumentParser(description="extract generated/osm_cycleways.json for a region")
    ap.add_argument("--region", required=True)
    a = ap.parse_args()
    reg = yaml.safe_load((REPO / "Data" / "Regions" / a.region / "region.yaml").read_text(encoding="utf-8"))
    d = extract(reg)
    p = write(a.region, d)
    kinds = {}
    for w in d["ways"]:
        k = (classify(w["tags"]) or {}).get("kind")
        kinds[k] = kinds.get(k, 0) + 1
    print(p, len(d["ways"]), "ways", kinds)


if __name__ == "__main__":
    main()
