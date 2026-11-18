"""Horizontal markings as geometry lying MARKING_LIFT above the road surface (decal mesh; the engine
material adds a depth offset). Dimensions and placement rules: standards.py ([ZNAKI-Z2]).

Placed:
  lane lines P-1a/P-1b (P-2a in the last 20 m before a signalised / turn-lane approach),
  centre lines of two-way roads (none if the carriageway is < 5.80 m), edge lines P-7b on GP roads,
  P-14 at signalised approaches, P-13 at roundabout entries and minor approaches to G/GP roads,
  P-10 at OSM crossing nodes (crossing != unmarked/no; inside a junction patch draped on the patch mesh, ADR 0069),
  P-8 arrows from turn:lanes.
"""

from __future__ import annotations

import math
import zlib

import numpy as np
import shapely
from shapely import affinity
from shapely.geometry import Polygon, box

from . import standards as S
from .network import lane_w_of
from .geom import ear_clip, polygon_area
from .meshing import MeshBuf

MARKED = {"motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link", "secondary",
          "secondary_link", "tertiary", "tertiary_link"}
RANK = {"A": 0, "S": 1, "GP": 2, "G": 3, "Z": 4, "L": 5, "D": 6}


# Paint wear data (TEXCOORD_1 of marking_white, Kamion/World PBR _DECAL_PAINT, review r6 W-H6):
#   x = lane coordinate, the same convention as the carriageway ribbon (meshing: |lat| / lane width on two-way roads,
#       from the edge strip on one-way / ring roads), so the wheel paths at ~0.26 / 0.74 of a lane line up with the
#       polished wheel paths of the asphalt beneath;
#   y = traffic exposure + age: [0, 1) longitudinal lines (lane, centre, edge: rarely run over), [2, 3) transverse
#       marks and glyphs (P-8 arrows, P-10, P-13, P-14: every wheel crosses them); fractional part = age 0..1 of
#       that mark (deterministic hash of the mark), which scales dirt and wear.
TRANSVERSE = ("P-8", "P-10", "P-12", "P-13", "P-14")
_SECS = []          # net.sec_list of the network being marked (set by _build_markings)


def _paint_uv1(c, s, lat, kind):
    s = np.asarray(s, float)
    lat = np.asarray(lat, float)
    sm = float(np.mean(s))
    if _SECS:
        sec = c.section(sm, _SECS)
        lw, edge, ring = max(float(sec.lane_w), 2.0), float(sec.edge_strip), bool(sec.oneway or sec.roundabout)
    else:
        lw, edge, ring = 3.5, 0.0, False
    hw = np.asarray(c.hw_at(s), float)
    if _SECS and getattr(sec, "lane_follow", False):
        lw = np.maximum(lane_w_of(sec, hw), 2.0)
    lanec = (lat + hw - edge) / lw if ring else np.abs(lat) / lw
    if _SECS and getattr(sec, "lane_edges", None):
        lanec = sec.lane_coord(lat, hw, int(c.dirn[c.idx(sm)]) or 1)
    key = f"{kind}@{c.id}:{sm:.1f}:{float(np.mean(lat)):.1f}".encode()
    age = (zlib.crc32(key) % 1000) / 1000.0 * 0.98
    y = (2.0 if kind.split("-P-2a")[0] in TRANSVERSE else 0.0) + age
    return np.column_stack([lanec, np.full(len(lanec), y)])


def _surface_pts(c, s, lat):
    p = c.line.offset_point(s, lat)
    z = c.crossfall_z(s, lat) + S.MARKING_LIFT
    return np.column_stack([p, z])


def strip(buf, c, s0, s1, lat, w, kind):
    """Longitudinal stripe from s0 to s1 centred on lateral `lat` (chain frame), width w."""
    if s1 - s0 < 0.05:
        return
    n = max(1, int(math.ceil((s1 - s0) / 2.0)))
    ss = np.linspace(s0, s1, n + 1)
    # lat may follow the carriageway edge (callable of s): edge lines and one-way lane lines keep their distance
    # to the gutter where the width changes inside a section (ADR 0074: P-7b drawn on the kerb of the link)
    la = np.asarray(lat(ss), float) if callable(lat) else np.full(len(ss), float(lat))
    a = _surface_pts(c, ss, la - w / 2)
    b = _surface_pts(c, ss, la + w / 2)
    V = np.concatenate([a[:, None], b[:, None]], axis=1).reshape(-1, 3)
    T = []
    for i in range(n):
        T += [(2 * i, 2 * i + 2, 2 * i + 3), (2 * i, 2 * i + 3, 2 * i + 1)]
    uv = np.column_stack([np.repeat(ss - s0, 2), np.tile([0.0, 1.0], len(ss))])
    sv = np.repeat(ss, 2)
    lv = np.column_stack([la - w / 2, la + w / 2]).ravel()
    buf.add("markings", "marking_white", V, uv, np.array(T), src=f"{kind}@{c.id}", UV1=_paint_uv1(c, sv, lv, kind))


def dashed(buf, c, s0, s1, lat, w, dash, gap, kind):
    s = s0 + gap / 2
    while s < s1:
        strip(buf, c, s, min(s + dash, s1), lat, w, kind)
        s += dash + gap


def polygon_mark(buf, c, poly_xy, origin_s, lat0, fwd, left, kind):
    """2D glyph (x forward, y left, metres) placed at station origin_s / lateral lat0."""
    ring = np.array(poly_xy.exterior.coords)[:-1]
    if polygon_area(ring) < 0:
        ring = ring[::-1]
    tris = ear_clip(ring)
    s = origin_s + fwd * ring[:, 0]
    lat = lat0 + left * ring[:, 1]
    V = _surface_pts(c, s, lat)
    T = np.array(tris)
    # chain frame (s, lat) is right-handed; flips if exactly one of fwd/left is negative
    if fwd * left < 0:
        T = T[:, [0, 2, 1]]
    buf.add("markings", "marking_white", V, ring.copy(), T, src=f"{kind}@{c.id}", UV1=_paint_uv1(c, s, lat, kind))


def arrow_glyph(turns: list, long: bool):
    for t in turns:
        if t in ("guide_left", "guide_right"):
            # P-9 guidance arrow (lane ends, move over): traced at 75 px/m on the 0.08 m orthophoto, Andersa SE-bound
            # before n10015785253 (artifacts/junctions-r4/trace/n100_arrow1.jpg; ADR 0110, REVIEW s10-0100 P1-5).
            # x = lane direction, y = left; origin = middle of the tail edge (which is cut parallel to the lane).
            # WORKING_VALUE (orthophoto read; the dimensions of the regulation drawing are UNVERIFIED).
            sg = 1.0 if t == "guide_left" else -1.0
            pts = [(-0.9, 0.0), (0.65, 1.45), (-0.2, 1.45), (4.2, 2.75), (3.1, 1.4), (2.1, 1.4), (0.9, 0.0)]
            return Polygon([(x, sg * y) for x, y in pts])
    d = S.ARROW_LONG if long else S.ARROW_SHORT
    L, hl, hw, sw = d["len"], d["head_len"], d["head_w"], d["shaft_w"]
    shapes = []
    through = "through" in turns or not turns
    side_turns = [t for t in turns if t in ("left", "right", "slight_left", "slight_right")]
    stem_end = L - hl if through else L * 0.45
    shapes.append(box(0, -sw / 2, stem_end + 0.01, sw / 2))
    if through:
        shapes.append(Polygon([(L - hl, -hw / 2), (L, 0), (L - hl, hw / 2)]))
    for t in side_turns:
        sgn = 1.0 if "left" in t else -1.0
        ang = 45.0 if "slight" in t else 60.0
        x0 = stem_end * 0.75 if through else stem_end
        arm_len = 1.1
        a = box(0, -sw / 2, arm_len, sw / 2)
        a = affinity.rotate(a, sgn * ang, origin=(0, 0))
        a = affinity.translate(a, x0, 0)
        tip = (x0 + arm_len * math.cos(math.radians(ang)), sgn * arm_len * math.sin(math.radians(ang)))
        head = Polygon([(0, -hw / 2), (hl * 0.8, 0), (0, hw / 2)])
        head = affinity.rotate(head, sgn * ang, origin=(0, 0))
        head = affinity.translate(head, *tip)
        shapes += [a, head]
    g = shapely.union_all(shapes).buffer(0)
    if g.geom_type == "MultiPolygon":
        g = max(g.geoms, key=lambda x: x.area)
    return g.simplify(0.005)


