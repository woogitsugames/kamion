"""Horizontal markings as geometry lying MARKING_LIFT above the road surface (decal mesh; the engine
material adds a depth offset). Dimensions and placement rules: standards.py ([ZNAKI-Z2]).

Placed:
  lane lines P-1a/P-1b (P-2a in the last 20 m before a signalised / turn-lane approach),
  centre lines of two-way roads (none if the carriageway is < 5.80 m), edge lines P-7b on GP roads,
  P-14 at signalised approaches, P-13 at roundabout entries and minor approaches to G/GP roads,
  P-10 at OSM crossing nodes (crossing != unmarked/no), P-8 arrows from turn:lanes.
"""

from __future__ import annotations

import math
import zlib

import numpy as np
import shapely
from shapely import affinity
from shapely.geometry import Polygon, box

from . import standards as S
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
TRANSVERSE = ("P-8", "P-10", "P-13", "P-14")
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
    lanec = (lat + hw - edge) / lw if ring else np.abs(lat) / lw
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
    a = _surface_pts(c, ss, np.full(len(ss), lat - w / 2))
    b = _surface_pts(c, ss, np.full(len(ss), lat + w / 2))
    V = np.concatenate([a[:, None], b[:, None]], axis=1).reshape(-1, 3)
    T = []
    for i in range(n):
        T += [(2 * i, 2 * i + 2, 2 * i + 3), (2 * i, 2 * i + 3, 2 * i + 1)]
    uv = np.column_stack([np.repeat(ss - s0, 2), np.tile([0.0, 1.0], len(ss))])
    sv = np.repeat(ss, 2)
    lv = np.tile([lat - w / 2, lat + w / 2], len(ss))
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
    lw, e = sec.lane_w, sec.edge_strip
    if sec.oneway:
        bounds = [hw - e - k * lw for k in range(1, sec.lanes)]
        centres = [dirn * (hw - e - (i + 0.5) * lw) for i in range(sec.lanes)]
        return None, bounds, {"fwd": centres, "bwd": []}
    lat_c = -hw + e + sec.lanes_fwd * lw
    bounds = [lat_c - k * lw for k in range(1, sec.lanes_fwd)] + [lat_c + k * lw for k in range(1, sec.lanes_bwd)]
    fwd = [lat_c - (i + 0.5) * lw for i in range(sec.lanes_fwd)]
    bwd = [lat_c + (i + 0.5) * lw for i in range(sec.lanes_bwd)]
    return lat_c, bounds, {"fwd": fwd, "bwd": bwd}


def build_markings(buf: MeshBuf, net, juncs, ctx_points, report: dict):
    first = len(buf.parts)
    _build_markings(buf, net, juncs, ctx_points, report)
    report["overlap_removed_tris"] = drop_overlapping(buf, net, first)


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
        if p.layer != "markings" or "@" not in p.src:
            continue
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
    buf.parts[first:] = [p for p in buf.parts[first:] if len(p.T)]
    return removed


