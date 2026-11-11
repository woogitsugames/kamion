"""Lane / edge lines carried through junction patches, and authored painted zones (ADR 0093).

markings.py paints every chain between its junction trims, so a junction patch (15-45 m at a ramp merge, the whole
ring of a roundabout between its entries) was bare asphalt: "lanes" ended and started again, and nobody could tell
which lane continues where (REVIEW 0076 #1-#5, REVIEW 0077 #5, #7, #8).

Rule (`build`): two arms of a junction form a *through pair* when traffic can enter by one and leave by the other
with a deflection below THROUGH_DEG (ring arms of a roundabout: RING_DEG). The lines both arms carry at the patch
boundary (lane lines, centre line, edge lines; the bare carriageway edge counts as an unpainted candidate) are
matched by their lateral offset about the common axis (chain ends meet at the OSM node, authored / fork shifts are
measured off the chain end points) and joined by a cubic curve draped on the generated surface:
  lane / centre <-> lane / centre     dashed P-1 (pattern of the entry arm)
  edge <-> lane (lane gain / drop)    dashed P-1 (the line of the joining lane starts / ends in the patch)
  P-4 <-> P-4 / centre                double solid
  P-7b <-> P-7b                       solid 0.24 m; dashed P-7a (1 / 1 m) where another arm joins on that side
Nothing is painted where two through pairs cross (a real intersection box) unless the pair is a ring.

`paint_zones`: `kind: painted_zone` authored overrides - P-21 exclusion zones traced on the 0.08 m orthophoto
(polygon in region-local E/N), border line + parallel or chevron stripes, paint only. Self-intersecting / empty
polygons are rejected (overrides_stale). No P-21 is generated without such a polygon.
"""

from __future__ import annotations

import math
import zlib

import numpy as np
import shapely
from shapely.geometry import LineString, Polygon

from . import standards as S

THROUGH_DEG = 35.0          # = consistency.JUNCTION_THROUGH_DEG
RING_DEG = 80.0             # consecutive ring arms (the ring bends inside the patch)
MATCH_MAX_M = 1.9           # WORKING_VALUE: a line continues in the nearest line within just over half a lane
STEP_M = 0.5
CARRIAGEWAY = {"road_asphalt", "road_asphalt_new", "road_concrete", "road_paving", "road_sett", "road_gravel"}
P21_STRIPE_W_M = 0.5        # WORKING_VALUE: read off the 0.08 m orthophoto (ADR 0077)
P21_STRIPE_GAP_M = 1.0
P21_BORDER_W_M = 0.24       # = S.LINE_W_WIDE


def _unit(v):
    n = float(np.hypot(*v))
    return v / n if n > 1e-9 else v


def _left(v):
    return np.array([-v[1], v[0]])


def chain_lines_at(c, s, secs, s0, s1, marked_hw, lane_layout):
    from . import markings as MKf
    """[(lat, kind)] of the lines markings._build_markings paints on chain c at station s; kind `edge` = the bare
    carriageway edge (inside the edge strip) of a road without edge lines."""
    i = int(c.idx(s))
    sidx = c.sec_idx
    a_ = i
    while a_ > 0 and sidx[a_ - 1] == sidx[i]:
        a_ -= 1
    b_ = i + 1
    while b_ < len(sidx) and sidx[b_] == sidx[i]:
        b_ += 1
    sec = secs[int(sidx[i])]
    sa = max(s0, float(c.line.s[a_]))
    sb = s1 if b_ == len(sidx) else min(s1, float(c.line.s[b_ - 1]))
    hw = float(c.hw_at(s))
    hw_mid = float(c.hw_at(0.5 * (sa + sb))) if sb - sa >= 1.0 else hw
    dirn = int(c.dirn[a_]) or 1
    lat_c, bounds, _ = lane_layout(sec, hw_mid, dirn)
    out = []
    painted = []
    if sec.highway in marked_hw or sec.roundabout:
        for lat in bounds:
            out.append((float(MKf.follow_edge(sec, float(lat), hw_mid, hw, dirn)) if sec.oneway else float(lat), "lane"))
        if lat_c is not None and sec.width >= S.SEGREGATION_MIN_CARRIAGEWAY:
            out.append((float(lat_c), "P-4" if sec.lanes >= 4 else "centre"))
        painted = [(float(lat), kind) for lat, kind in MKf.edge_lines(sec, hw, dirn)]
        out += painted
    # the bare carriageway edge (inside the edge strip) on every side without a painted edge line
    le = getattr(sec, "lane_edges", None)
    for sg in (-1, 1):
        if any(lat * sg > 0 and abs(lat) > hw - 1.5 for lat, _ in painted):
            continue
        if le and sec.oneway:
            d = int(dirn) or 1
            out.append((d * (hw - le[0]) if sg * d > 0 else d * (hw - le[-1]), "edge"))
        else:
            out.append((sg * (hw - max(float(sec.edge_strip), 0.0)), "edge"))
    return out, sec