def lane_layout(sec, hw, dirn):
    """Return (centre_line_lat or None, [lane boundary lats], lane centres by travel dir)."""
    lw, e = lane_w_of(sec, hw), sec.edge_strip        # ADR 0233: local lane width on `lanes_follow_width` sections
    le = getattr(sec, "lane_edges", None)
    if le and sec.oneway:
        # ADR 0095: measured lane edges, distances from the left edge in the direction of travel
        d = int(dirn) or 1
        bounds = [d * (hw - x) for x in le[1:-1]]
        centres = [d * (hw - 0.5 * (a + b)) for a, b in zip(le, le[1:])]
        return None, bounds, {"fwd": centres, "bwd": []}
    if sec.oneway:
        bounds = [hw - e - k * lw for k in range(1, sec.lanes)]
        centres = [dirn * (hw - e - (i + 0.5) * lw) for i in range(sec.lanes)]
        return None, bounds, {"fwd": centres, "bwd": []}
    lat_c = -hw + e + sec.lanes_fwd * lw
    bounds = [lat_c - k * lw for k in range(1, sec.lanes_fwd)] + [lat_c + k * lw for k in range(1, sec.lanes_bwd)]
    fwd = [lat_c - (i + 0.5) * lw for i in range(sec.lanes_fwd)]
    bwd = [lat_c + (i + 0.5) * lw for i in range(sec.lanes_bwd)]
    return lat_c, bounds, {"fwd": fwd, "bwd": bwd}


def follow_edge(sec, lat, hw_mid, hw_s, dirn):
    """A lane line of a one-way carriageway keeps its distance from the gutter it was laid out from where the
    half-width changes (hw_mid at the layout station, hw_s where it is painted)."""
    sg = (int(dirn) or 1) if getattr(sec, "lane_edges", None) else 1
    return sg * (hw_s - (hw_mid - sg * lat))


def edge_lines(sec, hw, dirn):
    """[(lat, kind)] of the painted edge lines of a section at half-width hw (scalar or array). Default rule:
    P-7b on both sides of class A / S / GP roads with an edge strip. `edge_lines` (override, direction of travel)
    narrows it; a section with measured `lane_edges` paints only what `edge_lines` names (ADR 0095)."""
    if sec.roundabout or unmarked(sec):
        return []
    el = getattr(sec, "edge_lines", None)
    le = getattr(sec, "lane_edges", None)
    d = int(dirn) or 1
    half = S.LINE_W_WIDE / 2
    out = []
    if le and sec.oneway:
        el = el or "none"
        if el in ("left", "both"):
            out.append((d * (hw - (le[0] - half if le[0] >= S.LINE_W_WIDE else le[0] + half)), "P-7b"))
        if el in ("right", "both"):       # on the right edge strip where there is one, else just inside the edge
            strip_r = float(sec.width) - le[-1] >= S.LINE_W_WIDE
            out.append((d * (hw - (le[-1] + half if strip_r else le[-1] - half)), "P-7b"))
        return out
    if sec.cls in ("A", "S", "GP") and sec.edge_strip > 0 and el != "none":
        for sg, name in ((1, "left"), (-1, "right")):       # sg in the travel frame: +1 = travel-left
            if el in (None, "both", name):
                out.append(((d if sec.oneway else 1) * sg * (hw - sec.edge_strip + half), "P-7b"))
    elif el in ("left", "right", "both"):
        # ADR 0205: edge lines read off the orthophoto on a road below class GP (rural G road, no edge strip):
        # only by authored override; narrow line (see edge_line_width) just inside the carriageway edge
        off = hw - S.EDGE_LINE_INSET_MINOR
        sp = getattr(sec, "edge_line_spacing", None)
        if sp:
            # ADR 0220: measured line-to-line distance; the line stays on the carriageway (EDGE_LINE_MIN_INSET)
            off = np.minimum(0.5 * float(sp), hw - EDGE_LINE_MIN_INSET)
        for sg, name in ((1, "left"), (-1, "right")):
            if el in ("both", name):
                out.append(((d if sec.oneway else 1) * sg * off, "P-7b"))
    return out


RAIL_P4_LEN_M = 50.0       # ADR 0268 WORKING_VALUE: P-4 on each approach of a level crossing, from the outer rail


def unmarked(sec) -> bool:
    """ADR 0215 (owner D65 p.6): a carriageway under construction / not open to traffic carries no horizontal
    markings at all (authored `set: {construction: true}`, roads.closures)."""
    return bool(getattr(sec, "construction", False))


EDGE_DASHED_KIND = "edge_line_dashed"
EDGE_DASHED_SNAP_M = 1.5     # a span sample may lie this far outside the carriageway half-width (axis traced off data)
EDGE_DASHED_STEP_M = 2.0     # resampling of line_en
EDGE_LINE_MIN_INSET = 0.12   # WORKING_VALUE (ADR 0220): an authored edge_line_spacing keeps the line axis this far
                             # inside the carriageway edge (half the 0.12 m line + 0.06 m of asphalt)


def _other_chain(owner, i, c):
    """True when sample i exists and lies on a chain other than c (the authored line goes on through a junction)."""
    return 0 <= i < len(owner) and owner[i] is not None and owner[i][0] is not c