def _build_markings(buf: MeshBuf, net, juncs, ctx_points, report: dict):
    secs = net.sec_list
    _SECS[:] = secs
    arm_info = {}
    for j in juncs:
        maxrank = min(RANK[a.cls(secs)] for a in j.arms)
        for i, a in enumerate(j.arms):
            arm_info[a.key] = (j, i, maxrank)
    counts = {}

    def cnt(k, n=1):
        counts[k] = counts.get(k, 0) + n

    # ---- crossings: snap to chains
    crossings = {}
    for p in ctx_points:
        if p["kind"] != "highway=crossing" or p.get("crossing") in ("unmarked", "no", "informal"):
            continue
        q = np.array([p["e"], p["n"]])
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
    report["crossings_snapped"] = sum(len(v) for v in crossings.values())

    for c in net.chains:
        if c.meta.get("absorbed"):
            continue
        s0, s1 = c.t_a, c.length - c.t_b
        if s1 - s0 < 1.0:
            continue
        # piecewise by section
        sidx = c.sec_idx
        cuts = [0] + [k for k in range(1, len(sidx)) if sidx[k] != sidx[k - 1]] + [len(sidx)]
        appr = {}   # stations of junction approaches for P-2a
        for end, sj in (("a", s0), ("b", s1)):
            info = arm_info.get((c.id, end))
            if info and (info[0].signalized or any(net.sec_list[i].turn_fwd for i in np.unique(sidx))):
                appr[end] = sj
        for a_, b_ in zip(cuts, cuts[1:]):
            sec = secs[int(sidx[a_])]
            sa = max(s0, c.line.s[a_])
            sb = min(s1, c.line.s[b_ - 1] if b_ - 1 < len(c.line.s) else s1)
            if b_ == len(sidx):
                sb = s1
            if sb - sa < 1.0:
                continue
            marked = sec.highway in MARKED or sec.roundabout
            hw = float(c.hw_at(0.5 * (sa + sb)))
            dirn = int(c.dirn[a_]) or 1
            lat_c, bounds, _ = lane_layout(sec, hw, dirn)
            fast = (sec.maxspeed or 50) > 70
            dash, gap = S.DASH["P-1a" if fast else "P-1b"]
            if marked:
                cont = []
                for end, sj in appr.items():
                    cont.append((sj, sj + S.P2A_MIN_LEN) if end == "a" else (sj - S.P2A_MIN_LEN, sj))
                for lat in bounds:
                    _segmented(buf, c, sa, sb, lat, S.LINE_W_NARROW, dash, gap, cont, "lane")
                    cnt("P-1 lane line")
                if lat_c is not None and sec.width >= S.SEGREGATION_MIN_CARRIAGEWAY:
                    if sec.lanes >= 4:
                        for off in (-0.12, 0.12):
                            strip(buf, c, sa, sb, lat_c + off, S.LINE_W_NARROW, "P-4")
                        cnt("P-4 double centre line")
                    else:
                        _segmented(buf, c, sa, sb, lat_c, S.LINE_W_NARROW, dash, gap, cont, "centre")
                        cnt("P-1 centre line")
                if sec.cls in ("A", "S", "GP") and sec.edge_strip > 0 and not sec.roundabout:
                    for sg in (-1, 1):
                        strip(buf, c, sa, sb, sg * (hw - sec.edge_strip + S.LINE_W_WIDE / 2), S.LINE_W_WIDE, "P-7b")
                    cnt("P-7b edge line", 2)
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
                        polygon_mark(buf, c, g, base, lat, trav, trav, "P-8")
                        cnt("P-8 arrow")
        # crossings on this chain
        for s_c, osm in crossings.get(c.id, []):
            hw = float(c.hw_at(s_c))
            half = S.P10_WIDTH / 2
            if s_c - half < s0 + 0.5 or s_c + half > s1 - 0.5:
                # inside a junction patch: move onto the ribbon if close, else skip
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
            kind = None
            if j.signalized:
                kind = "P-14"
            elif j.roundabout:
                kind = "P-13"
            elif j.give_way or (rank > maxrank and maxrank <= RANK["G"]):
                kind = "P-13"
            if kind is None or inb == -1:
                continue
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
            else:
                s_base = float(a.s(d0))
                x = lo
                # triangle tip points toward the arriving driver (outward along the arm)
                tri = Polygon([(0, -S.P13_BASE / 2), (S.P13_H, 0), (0, S.P13_BASE / 2)])
                while x + S.P13_BASE <= hi + 1e-6:
                    polygon_mark(buf, c, tri, s_base, x + S.P13_BASE / 2, fwd, 1.0, "P-13")
                    x += S.P13_BASE + S.P13_GAP
            cnt(kind)
    report["markings"] = counts


def strip_cross(buf, c, s_mid, depth, lat0, lat1):
    s = np.array([s_mid - depth / 2, s_mid + depth / 2])
    a = _surface_pts(c, s, np.full(2, lat0))
    b = _surface_pts(c, s, np.full(2, lat1))
    V = np.vstack([a, b])          # 0:(s0,lat0) 1:(s1,lat0) 2:(s0,lat1) 3:(s1,lat1)
    T = np.array([(0, 1, 3), (0, 3, 2)])
    uv1 = _paint_uv1(c, np.concatenate([s, s]), np.array([lat0, lat0, lat1, lat1]), "P-14")
    buf.add("markings", "marking_white", V, np.array([[0, 0], [0, 1], [1, 0], [1, 1]], float), T, src=f"P-14@{c.id}",
            UV1=uv1)


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