class _Top:
    """Top of the generated carriageway meshes (ground level) at a plan point."""

    def __init__(self, parts):
        from streetscape.furniture import SurfaceTop
        self.t = SurfaceTop([p for p in parts if p.layer == "road" and p.mat in CARRIAGEWAY], layers=("road",))

    def z(self, P, zref=None):
        out = np.full(len(P), np.nan)
        for k, (e, n) in enumerate(P):
            below = None if zref is None else float(zref[k] if np.ndim(zref) else zref) + 1.2
            out[k] = self.t.top(float(e), float(n), below)
        return out


def _bezier(pa, ta, pb, tb):
    L = float(np.hypot(*(pb - pa)))
    n = max(2, int(math.ceil(L / STEP_M)))
    u = np.linspace(0.0, 1.0, n + 1)[:, None]
    p1, p2 = pa + ta * (L / 3.0), pb - tb * (L / 3.0)
    return (1 - u) ** 3 * pa + 3 * (1 - u) ** 2 * u * p1 + 3 * (1 - u) * u ** 2 * p2 + u ** 3 * pb


def _emit(buf, top, Q, w, src, zref, uv1x=0.5, exposure=0.0):
    """Ribbon of width w along polyline Q (n, 2), draped; segments with a vertex off the carriageway are dropped."""
    if len(Q) < 2:
        return 0
    d = np.gradient(Q, axis=0)
    d /= np.maximum(np.hypot(d[:, 0], d[:, 1]), 1e-9)[:, None]
    nrm = np.column_stack([-d[:, 1], d[:, 0]])
    A, B = Q - nrm * (w / 2), Q + nrm * (w / 2)
    za, zb = top.z(A, zref), top.z(B, zref)
    ok = np.isfinite(za) & np.isfinite(zb)
    s = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(Q, axis=0).T))])
    V = np.concatenate([np.column_stack([A, np.nan_to_num(za) + S.MARKING_LIFT])[:, None],
                        np.column_stack([B, np.nan_to_num(zb) + S.MARKING_LIFT])[:, None]], axis=1).reshape(-1, 3)
    T = []
    for i in range(len(Q) - 1):
        if ok[i] and ok[i + 1]:
            T += [(2 * i, 2 * i + 2, 2 * i + 3), (2 * i, 2 * i + 3, 2 * i + 1)]
    if not T:
        return 0
    uv = np.column_stack([np.repeat(s, 2), np.tile([0.0, 1.0], len(Q))])
    age = (zlib.crc32(f"{src}:{Q[0][0]:.1f}:{Q[0][1]:.1f}".encode()) % 1000) / 1000.0 * 0.98
    uv1 = np.column_stack([np.full(len(V), uv1x), np.full(len(V), exposure + age)])
    buf.add("markings", "marking_white", V, uv, np.array(T), src=src, UV1=uv1)
    return len(T)


def _resample(Q, s0, s1):
    s = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(Q, axis=0).T))])
    n = max(1, int(math.ceil((s1 - s0) / STEP_M)))
    u = np.linspace(s0, s1, n + 1)
    return np.column_stack([np.interp(u, s, Q[:, 0]), np.interp(u, s, Q[:, 1])])


def _line(buf, top, Q, w, pattern, src, zref):
    total = float(np.sum(np.hypot(*np.diff(Q, axis=0).T)))
    if pattern is None:
        return _emit(buf, top, Q, w, src, zref)
    dash, gap = pattern
    n = 0
    s = gap / 2
    while s < total - 0.2:
        n += _emit(buf, top, _resample(Q, s, min(s + dash, total)), w, src, zref)
        s += dash + gap
    return n