def edge_dashed_spans(net, authored, report=None):
    """ADR 0220: authored spans where an override edge line is broken instead of solid (a bus bay, a junction mouth
    the OSM graph does not have, a section painted with short dashes):

      kind: edge_line_dashed   line_en: [[E, N], ...] (the carriageway axis from the start to the end of the span,
                                        >= 2 points; may run through junctions: every chain it follows is broken)
                               side: left | right   (of the carriageway, looking along line_en)
                               line: P-7a (dash / gap of S.DASH) or dash_m: [dash, gap] (measured)

    The line is resampled every EDGE_DASHED_STEP_M; a sample belongs to the nearest chain whose carriageway it lies on
    (|lat| <= half-width + EDGE_DASHED_SNAP_M) running the same way (|cos| >= 0.8). Each run of >= 2 consecutive samples
    on one chain is a span; where the line goes on to ANOTHER chain (through a junction) the span reaches that chain end.
    Samples that match no chain are a hole: the span ends at the last matched sample on either side of it, the hole
    stays solid and the dash / gap rhythm restarts behind it like at any span start (`dashed`).
    Returns {chain_id: [(s_lo, s_hi, lat_sign, dash, gap, id)]}. Nothing matched = stale (reported, never dropped)."""
    out, applied, stale = {}, [], []
    chains = [c for c in net.chains if not c.meta.get("absorbed") and len(c.line.p) >= 2]
    for o in authored or []:
        if o.get("kind") != EDGE_DASHED_KIND:
            continue
        # review s23 D18 P2-6: a malformed entry (no id, unknown line, bad dash_m / line_en) is stale, never an exception
        oid = o.get("id", "?")
        try:
            pts = np.asarray(o.get("line_en") or [], float).reshape(-1, 2)
            dm = o.get("dash_m") or S.DASH.get(o.get("line", "P-7a"))
            dash, gap = (float(v) for v in dm)
            ok = bool(np.isfinite(pts).all()) and math.isfinite(dash) and math.isfinite(gap) and dash > 0 and gap > 0
        except (TypeError, ValueError):
            ok = False
        if not ok or "id" not in o:
            stale.append(oid)
            continue
        side = o.get("side")
        runs = []
        if len(pts) >= 2 and side in ("left", "right"):
            seg = np.hypot(*np.diff(pts, axis=0).T)
            cum = np.concatenate([[0.0], np.cumsum(seg)])
            u = np.unique(np.append(np.arange(0.0, cum[-1], EDGE_DASHED_STEP_M), cum[-1]))
            Q = np.column_stack([np.interp(u, cum, pts[:, 0]), np.interp(u, cum, pts[:, 1])])
            D = np.gradient(Q, axis=0)
            D /= np.maximum(np.hypot(*D.T), 1e-9)[:, None]
            owner = [None] * len(Q)
            for k, q in enumerate(Q):
                best = None
                for c in chains:
                    s, lat = c.line.project(q)
                    if abs(lat) > float(c.hw_at(s)) + EDGE_DASHED_SNAP_M:
                        continue
                    t, _ = c.line.frame(s)
                    cos = float(np.dot(t, D[k]))
                    if abs(cos) < 0.8:
                        continue
                    if best is None or abs(lat) < best[0]:
                        best = (abs(lat), c, s)
                owner[k] = None if best is None else (best[1], best[2])
            k = 0
            while k < len(Q):
                if owner[k] is None:
                    k += 1
                    continue
                c = owner[k][0]
                k1 = k
                while k1 + 1 < len(Q) and owner[k1 + 1] is not None and owner[k1 + 1][0] is c:
                    k1 += 1
                if k1 > k:
                    sa, sb = owner[k][1], owner[k1][1]
                    fwd = sb > sa
                    # the span reaches the chain end only where the line really goes on to ANOTHER chain (through a
                    # junction); samples that matched no chain (a hole: the traced axis strays off the carriageway,
                    # the graph changed under the override) end the span at the last matched sample - the hole and
                    # the rest of the chain stay solid (review of PR #98, FIX 1)
                    if _other_chain(owner, k - 1, c):
                        sa = 0.0 if fwd else c.length
                    if _other_chain(owner, k1 + 1, c):
                        sb = c.length if fwd else 0.0
                    sign = (1.0 if side == "left" else -1.0) * (1.0 if fwd else -1.0)
                    runs.append((c.id, (min(sa, sb), max(sa, sb), sign, float(dash), float(gap), o["id"])))
                k = k1 + 1
        if not runs:
            stale.append(o["id"])
            continue
        for cid, span in runs:
            out.setdefault(cid, []).append(span)
            applied.append({"id": o["id"], "chain": cid, "s": [round(span[0], 2), round(span[1], 2)],
                            "lat_sign": span[2]})
    if report is not None:
        report["edge_line_dashed"] = {"applied": applied, "stale": stale}
    if hasattr(net, "overrides_stale"):
        net.overrides_stale.extend(s for s in stale if s not in net.overrides_stale)
        net.overrides_applied.extend({"id": a["id"], "targets": [a["chain"]]} for a in applied)
    return out


def _solid_with_dashes(buf, c, sa, sb, lat, w, spans, sign, kind):
    """Edge line from sa to sb: solid, broken (dash / gap) inside the authored spans on its side (ADR 0220)."""
    iv = sorted((max(sa, a), min(sb, b), d, g) for a, b, sg, d, g, _ in spans if sg == sign and min(sb, b) > max(sa, a))
    cur = sa
    for a, b, d, g in iv:
        if a > cur:
            strip(buf, c, cur, a, lat, w, kind)
        if b > max(a, cur):
            # same paint kind as the solid line (QA: consistency.PAINT, fidelity overlays), broken pattern
            dashed(buf, c, max(a, cur), b, lat, w, d, g, kind)
        cur = max(cur, b)
    if sb > cur:
        strip(buf, c, cur, sb, lat, w, kind)
    return len(iv)


def edge_line_width(sec):
    """0.24 m (P-7a/P-7b) on class A / S / GP; 0.12 m on lower classes, painted only by override (ADR 0205)."""
    return S.LINE_W_WIDE if sec.cls in ("A", "S", "GP") or getattr(sec, "lane_edges", None) else S.LINE_W_NARROW


def build_markings(buf: MeshBuf, net, juncs, ctx_points, report: dict):
    # ADR 0100: authored paved aprons re-surface the generated carriageway before any paint is draped on it
    from . import aprons as APR
    APR.apply(buf, getattr(net, "authored", None) or [], report, net.overrides_applied, net.overrides_stale)
    first = len(buf.parts)
    _build_markings(buf, net, juncs, ctx_points, report)
    report["overlap_removed_tris"] = drop_overlapping(buf, net, first)
    # ADR 0093: lines carried through the junction patches, authored P-21 zones (after the overlap pass: these are
    # draped on the generated surface and belong to no single chain)
    from . import through_lines as TL
    TL.build(buf, net, juncs, report, MARKED, lane_layout)
    from . import authored_paint as AP
    authored = getattr(net, "authored", None) or []
    AP.clear_zones(buf, authored, report, net.overrides_applied)        # ADR 0095: erase zones, then authored paint
    TL.paint_zones(buf, authored, report, net.overrides_applied, net.overrides_stale)
    AP.paint(buf, authored, report, net.overrides_applied, net.overrides_stale)


FRAGMENT_MIN_M = 2.0        # ADR 0093: a line cut by the overlap pass to less than this is removed
OVERLAP_INSET_M = 0.25      # a line is inside another carriageway when it lies this far inside its edge (WORKING_VALUE)
OVERLAP_DZ_M = 1.0          # ... and within this height of its surface (bridges over roads are not overlaps)


def drop_overlapping(buf, net, first):
    """Removes marking triangles of one chain that lie on another chain's carriageway (ADR 0018 overlap zones: an
    on-ramp running onto Andersa, the gate split at Kwadrat Park). Both chains used to paint their edge and lane lines
    across each other there (REVIEW r4 P1). Lines on a shared touching edge (within OVERLAP_INSET_M) are kept."""
    import shapely
    from shapely.geometry import LineString as _LS
    chains = [c for c in net.chains if not c.meta.get("absorbed") and len(c.line.p) >= 2]
    foot = [_LS(c.line.p).buffer(float(np.max(c.hw_at(c.line.s))) + 0.5) for c in chains]
    tree = shapely.STRtree(foot)
    removed = 0
    for pi in range(first, len(buf.parts)):
        p = buf.parts[pi]
        if p.layer != "markings" or "@" not in p.src or p.src.startswith("P-10J@"):
            continue        # a zebra draped on a junction patch crosses the neighbour ribbon there by design (r9d:
                            # its stripes came out cut diagonally, half triangles dropped)
        own = p.src.split("@", 1)[1]
        cen = p.V[p.T].mean(1)
        hits = tree.query(shapely.points(cen[:, :2]), predicate="intersects")
        if hits.size == 0:
            continue
        drop = np.zeros(len(p.T), bool)
        for ti, ci in zip(hits[0].tolist(), hits[1].tolist()):
            c = chains[ci]
            if c.id == own or drop[ti]:
                continue
            s, lat = c.line.project(cen[ti, :2])
            if not (c.t_a <= s <= c.length - c.t_b):
                continue
            hw = float(c.hw_at(s))
            if abs(lat) > hw - OVERLAP_INSET_M:
                continue
            if abs(float(c.crossfall_z(s, lat)) - (cen[ti, 2] - S.MARKING_LIFT)) > OVERLAP_DZ_M:
                continue
            drop[ti] = True
        if drop.any():
            removed += int(drop.sum())
            p.T = p.T[~drop]
            # ADR 0093: what is left of a cut line shorter than FRAGMENT_MIN_M is a stray fragment (REVIEW 0077 #10),
            # a cut glyph (arrow, give-way triangle) is removed whole
            kind = p.src.split("@", 1)[0]
            if kind.startswith(("P-8", "P-13")):
                removed += len(p.T)
                p.T = p.T[:0]
            elif kind.split("-P-2a")[0] in ("lane", "centre", "P-4", "P-7b") and len(p.T):
                tri = p.V[p.T]
                left = 0.5 * float(np.sum(np.max(np.linalg.norm(tri - np.roll(tri, 1, axis=1), axis=2), axis=1)))
                if left < FRAGMENT_MIN_M:
                    removed += len(p.T)
                    p.T = p.T[:0]
    buf.parts[first:] = [p for p in buf.parts[first:] if len(p.T)]
    return removed


def _build_markings(buf: MeshBuf, net, juncs, ctx_points, report: dict):
    secs = net.sec_list
    _SECS[:] = secs
    arm_info = arm_infos(juncs, secs)
    counts = {}
    dashed_spans = edge_dashed_spans(net, getattr(net, "authored", None), report)

    def cnt(k, n=1):
        counts[k] = counts.get(k, 0) + n

    # ---- crossings: snap to chains
    from streetscape import cycleways as CY
    crossings = {}
    ctx_red_nodes = {p["osm_node"] for p in ctx_points if p.get("kind") == "highway=crossing" and p.get("crossing_red") is True}
    ctx_white_nodes = {p["osm_node"] for p in ctx_points if p.get("kind") == "highway=crossing" and p.get("crossing_red") is False}
    _top = []

    def _want_p11_red(osm) -> bool:
        if osm in ctx_red_nodes:
            return True
        if osm in ctx_white_nodes:
            return False
        try:
            oid = int(osm)
        except (TypeError, ValueError):
            return False
        if oid in CY.P11_RED_NODES:
            return True
        # Synthetic unit-test node IDs (< 100_000) default to red=True unless explicitly marked crossing_red=False
        return 0 < oid < 100_000

    def top_of(e, n):           # exact top of the road / junction-patch meshes built so far (lazy, one index)
        if not _top:
            from streetscape.furniture import SurfaceTop
            _top.append(SurfaceTop([p for p in buf.parts if p.layer == "road"]))
        return _top[0].top(e, n)
    from . import compact_roundabout as CR
    cr_juncs = {id(j) for j in juncs if getattr(j, "compact", None) is not None and CR.kerb_mode(j.compact.opts)}
    cr_zones = [j.compact.outline.buffer(2.0) for j in juncs if id(j) in cr_juncs and j.compact.outline is not None]
    for p in ctx_points:
        if p["kind"] != "highway=crossing" or p.get("crossing") in ("unmarked", "no", "informal"):
            continue
        try:
            if int(p.get("osm_node") or 0) in CY.P11_NONE_NODES:
                continue
        except (TypeError, ValueError):
            pass
        q = np.array([p["e"], p["n"]])
        if any(pg.contains(shapely.Point(*q)) for pg in cr_zones):
            continue        # ADR 0274: crossings of a kerb-mode compact roundabout are authored at the ring
        best = None
        for c in net.chains:
            if c.meta.get("absorbed"):
                continue
            lo, hi = c.line.p.min(0) - 12, c.line.p.max(0) + 12
            if not (lo[0] <= q[0] <= hi[0] and lo[1] <= q[1] <= hi[1]):
                continue
            s, lat = c.line.project(q)
            if abs(lat) <= float(c.hw_at(s)) + 0.5 and (best is None or abs(lat) < best[2]):
                best = (c, s, abs(lat))
        if best is not None:
            crossings.setdefault(best[0].id, []).append((best[1], p["osm_node"]))
    # ADR 0093: what crosses there? Only a cycleway through the node -> P-11 (two rows of squares), otherwise P-10.
    # Two crossing nodes closer than their widths on one chain (footway + cycleway side by side, or one crossing
    # mapped twice) used to give two zebras laid over each other (REVIEW 0077 #9): same kind -> one crossing at the
    # mean station; foot + cycle -> pushed apart until they abut.
    foot_lines = getattr(net, "foot_lines", None) or []
    ftree = shapely.STRtree([f[0] for f in foot_lines]) if foot_lines else None
    xy_of = {p["osm_node"]: (p["e"], p["n"]) for p in ctx_points if p["kind"] == "highway=crossing"}

    def crossing_kind(osm):
        if ftree is None or osm not in xy_of:
            return "P-10"
        pt = shapely.Point(*xy_of[osm])
        kinds = {foot_lines[int(k)][1] for k in ftree.query(pt, predicate="dwithin", distance=0.75)}
        return "P-11" if kinds == {"cycleway"} else "P-10"

    # ADR 0188: a built cycle track (streetscape.cycleways, net.cycle_items) through the node decides the crossing:
    # DDR -> P-11 (3.0 m clear when two-way) on red surfacing; DDR + footway side by side -> P-10 and P-11 abutting,
    # the cycle crossing on the side where the DDR strip lies.
    cyc_items = getattr(net, "cycle_items", None) or []
    ctree = shapely.STRtree([it["line"] for it in cyc_items]) if cyc_items else None
    chain_of = {c.id: c for c in net.chains}

    def cycle_at(osm):
        if ctree is None or osm not in xy_of:
            return None
        ks = ctree.query(shapely.Point(*xy_of[osm]), predicate="dwithin", distance=0.75)
        return cyc_items[int(sorted(ks)[0])] if len(ks) else None

    def cycle_dir(c, s_, it, osm):
        """+1 / -1: along the chain, the side of the node on which the DDR strip of a segregated path lies"""
        ln = it["line"]
        u = ln.project(shapely.Point(*xy_of[osm]))
        a, b = ln.interpolate(max(u - 0.5, 0.0)), ln.interpolate(min(u + 0.5, ln.length))
        tp = np.array([b.x - a.x, b.y - a.y])
        tp /= max(float(np.hypot(*tp)), 1e-9)
        tc = c.line.t[c.idx(s_)]
        return 1.0 if float(np.dot(it["side"] * np.array([-tp[1], tp[0]]), tc)) >= 0 else -1.0

    merged = 0
    report["crossings_cycle"] = {"ddr": 0, "segregated": 0}
    is_dojlidy = getattr(net, "region_id", None) == "bialystok-dojlidy"
    for cid, lst in crossings.items():
        ent = []
        c_chain = chain_of[cid]
        for s_, osm in lst:
            try:
                oid = int(osm)
            except (TypeError, ValueError):
                oid = 0
            it = cycle_at(osm)
            if is_dojlidy and c_chain.section(s_, secs).highway == "service" and oid not in CY.P11_RED_NODES:
                continue
            if it is None:
                if oid in CY.P11_RED_NODES:
                    w11 = S.P11_CLEAR_TWO_WAY + 2 * S.P11_SQUARE
                    report["crossings_cycle"]["segregated"] += 1
                    ent.append((s_ + w11 / 2 + 0.2, osm, "P-11", w11))
                    ent.append((s_ - S.P10_WIDTH / 2 - 0.2, osm, "P-10", S.P10_WIDTH))
                    continue
                kd = crossing_kind(osm)
                ent.append((s_, osm, kd, S.P10_WIDTH if kd == "P-10" else S.P11_CLEAR + 2 * S.P11_SQUARE))
                continue
            w11 = (S.P11_CLEAR_TWO_WAY if it["two_way"] else S.P11_CLEAR) + 2 * S.P11_SQUARE
            report["crossings_cycle"][it["kind"]] += 1
            if it["kind"] == "ddr":
                ent.append((s_, osm, "P-11", w11))
                continue
            dc = cycle_dir(c_chain, s_, it, osm)
            ub = it["total"] / 2 - it["w_cycle"]            # DDR / footway boundary, measured towards the DDR
            ent.append((s_ + dc * (ub + w11 / 2 + 0.2), osm, "P-11", w11))
            ent.append((s_ + dc * (ub - S.P10_WIDTH / 2 - 0.2), osm, "P-10", S.P10_WIDTH))
        lst = sorted(ent)
        out = []
        for s_, osm, kd, wd in lst:
            if out:
                ps, posm, pkd, pwd = out[-1]
                need = (pwd + wd) / 2 + 0.4
                if s_ - ps < need:
                    if pkd == kd:
                        out[-1] = (0.5 * (ps + s_), posm, pkd, pwd)
                        merged += 1
                        continue
                    mid = 0.5 * (ps + s_)
                    out[-1] = (mid - need / 2, posm, pkd, pwd)
                    s_ = mid + need / 2
            out.append((s_, osm, kd, wd))
        crossings[cid] = out
    report["crossings_snapped"] = sum(len(v) for v in crossings.values())
    report["crossings_merged"] = merged
    report["crossings_p11"] = sum(1 for v in crossings.values() for x in v if x[2] == "P-11")

    for c in net.chains:
        if c.meta.get("absorbed"):
            continue
        s0, s1 = c.t_a, c.length - c.t_b
        if s1 - s0 < 1.0:
            continue
        # piecewise by section
        sidx = c.sec_idx
        cuts = [0] + [k for k in range(1, len(sidx)) if sidx[k] != sidx[k - 1]] + [len(sidx)]
        appr = approach_ends(c, arm_info, secs)   # stations of junction approaches for P-2a
        # seams-fix-s23: the rest of a P-2a approach of the neighbouring tile that its seam cut (net.seam_p2a)
        seam_cont = [(s0, s0 + L_) if end == "a" else (s1 - L_, s1)
                     for (cid, end), L_ in getattr(net, "seam_p2a", {}).items() if cid == c.id]
        for a_, b_ in zip(cuts, cuts[1:]):
            sec = secs[int(sidx[a_])]
            sa = max(s0, c.line.s[a_])
            sb = min(s1, c.line.s[b_ - 1] if b_ - 1 < len(c.line.s) else s1)
            if b_ == len(sidx):
                sb = s1
            if sb - sa < 1.0:
                continue
            if unmarked(sec):
                cnt("construction section (no markings)")     # ADR 0215: not open to traffic, no horizontal signs
                continue
            marked = sec.highway in MARKED or sec.roundabout
            hw = float(c.hw_at(0.5 * (sa + sb)))
            dirn = int(c.dirn[a_]) or 1
            lat_c, bounds, _ = lane_layout(sec, hw, dirn)
            fast = (sec.maxspeed or 50) > 70
            dash, gap = S.DASH["P-1a" if fast else "P-1b"]
            if marked:
                cont = list(seam_cont)
                for end, sj in appr.items():
                    cont.append((sj, sj + S.P2A_MIN_LEN) if end == "a" else (sj - S.P2A_MIN_LEN, sj))
                for lat in bounds:
                    if sec.oneway:            # one-way lane lines are laid out from the left gutter: follow it
                        lat = (lambda ss_, l0=float(lat), sec=sec, hw=hw, dirn=dirn:
                               follow_edge(sec, l0, hw, c.hw_at(ss_), dirn))
                    _segmented(buf, c, sa, sb, lat, S.LINE_W_NARROW, dash, gap, cont, "lane")
                    cnt("P-1 lane line")
                if lat_c is not None and sec.width >= S.SEGREGATION_MIN_CARRIAGEWAY:
                    if sec.lanes >= 4:
                        for off in (-0.12, 0.12):
                            strip(buf, c, sa, sb, lat_c + off, S.LINE_W_NARROW, "P-4")
                        cnt("P-4 double centre line")
                    else:
                        # ADR 0268: P-4 double continuous line on the approaches to a level crossing and across it
                        # (Dz.U. 2025 poz. 1105 § 79 pkt 4 lit. b); length RAIL_P4_LEN_M is a WORKING_VALUE
                        rx = sorted((max(sa, x["s"] - x["rail_d"] - RAIL_P4_LEN_M), min(sb, x["s"] + x["rail_d"] + RAIL_P4_LEN_M))
                                    for x in c.meta.get("rail_xings", []))
                        cur = sa
                        for xa, xb in rx:
                            if xb - xa < 0.5:
                                continue
                            xa = max(xa, cur)
                            if xa > cur:
                                _segmented(buf, c, cur, xa, lat_c, S.LINE_W_NARROW, dash, gap, cont, "centre")
                            for off in (-0.12, 0.12):
                                strip(buf, c, xa, xb, lat_c + off, S.LINE_W_NARROW, "P-4")
                            cnt("P-4 level crossing approach")
                            cur = max(cur, xb)
                        if sb > cur:
                            _segmented(buf, c, cur, sb, lat_c, S.LINE_W_NARROW, dash, gap, cont, "centre")
                        cnt("P-1 centre line")
                for k_e, (lat_e, _) in enumerate(edge_lines(sec, hw, dirn)):
                    lat_fn = (lambda ss_, k_e=k_e, sec=sec, dirn=dirn: edge_lines(sec, c.hw_at(ss_), dirn)[k_e][0])
                    spans = dashed_spans.get(c.id)
                    if spans:       # ADR 0220: authored broken spans of the edge line on this side
                        n_iv = _solid_with_dashes(buf, c, sa, sb, lat_fn, edge_line_width(sec), spans,
                                                  1.0 if float(lat_e) > 0 else -1.0, "P-7b")
                        if n_iv:
                            cnt("P-7a edge line span (authored)", n_iv)
                    else:
                        strip(buf, c, sa, sb, lat_fn, edge_line_width(sec), "P-7b")
                    cnt("P-7b edge line")
            # arrows from turn:lanes at the downstream end of this section
            for tl, tdir in ((sec.turn_fwd, 1), (sec.turn_bwd, -1)):
                if not tl:
                    continue
                trav = dirn * tdir if sec.oneway else tdir      # travel direction along chain
                _, _, centres = lane_layout(sec, hw, dirn)
                lanes = centres["fwd"] if tdir == 1 else centres["bwd"]
                if sec.oneway:
                    lanes = centres["fwd"]
                if len(lanes) != len(tl):
                    continue
                end_s = sb if trav > 0 else sa
                # the same turn:lanes continue past this point (an OSM way split at a minor junction or a section
                # boundary): the lanes do not diverge here, so no arrows (they belong before the real divergence,
                # ADR 0074 - arrows before the fire-station exit on Andersa)
                if _turns_continue(c, sec, tl, trav, end_s, s0, s1, arm_info, secs):
                    cnt("P-8 skipped (lanes continue)")
                    continue
                long = fast
                spacing = S.ARROW_SPACING["long" if long else "short"]
                L = (S.ARROW_LONG if long else S.ARROW_SHORT)["len"]
                for k_, lat in enumerate(lanes):
                    turns = [t for t in tl[k_].split(";") if t and t != "none"]
                    turns = [t for t in turns if t in ("through", "left", "right", "slight_left", "slight_right")]
                    if not turns:
                        continue
                    g = arrow_glyph(turns, long)
                    for m in range(2):
                        base = end_s - trav * (6.0 + L + m * spacing)
                        if not (sa + 1 <= base <= sb - 1 and sa + 1 <= base + trav * L <= sb - 1):
                            continue
                        # the glyph must lie on this carriageway where it is painted (narrowing sections: a 2-lane
                        # tag on a 4-5 m road put the arrow on the kerb, ADR 0074)
                        gw = float(np.max(np.abs(np.array(g.exterior.coords)[:, 1])))
                        hwb = float(min(c.hw_at(base), c.hw_at(base + trav * L)))
                        if abs(lat) + gw > hwb - 0.1:
                            cnt("P-8 skipped (off carriageway)")
                            continue
                        # ADR 0093 (REVIEW 0076 #11): the arrow lies on the lane axis and inside the lane where it is
                        # painted - not in a lane narrower than P8_MIN_LANE_W, not with a head on the lane line
                        lw_here = (2 * hwb - 2 * float(sec.edge_strip)) / max(len(lanes) if sec.oneway else sec.lanes, 1)
                        if lw_here < S.P8_MIN_LANE_W or gw > lw_here / 2 - 0.10:
                            cnt("P-8 skipped (lane too narrow)")
                            continue
                        polygon_mark(buf, c, g, base, lat, trav, trav, "P-8")
                        cnt("P-8 arrow")
        # crossings on this chain
        for s_c, osm, ckind, cwid in crossings.get(c.id, []):
            if unmarked(c.section(s_c, secs)):
                cnt("crossing skipped (construction)")
                continue
            hw = float(c.hw_at(s_c))
            if ckind == "P-11":
                clear = cwid - 2 * S.P11_SQUARE            # 2.0 m (ADR 0093) or 3.0 m two-way (ADR 0188)
                want_red = _want_p11_red(osm)
                placed_red: list[bool] = []
                if s0 + cwid / 2 + 0.5 <= s_c <= s1 - cwid / 2 - 0.5:
                    _emit_p11_ribbon(buf, c, s_c, hw, clear, red=want_red)
                    if want_red:
                        cnt("P-11 red surfacing")
                        report.setdefault("crossings_p11_red_nodes", []).append(osm)
                    cnt("P-11 cycle crossing")
                    c.meta.setdefault("crossings", []).append(round(float(s_c), 2))
                    continue
                if _drape_crossing(buf, c, s_c, hw, s0, s1, top_of, kind="P-11", clear=clear,
                                   red=want_red, red_out=placed_red):
                    cnt("P-11 cycle crossing")
                    cnt("P-11 cycle crossing in junction")
                    if placed_red:
                        cnt("P-11 red surfacing")
                        report.setdefault("crossings_p11_red_nodes", []).append(osm)
                    report.setdefault("crossings_in_junction", []).append(osm)
                    c.meta.setdefault("crossings", []).append(round(float(s_c), 2))
                    continue
                # not drapeable in the junction patch: clamp onto the carriageway ribbon if nearby;
                # never demote a P-11 cycle crossing into a pedestrian P-10 zebra
                if s_c < s0 + cwid / 2 + 0.5 and s0 - s_c < 8:
                    s_c = s0 + cwid / 2 + 0.5
                elif s_c > s1 - cwid / 2 - 0.5 and s_c - s1 < 8:
                    s_c = s1 - cwid / 2 - 0.5
                if s0 + cwid / 2 + 0.2 <= s_c <= s1 - cwid / 2 - 0.2:
                    _emit_p11_ribbon(buf, c, s_c, float(c.hw_at(s_c)), clear, red=want_red)
                    if want_red:
                        cnt("P-11 red surfacing")
                        report.setdefault("crossings_p11_red_nodes", []).append(osm)
                    cnt("P-11 cycle crossing")
                    c.meta.setdefault("crossings", []).append(round(float(s_c), 2))
                else:
                    report.setdefault("crossings_skipped", []).append(osm)
                continue
            half = S.P10_WIDTH / 2
            if s_c - half < s0 + 0.5 or s_c + half > s1 - 0.5:
                # inside a junction patch (wide signalised mouths, roundabout entries: Mapillary p40 / p42 show the
                # zebra right at the mouth, REFS-MAPILLARY #5): drape it on the generated patch at its OSM station
                # (ADR 0069); only where that fails move it onto the ribbon if close, else skip
                if _drape_crossing(buf, c, s_c, hw, s0, s1, top_of):
                    cnt("P-10 crossing")
                    cnt("P-10 crossing in junction")
                    report.setdefault("crossings_in_junction", []).append(osm)
                    c.meta.setdefault("crossings", []).append(round(float(s_c), 2))
                    continue
                if s_c < s0 and s0 - s_c < 8:
                    s_c = s0 + half + 0.5
                elif s_c > s1 and s_c - s1 < 8:
                    s_c = s1 - half - 0.5
                if s_c - half < s0 + 0.2 or s_c + half > s1 - 0.2:
                    report.setdefault("crossings_skipped", []).append(osm)
                    continue
            W = 2 * hw - 2 * 0.25
            n = int(math.floor((W + S.P10_GAP) / (S.P10_STRIPE + S.P10_GAP)))
            used = n * S.P10_STRIPE + (n - 1) * S.P10_GAP
            start = -used / 2
            for k_ in range(n):
                lat = start + k_ * (S.P10_STRIPE + S.P10_GAP) + S.P10_STRIPE / 2
                strip(buf, c, s_c - half, s_c + half, lat, S.P10_STRIPE, "P-10")
            cnt("P-10 crossing")
            c.meta.setdefault("crossings", []).append(round(float(s_c), 2))

    # ---- transverse lines at junction approaches
    for j in juncs:
        maxrank = min(RANK[a.cls(secs)] for a in j.arms)
        for i, a in enumerate(j.arms):
            c = a.chain
            if c.meta.get("absorbed") or a.is_ring():
                continue
            inb = a.inbound_dirn()
            sec = c.section(a.s(1.0), secs)
            if sec.highway == "service" and not j.signalized:
                continue
            rank = RANK[sec.cls]
            kind = approach_line_kind(j, rank, maxrank, sec.cls)
            if kind is None or inb == -1:
                continue
            if id(j) in cr_juncs:
                continue        # ADR 0274: P-13 lies along the ring edge (CR.build_markings), not at the split node
            t = j.trims[i]
            if t >= a.L - 2:
                continue
            hw = float(c.hw_at(a.s(t)))
            lat_c, _, _ = lane_layout(sec, hw, int(c.dirn[c.idx(a.s(t))]) or 1)
            # inbound part of the cross-section (chain lateral)
            if inb == 1:
                lo, hi = -hw, hw
            else:
                if a.end == "a":
                    lo, hi = lat_c, hw
                else:
                    lo, hi = -hw, lat_c
            lo, hi = lo + 0.15, hi - 0.15
            d0 = t + 0.6
            if kind == "P-14" and j.signalized:
                # ADR 0279 P1: >= 2.0 m before the side head / >= 8.0 m before a head over the carriageway (zał. 2
                # pkt 4.2.5); the signal post stands at trim + S.SIGNAL_AFTER_TRIM (furniture.signals). Was t + 0.6 =
                # at the foot of the mast.
                ts = t + S.SIGNAL_AFTER_TRIM
                if ts <= a.L - 1:
                    d0 = max(d0, S.p14_before_signal_d(t, c.section(a.s(ts), secs), a.end))
            cr = [abs(sc - float(a.s(0))) for sc in c.meta.get("crossings", [])]
            near = [x for x in cr if x - S.P10_WIDTH / 2 < d0 + 6]
            if near:
                d0 = max(near) + S.P10_WIDTH / 2 + S.P14_BEFORE_CROSSING
            if d0 + 1 > a.L - 1:
                continue
            fwd = 1.0 if a.end == "a" else -1.0
            if kind == "P-14":
                s_mid = float(a.s(d0 + S.P14_DEPTH / 2))
                x = lo
                while x + S.P14_LEN <= hi + 1e-6:
                    strip_cross(buf, c, s_mid, S.P14_DEPTH, x, x + S.P14_LEN)
                    x += S.P14_LEN + S.P14_GAP
            elif kind == "P-12":
                # zał. 2 pkt 4.2.3 (Dz.U. s. 571-572): one continuous 0.50 m line over all inbound lanes, along the
                # edge of the priority carriageway (= where P-13 stood)
                strip_cross(buf, c, float(a.s(d0 + S.P12_W / 2)), S.P12_W, lo, hi, kind="P-12")
            else:
                s_base = float(a.s(d0))
                x = lo
                # triangle tip points toward the arriving driver (outward along the arm)
                tri = Polygon([(0, -S.P13_BASE / 2), (S.P13_H, 0), (0, S.P13_BASE / 2)])
                while x + S.P13_BASE <= hi + 1e-6:
                    polygon_mark(buf, c, tri, s_base, x + S.P13_BASE / 2, fwd, 1.0, "P-13")
                    x += S.P13_BASE + S.P13_GAP
            cnt(kind)
    cr_rep = CR.build_markings(buf, net, juncs, report)
    for k in ("P-10", "P-13"):
        if cr_rep[k]:
            cnt(f"{k} at compact roundabout", cr_rep[k])
    # ADR 0268: P-14 before a level crossing of category A-D (Dz.U. 2025 poz. 1105 § 79 pkt 4 lit. e), 2.0 m before the
    # crossing devices beside the carriageway (S.P14_BEFORE_SIGNAL, zał. 2 pkt 4.2.5). Only on carriageways that carry
    # markings at all (highway in MARKED): the local roads of the other crossings are unmarked - reported, not painted.
    for c in net.chains:
        for x in c.meta.get("rail_xings", []):
            for trav in (1.0, -1.0):                      # travel direction along the chain, towards the crossing
                d0 = x["device_d"] + S.P14_BEFORE_SIGNAL
                s_mid = x["s"] - trav * (d0 + S.P14_DEPTH / 2)
                if not (c.t_a + 1.0 < s_mid < c.length - c.t_b - 1.0):
                    cnt("P-14 level crossing skipped (road end)")
                    continue
                sec = c.section(s_mid, secs)
                dn = int(c.dirn[c.idx(s_mid)])
                if dn * trav < 0:
                    continue                              # one-way against this approach
                if unmarked(sec) or sec.highway not in MARKED:
                    cnt("P-14 level crossing skipped (unmarked road)")
                    continue
                hw = float(c.hw_at(s_mid))
                lat_c, _, _ = lane_layout(sec, hw, dn or 1)
                if dn != 0 or lat_c is None:
                    lo, hi = -hw, hw
                elif trav > 0:
                    lo, hi = -hw, lat_c
                else:
                    lo, hi = lat_c, hw
                lo, hi = lo + 0.15, hi - 0.15
                xl = lo
                while xl + S.P14_LEN <= hi + 1e-6:
                    strip_cross(buf, c, s_mid, S.P14_DEPTH, xl, xl + S.P14_LEN)
                    xl += S.P14_LEN + S.P14_GAP
                cnt("P-14 level crossing")
    report["markings"] = counts