def build(buf, net, juncs, report, marked_hw, lane_layout):
    secs = net.sec_list
    top = _Top(buf.parts)
    rep = {"junctions": 0, "pairs": 0, "lines": {}, "crossing_pairs_skipped": 0, "unmatched": 0}
    for j in juncs:
        fr = []
        for i, a in enumerate(j.arms):
            c = a.chain
            if c.meta.get("absorbed"):
                fr.append(None)
                continue
            s0, s1 = c.t_a, c.length - c.t_b
            s_end = (s0 if a.end == "a" else s1) if s1 - s0 >= 0.0 else 0.5 * (s0 + s1)
            s_end = float(np.clip(s_end, 0.0, c.length))
            lines, sec = chain_lines_at(c, s_end, secs, min(s0, s1), max(s0, s1), marked_hw, lane_layout)
            tq, _ = c.line.frame(s_end)
            out = np.asarray(tq, float) * a.lat_sign()
            end_pt = np.asarray(c.line.point(float(a.s(0.0))), float).reshape(-1)[:2]
            fast = (sec.maxspeed or 50) > 70
            fr.append({"a": a, "c": c, "s": s_end, "out": out, "end": end_pt, "lines": lines,
                       "dash": S.DASH["P-1a" if fast else "P-1b"],
                       "mouth": np.asarray(c.line.offset_point(s_end, 0.0), float).reshape(-1)[:2],
                       "z": float(c.zc(s_end))})
        pairs = []
        for i in range(len(fr)):
            for k in range(len(fr)):
                if i == k or fr[i] is None or fr[k] is None:
                    continue
                A, B = fr[i], fr[k]
                if A["a"].inbound_dirn() == -1 or B["a"].inbound_dirn() == 1:
                    continue
                if any(p[0] == k and p[1] == i for p in pairs):
                    continue                                  # two-way pair already taken the other way round
                tA, tB = -A["out"], B["out"]
                ring = A["a"].is_ring() and B["a"].is_ring()
                defl = math.degrees(math.acos(float(np.clip(np.dot(tA, tB), -1.0, 1.0))))
                if defl > (RING_DEG if ring else THROUGH_DEG):
                    continue
                axis = _bezier(A["mouth"], tA, B["mouth"], tB)
                pairs.append((i, k, ring, axis))
        if not pairs:
            continue
        crossing = set()
        for x in range(len(pairs)):
            for y in range(x + 1, len(pairs)):
                if {pairs[x][0], pairs[x][1]} & {pairs[y][0], pairs[y][1]}:
                    continue
                if LineString(pairs[x][3]).intersects(LineString(pairs[y][3])):
                    crossing |= {x, y}
        used = False
        # candidates of every pair of this junction, then one greedy pass by offset mismatch: a line of an arm is
        # continued once, a line of the exit arm is reached at most twice (the two edges of a merging wedge end in
        # one lane line) and no connection crosses one already made (two entries fanning into one exit used to
        # paint a star of crossing dashes in short patches)
        cand = []
        for pi, (i, k, ring, axis) in enumerate(pairs):
            if pi in crossing and not ring:
                rep["crossing_pairs_skipped"] += 1
                continue
            A, B = fr[i], fr[k]
            tA, tB = -A["out"], B["out"]
            nb = _left(_unit(tA + tB))
            delta = float(np.dot(B["end"] - A["end"], nb))
            sgA = 1.0 if A["a"].end == "b" else -1.0          # travel into the junction along +s at a 'b' end
            sgB = 1.0 if B["a"].end == "a" else -1.0
            for ia, (la, ka) in enumerate(A["lines"]):
                for ib, (lb, kb) in enumerate(B["lines"]):
                    if ka == "edge" and kb in ("edge", "P-7b") or kb == "edge" and ka in ("edge", "P-7b"):
                        continue
                    cost = abs(sgA * la - delta - sgB * lb)
                    if cost <= MATCH_MAX_M:
                        cand.append((cost, pi, ia, ib))
            rep["pairs"] += 1
        cand.sort()
        used_a, used_b, drawn = set(), {}, []
        for cost, pi, ia, ib in cand:
            i, k, ring, axis = pairs[pi]
            A, B = fr[i], fr[k]
            if (i, ia) in used_a:
                continue
            (la, ka), (lb, kb) = A["lines"][ia], B["lines"][ib]
            edge_like_a = ka in ("edge", "P-7b")
            # an exit line is reached by at most one lane line and, besides, by wedge edges only (two in all)
            took = used_b.get((k, ib), [])
            if len(took) >= 2 or (not edge_like_a and any(not e for e in took)):
                continue
            tA, tB = -A["out"], B["out"]
            nb = _left(_unit(tA + tB))
            sgA = 1.0 if A["a"].end == "b" else -1.0
            pa = np.asarray(A["c"].line.offset_point(A["s"], la), float).reshape(-1)[:2]
            pb = np.asarray(B["c"].line.offset_point(B["s"], lb), float).reshape(-1)[:2]
            if float(np.hypot(*(pb - pa))) < 0.6:
                used_a.add((i, ia))
                used_b.setdefault((k, ib), []).append(edge_like_a)
                continue
            Q = _bezier(pa, tA, pb, tB)
            core = LineString(Q[1:-1]) if len(Q) > 4 else LineString(Q)
            if any(core.crosses(d) for d in drawn):
                continue
            zref = np.linspace(A["z"], B["z"], len(Q))
            kinds = {ka, kb}
            src, n = None, 0
            others = [fr[m]["mouth"] for m in range(len(fr)) if m not in (i, k) and fr[m] is not None]
            # arms that merge into / diverge from this pair (they form a through pair with A or B themselves): the
            # edge line towards them is the wedge border, not a line across a side-road mouth
            partners = [fr[m]["mouth"] for m in range(len(fr)) if m not in (i, k) and fr[m] is not None
                        and any((p_[0] in (i, k) or p_[1] in (i, k)) and m in (p_[0], p_[1]) for p_ in pairs)]
            if kinds == {"P-7b"}:
                side = math.copysign(1.0, sgA * la)
                mid = Q[len(Q) // 2]
                if any(float(np.dot(m - mid, nb)) * side > 0.5 for m in partners):
                    continue
                joined = any(float(np.dot(m - mid, nb)) * side > 0.5 for m in others)
                n = _line(buf, top, Q, S.LINE_W_WIDE, S.DASH["P-7a"] if joined else None,
                          f"TL-{'P-7a' if joined else 'P-7b'}@{j.id}", zref)
                src = "P-7a" if joined else "P-7b"
            elif "P-4" in kinds:
                nq = np.gradient(Q, axis=0)
                nq /= np.maximum(np.hypot(nq[:, 0], nq[:, 1]), 1e-9)[:, None]
                nq = np.column_stack([-nq[:, 1], nq[:, 0]])
                n = sum(_line(buf, top, Q + nq * off, S.LINE_W_NARROW, None, f"TL-P-4@{j.id}", zref)
                        for off in (-0.12, 0.12))
                src = "P-4"
            else:
                n = _line(buf, top, Q, S.LINE_W_NARROW, A["dash"], f"TL-lane@{j.id}", zref)
                src = "lane"
            used_a.add((i, ia))
            used_b.setdefault((k, ib), []).append(edge_like_a)
            if src and n:
                drawn.append(core)
                rep["lines"][src] = rep["lines"].get(src, 0) + 1
                used = True
        for i, f_ in enumerate(fr):
            if f_ is not None and any(p_[0] == i for p_ in pairs):
                rep["unmatched"] += sum(1 for ia, (_, ka) in enumerate(f_["lines"]) if ka != "edge" and (i, ia) not in used_a)
        rep["junctions"] += int(used)
    report["through_lines"] = rep


# --------------------------------------------------------------------------------------------- painted zones (P-21)
def zone_polygon(o):
    """Shapely polygon of a painted_zone override, or (None, reason)."""
    pts = np.asarray(o.get("polygon_en") or [], float)
    if pts.ndim != 2 or len(pts) < 3:
        return None, "polygon_en needs >= 3 points"
    pg = Polygon(pts)
    if not pg.is_valid:
        return None, "self-intersecting polygon: " + shapely.is_valid_reason(pg)
    if pg.area < 1.0:
        return None, "polygon smaller than 1 m2"
    return pg, ""


def paint_zones(buf, overrides, report, applied, stale):
    """P-21 zones as analytic quads (roads/p21_hatch.py, ADR 0100): border ring + stripes, each quad draped in
    cells <= 0.5 m; cells with a corner off the generated carriageway are dropped (counted)."""
    from . import p21_hatch as H
    top = None
    rep = []
    for o in overrides:
        if o.get("kind") != "painted_zone":
            continue
        try:
            g = H.hatch(o)
        except ValueError as e:
            stale.append(o["id"])
            rep.append({"id": o["id"], "built": False, "note": str(e)})
            continue
        if top is None:
            top = _Top(buf.parts)
        pg = g["polygon"]
        cen = np.asarray(pg.centroid.coords[0])
        Vs, Ts, nv = [], [], 0
        lost, sink = 0, 0.0
        for q in g["border"] + g["stripes"]:
            V, T = H.drape_quad(q)
            z = top.z(V)
            ok = np.isfinite(z)
            keep = ok[T].all(1)
            lost += int((~keep).sum())
            if not keep.any():
                continue
            T = T[keep]
            # the paint plane between the draped corners must not dip under the surface (junction plates and chain
            # ribbons overlap with cm differences): sample each cell at its centroid and edge midpoints and lift the
            # cell's corners to the highest sample; a cell over a step > H.MAX_LIFT_M is dropped (paint over a step)
            P3 = V[T]
            Z3 = z[T]
            smp = np.concatenate([P3.mean(1)[:, None], 0.5 * (P3 + np.roll(P3, -1, axis=1))], axis=1)   # (m, 4, 2)
            zpl = np.concatenate([Z3.mean(1)[:, None], 0.5 * (Z3 + np.roll(Z3, -1, axis=1))], axis=1)  # paint plane there
            zs = top.z(smp.reshape(-1, 2)).reshape(len(T), 4)
            under = np.where(np.isfinite(zs), zs - zpl, 0.0).max(1)          # surface above the paint plane
            step = under > H.MAX_LIFT_M
            lost += int(step.sum())
            T, under = T[~step], np.maximum(under[~step], 0.0)
            if not len(T):
                continue
            lift = np.zeros(len(V))
            for k in range(3):
                np.maximum.at(lift, T[:, k], under)
            zl = z + lift
            sink = max(sink, float(under.max()))
            Vs.append(np.column_stack([V, np.nan_to_num(zl) + S.MARKING_LIFT]))
            Ts.append(T + nv)
            nv += len(V)
        ntri = int(sum(len(t) for t in Ts))
        if ntri:
            V3 = np.vstack(Vs)
            uv1 = np.column_stack([np.full(len(V3), 0.5), np.full(len(V3), 0.35)])
            buf.add("markings", "marking_white", V3, V3[:, :2].copy(), np.vstack(Ts), src=f"P-21@zone:{o['id']}", UV1=uv1)
            applied.append({"id": o["id"], "targets": [f"zone@{cen[0]:.0f},{cen[1]:.0f}"]})
        else:
            stale.append(o["id"])
        rep.append({"id": o["id"], "built": bool(ntri), "area_m2": round(float(pg.area), 1), "tris": ntri,
                    "tris_off_carriageway": lost, "xy": [round(float(v), 1) for v in cen], "mode": g["mode"],
                    "stripes": len(g["stripes"]), "fields_deg": g["fields"], "max_lift_m": round(sink, 4)})
    report["painted_zones"] = rep
    # other paint inside a painted zone or on an authored island is erased (a lane line of the generated ribbon
    # under the hatching of a painted lane drop; lines of the patch under an island)
    polys = []
    for o in overrides:
        if o.get("kind") == "painted_zone":
            pg, _ = zone_polygon(o)
            if pg is not None:
                polys.append(pg.buffer(-0.05))
        elif o.get("kind") == "traffic_island" and o.get("polygon_en"):
            polys.append(Polygon(np.asarray(o["polygon_en"], float)).buffer(0.10))
    erased = 0
    if polys:
        zone = shapely.union_all(polys)
        shapely.prepare(zone)
        keep = []
        for p in buf.parts:
            if p.layer == "markings" and not p.src.startswith("P-21@zone:") and len(p.T):
                lo, hi = p.V[:, :2].min(0), p.V[:, :2].max(0)
                b = zone.bounds
                if not (hi[0] < b[0] or lo[0] > b[2] or hi[1] < b[1] or lo[1] > b[3]):
                    cen = p.V[p.T].mean(1)
                    drop = shapely.contains_xy(zone, cen[:, 0], cen[:, 1])
                    if drop.any():
                        if p.src.startswith(("P-8", "P-13")):      # a cut glyph is removed whole
                            drop[:] = True
                        erased += int(drop.sum())
                        p.T = p.T[~drop]
            if len(p.T):
                keep.append(p)
        buf.parts[:] = keep
    report["paint_erased_in_zones_tris"] = erased