# A zebra is draped on a junction patch only this far from the node (m): closer, it would cross the other arms.
P10_NODE_CLEAR_M = 3.0      # WORKING_VALUE (clear of the stripes' own half length)
P10_DRAPE_STEP_M = 0.5      # vertices along a stripe on a patch (patch facets are not planar)
P10_DRAPE_MAX_STEP_M = 0.06  # a larger height step between samples 0.5 m apart is a kerb, not the carriageway


CYCLE_RED_LIFT = S.MARKING_LIFT / 2      # under the paint, over the asphalt (decal depth offset in the engine)


def cycle_red(buf, c, s0, s1, hw):
    """ADR 0188: red surfacing of a cycle crossing, kerb to kerb between the two rows of P-11 squares (owner photo
    P11-056, Dywizjonu 303). A grid <= 1 m follows the crown; material `cycle_crossing_red` (decal, markings layer)."""
    ns = max(1, int(math.ceil((s1 - s0) / 1.0)))
    nl = max(2, int(math.ceil(2 * hw / 1.0)))
    ss, ll = np.meshgrid(np.linspace(s0, s1, ns + 1), np.linspace(-hw + 0.02, hw - 0.02, nl + 1), indexing="ij")
    ss, ll = ss.ravel(), ll.ravel()
    V = np.column_stack([c.line.offset_point(ss, ll), c.crossfall_z(ss, ll) + CYCLE_RED_LIFT])
    T = []
    for i in range(ns):
        for j in range(nl):
            a = i * (nl + 1) + j
            T += [(a, a + nl + 1, a + nl + 2), (a, a + nl + 2, a + 1)]
    buf.add("markings", "cycle_crossing_red", V, V[:, :2].copy(), np.array(T), src=f"DDR-X@{c.id}")


def _emit_p11_ribbon(buf, c, s_c, hw, clear, red: bool = True):
    """P-11 cycle crossing on a road ribbon: two rows of 0.5 m squares (+ red surfacing when verified, M65 §2.2)."""
    W = 2 * hw - 2 * 0.25
    nsq = int(math.floor((W + S.P11_GAP) / (S.P11_SQUARE + S.P11_GAP)))
    start = -(nsq * S.P11_SQUARE + (nsq - 1) * S.P11_GAP) / 2
    for row in (-1, 1):
        sr = s_c + row * (clear + S.P11_SQUARE) / 2
        for k_ in range(nsq):
            lat = start + k_ * (S.P11_SQUARE + S.P11_GAP) + S.P11_SQUARE / 2
            strip(buf, c, sr - S.P11_SQUARE / 2, sr + S.P11_SQUARE / 2, lat, S.P11_SQUARE, "P-11")
    if red:
        cycle_red(buf, c, s_c - clear / 2, s_c + clear / 2, hw)


def _drape_crossing(buf, c, s_c, hw, s0, s1, top_of, kind="P-10", clear=S.P11_CLEAR, red: bool = True, red_out=None):
    """P-10/P-11 inside a junction patch: stripes/squares in the chain frame at the OSM station, z = patch + lift.
    False (nothing added) when the station is too close to the node or any vertex is off the road meshes."""
    half = (clear + 2 * S.P11_SQUARE) / 2 if kind == "P-11" else S.P10_WIDTH / 2
    d_node = min(s_c, c.length - s_c)
    if d_node - half < P10_NODE_CLEAR_M:
        return False
    W = 2 * hw - 2 * 0.25
    n = int(math.floor((W + S.P10_GAP) / (S.P10_STRIPE + S.P10_GAP)))
    if n < 2:
        return False
    used = n * S.P10_STRIPE + (n - 1) * S.P10_GAP
    ss = np.linspace(s_c - half, s_c + half, int(round(S.P10_WIDTH / P10_DRAPE_STEP_M)) + 1)
    # stripes parallel to the arm at the crossing (tangent at s_c), not fanned along the chain's bend into the node
    o = np.asarray(c.line.offset_point(np.array([s_c]), np.array([0.0])), float).reshape(-1)[:2]
    a_ = np.asarray(c.line.offset_point(np.array([s_c - half]), np.array([0.0])), float).reshape(-1)[:2]
    b_ = np.asarray(c.line.offset_point(np.array([s_c + half]), np.array([0.0])), float).reshape(-1)[:2]
    t = (b_ - a_) / max(float(np.hypot(*(b_ - a_))), 1e-9)
    nrm = np.array([-t[1], t[0]])
    l_probe = np.asarray(c.line.offset_point(np.array([s_c]), np.array([1.0])), float).reshape(-1)[:2] - o
    if float(np.dot(l_probe, nrm)) < 0:                 # keep the chain's lateral sign convention
        nrm = -nrm
    meshes = []
    if kind == "P-11":      # cycle crossing (ADR 0093): two rows of squares instead of stripes
        nsq = int(math.floor((W + S.P11_GAP) / (S.P11_SQUARE + S.P11_GAP)))
        if nsq < 1:
            return False
        used_p11 = nsq * S.P11_SQUARE + (nsq - 1) * S.P11_GAP
        start = -used_p11 / 2
        for row in (-1.0, 1.0):
            sr = s_c + row * (clear + S.P11_SQUARE) / 2
            sq = np.array([sr - S.P11_SQUARE / 2, sr + S.P11_SQUARE / 2])
            for k_ in range(nsq):
                lat = start + k_ * (S.P11_SQUARE + S.P11_GAP) + S.P11_SQUARE / 2
                sides = []
                for l_ in (lat - S.P11_SQUARE / 2, lat + S.P11_SQUARE / 2):
                    p = o + np.outer(sq - s_c, t) + nrm * l_
                    z = np.array([top_of(float(e), float(nn)) for e, nn in p])
                    if not np.all(np.isfinite(z)) or np.max(np.abs(np.diff(z))) > P10_DRAPE_MAX_STEP_M:
                        return False
                    sides.append(np.column_stack([p, z + S.MARKING_LIFT]))
                meshes.append((lat, sides, sq))
        for lat, (a, b), sq in meshes:
            V = np.concatenate([a[:, None], b[:, None]], axis=1).reshape(-1, 3)
            uv = np.column_stack([np.repeat(sq - sq[0], 2), np.tile([0.0, 1.0], 2)])
            lv = np.tile([lat - S.P11_SQUARE / 2, lat + S.P11_SQUARE / 2], 2)
            buf.add("markings", "marking_white", V, uv, np.array([(0, 2, 3), (0, 3, 1)]), src=f"P-11J@{c.id}",
                    UV1=_paint_uv1(c, np.repeat(sq, 2), lv, "P-10"))
        if not red:
            return True
        # ADR 0188: red surfacing between the rows, stepping inward from full width to square span if kerbs interfere
        ns, nl = max(1, int(math.ceil(clear / 0.5))), max(2, int(math.ceil(2 * hw / 0.5)))
        for lim in (hw - 0.04, hw - 0.14, min(hw - 0.04, used_p11 / 2)):
            if lim <= 0.1:
                continue
            gs, gl = np.meshgrid(np.linspace(-clear / 2, clear / 2, ns + 1), np.linspace(-lim, lim, nl + 1),
                                 indexing="ij")
            p = o + np.outer(gs.ravel(), t) + np.outer(gl.ravel(), nrm)
            z = np.array([top_of(float(e), float(nn)) for e, nn in p])
            zg = z.reshape(ns + 1, nl + 1)
            if (np.all(np.isfinite(z))
                    and np.max(np.abs(np.diff(zg, axis=1))) <= P10_DRAPE_MAX_STEP_M
                    and np.max(np.abs(np.diff(zg, axis=0))) <= P10_DRAPE_MAX_STEP_M):
                T = []
                for i in range(ns):
                    for j in range(nl):
                        a = i * (nl + 1) + j
                        T += [(a, a + nl + 1, a + nl + 2), (a, a + nl + 2, a + 1)]
                if float(t[0] * nrm[1] - t[1] * nrm[0]) < 0:
                    T = [(a, c_, b) for a, b, c_ in T]
                buf.add("markings", "cycle_crossing_red", np.column_stack([p, z + CYCLE_RED_LIFT]), p.copy(),
                        np.array(T), src=f"DDR-XJ@{c.id}")
                if red_out is not None:
                    red_out.append(True)
                break
        return True
    for k_ in range(n):
        lat = -used / 2 + k_ * (S.P10_STRIPE + S.P10_GAP) + S.P10_STRIPE / 2
        sides = []
        for l_ in (lat - S.P10_STRIPE / 2, lat + S.P10_STRIPE / 2):
            p = o + np.outer(ss - s_c, t) + nrm * l_       # rigid rectangle: the chain bends into the node
            z = np.array([top_of(float(e), float(nn)) for e, nn in p])
            if not np.all(np.isfinite(z)) or np.max(np.abs(np.diff(z))) > P10_DRAPE_MAX_STEP_M:
                return False        # off the road meshes, or onto a kerb / island top
            sides.append(np.column_stack([p, z + S.MARKING_LIFT]))
        meshes.append((lat, sides))
    for lat, (a, b) in meshes:
        V = np.concatenate([a[:, None], b[:, None]], axis=1).reshape(-1, 3)
        T = []
        for i in range(len(ss) - 1):
            T += [(2 * i, 2 * i + 2, 2 * i + 3), (2 * i, 2 * i + 3, 2 * i + 1)]
        uv = np.column_stack([np.repeat(ss - ss[0], 2), np.tile([0.0, 1.0], len(ss))])
        sv = np.repeat(ss, 2)
        lv = np.tile([lat - S.P10_STRIPE / 2, lat + S.P10_STRIPE / 2], len(ss))
        buf.add("markings", "marking_white", V, uv, np.array(T), src=f"P-10J@{c.id}", UV1=_paint_uv1(c, sv, lv, "P-10"))
    return True


def _way(sec):
    return str(sec.edge_id).split(":")[0]


def arm_infos(juncs, secs) -> dict:
    """{arm key (chain id, "a" | "b"): (junction, arm index, best arm rank)} - what the marking stage knows of the ends."""
    out = {}
    for j in juncs:
        maxrank = min(RANK[a.cls(secs)] for a in j.arms)
        for i, a in enumerate(j.arms):
            out[a.key] = (j, i, maxrank)
    return out


def approach_ends(c, arm_info, secs) -> dict:
    """{"a" | "b": station of the junction end} of the chain ends that are junction approaches with the solid P-2a
    (pkt 2.2.1.6: signalised, or turn lanes that do not continue through the junction). Also read for the chains of a
    neighbouring tile (roads.seam_p2a, seams-fix-s23), so both tiles decide with this one rule."""
    s0, s1 = c.t_a, c.length - c.t_b
    sidx = c.sec_idx
    appr = {}
    for end, sj in (("a", s0), ("b", s1)):
        info = arm_info.get((c.id, end))
        # ADR 0095: a one-way carriageway approaches a junction only at its downstream end; the solid P-2a was
        # also painted for 20 m behind the junction (Andersa after the side street at n10015785253)
        d_end = int(c.dirn[0 if end == "a" else -1])
        if (d_end > 0 and end == "a") or (d_end < 0 and end == "b"):
            continue
        if info and (info[0].signalized or (any(secs[i].turn_fwd for i in np.unique(sidx))
                                            and not _lanes_continue(c, end, info[0], secs))):
            appr[end] = sj
    return appr


def _lanes_continue(c, end, j, secs):
    """True if an outbound arm of junction j continues this chain end's OSM way with the same turn:lanes."""
    s_in = 1.0 if end == "a" else c.length - 1.0
    sec = c.section(s_in, secs)
    tl = sec.turn_fwd or sec.turn_bwd
    if not tl:
        return False
    for a in j.arms:
        if a.chain is c or a.inbound_dirn() > 0:
            continue
        so = a.chain.section(a.s(1.0), secs)
        if _way(so) == _way(sec) and tl in (so.turn_fwd, so.turn_bwd):
            return True
    return False


def _turns_continue(c, sec, tl, trav, end_s, s0, s1, arm_info, secs):
    if (trav > 0 and end_s < s1 - 0.5) or (trav < 0 and end_s > s0 + 0.5):
        nxt = c.section(end_s + trav * 1.0, secs)          # mid-chain section boundary
        return nxt is not sec and tl in (nxt.turn_fwd, nxt.turn_bwd)
    info = arm_info.get((c.id, "b" if trav > 0 else "a"))
    return bool(info) and _lanes_continue(c, "b" if trav > 0 else "a", info[0], secs)


def strip_cross(buf, c, s_mid, depth, lat0, lat1, kind="P-14"):
    s = np.array([s_mid - depth / 2, s_mid + depth / 2])
    a = _surface_pts(c, s, np.full(2, lat0))
    b = _surface_pts(c, s, np.full(2, lat1))
    V = np.vstack([a, b])          # 0:(s0,lat0) 1:(s1,lat0) 2:(s0,lat1) 3:(s1,lat1)
    T = np.array([(0, 1, 3), (0, 3, 2)])
    uv1 = _paint_uv1(c, np.concatenate([s, s]), np.array([lat0, lat0, lat1, lat1]), kind)
    buf.add("markings", "marking_white", V, np.array([[0, 0], [0, 1], [1, 0], [1, 1]], float), T, src=f"{kind}@{c.id}",
            UV1=uv1)


def approach_line_kind(j, rank, maxrank, cls):
    """Transverse line of one inbound junction approach (None = no line):
    P-14 signalised; P-13 roundabout entry; P-12 where streetscape.furniture.junction_signs puts B-20 (j.stop and the
    approach ranks below the best arm - same test) - ADR 0279 P1, zał. 1 pkt 3.2.21 / zał. 2 pkt 4.2.3: P-12 with
    B-20 (was P-13); P-13 at give-way junctions and on minor approaches to G / GP / S / A roads."""
    if j.signalized:
        return "P-14"
    if j.roundabout:
        return "P-13"
    if getattr(j, "stop", False) and rank > maxrank and (cls in ("Z", "L", "G") or rank < RANK["D"]):
        return "P-12"
    if j.give_way or (rank > maxrank and maxrank <= RANK["G"]):
        return "P-13"
    return None


def _segmented(buf, c, sa, sb, lat, w, dash, gap, cont, kind):
    """Dashed line, continuous inside any (start, end) interval of `cont`."""
    iv = sorted((max(sa, a), min(sb, b)) for a, b in cont if min(sb, b) > max(sa, a))
    cur = sa
    for a, b in iv:
        if a > cur:
            dashed(buf, c, cur, a, lat, w, dash, gap, kind)
        strip(buf, c, a, b, lat, w, kind + "-P-2a")
        cur = max(cur, b)
    if sb > cur:
        dashed(buf, c, cur, sb, lat, w, dash, gap, kind)
