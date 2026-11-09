"""Road surface meshes: chain ribbons (carriageway + side strips), junction patches (polar
triangulation of the CCW patch polygon) with kerb corner strips, bridge decks/abutments/piers, and the
simplified collision mesh. Coordinates: local E, N, U (metres). Triangles CCW seen from outside.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from . import standards as S
from .geom import ear_clip, polygon_area
from .network import ISLAND, URBAN, side_params, side_profile


@dataclass
class Part:
    layer: str          # "road", "bridge", "markings", "collision"
    mat: str
    V: np.ndarray       # (n, 3) E, N, U
    UV: np.ndarray      # (n, 2)
    T: np.ndarray       # (m, 3) int
    footprint: bool = False     # rasterised into the terrain conform (ground-level surfaces)
    src: str = ""


@dataclass
class MeshBuf:
    parts: list = field(default_factory=list)

    def add(self, layer, mat, V, UV, T, footprint=False, src=""):
        V = np.asarray(V, float)
        T = np.asarray(T, np.int64).reshape(-1, 3)
        if len(T) == 0:
            return
        # drop degenerate triangles
        a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
        area = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)
        T = T[area > 1e-6]
        if len(T):
            self.parts.append(Part(layer, mat, V, np.asarray(UV, float), T, footprint, src))


def grid_tris(nr, nc, flip=False):
    """Triangles for an nr x nc vertex grid (row-major; rows = stations, cols = lateral)."""
    r, c = np.meshgrid(np.arange(nr - 1), np.arange(nc - 1), indexing="ij")
    a = (r * nc + c).ravel()
    b = ((r + 1) * nc + c).ravel()
    cc = ((r + 1) * nc + c + 1).ravel()
    d = (r * nc + c + 1).ravel()
    if not flip:
        t = np.concatenate([np.column_stack([a, b, cc]), np.column_stack([a, cc, d])])
    else:
        t = np.concatenate([np.column_stack([a, cc, b]), np.column_stack([a, d, cc])])
    return t


def stations(c, s0, s1, coarse=False):
    L = s1 - s0
    if L <= 0.05:
        return np.array([])
    base = 4.0 if coarse else 2.0
    ss = [s0]
    s = s0
    while s < s1 - 1e-6:
        k = abs(float(c.line.curvature(s)))
        step = base if k < 1 / 120 else (base / 2 if k < 1 / 40 else base / 4)
        s = min(s + step, s1)
        if s1 - s < step * 0.3:
            s = s1
        ss.append(s)
    return np.array(ss)


def lat_fracs(c, coarse=False):
    if coarse:
        return np.array([-1.0, 0.0, 1.0])
    return np.linspace(-1.0, 1.0, c.m_lat + 1)


# ---------------------------------------------------------------------------------------------
def build_ribbon(buf: MeshBuf, net, c, coarse=False):
    if c.meta.get("absorbed"):
        return
    s0, s1 = c.t_a, c.length - c.t_b
    st = stations(c, s0, s1, coarse)
    if len(st) < 2:
        return
    layer = "collision" if coarse else "road"
    P = c.line.point(st)
    _, N = c.line.frame(st)
    hw = c.hw_at(st)
    br = c.interp(c.bridge.astype(float), st) > 0.5
    q = lat_fracs(c, coarse)
    lat = hw[:, None] * q[None, :]
    XY = P[:, None, :] + N[:, None, :] * lat[..., None]
    Z = c.crossfall_z(np.repeat(st, len(q)), lat.ravel()).reshape(len(st), len(q))
    V = np.concatenate([XY, Z[..., None]], axis=2).reshape(-1, 3)
    UV = V[:, :2].copy()
    T = grid_tris(len(st), len(q))
    secmat = c.section(0.5 * (s0 + s1), net.sec_list).surface_mat
    # split carriageway into ground / bridge parts so bridges are not rasterised into the terrain
    tri_station = np.minimum(T.min(1) // len(q), len(st) - 2)      # station row of each quad
    on_bridge = br[tri_station] | br[np.minimum(tri_station + 1, len(st) - 1)]
    mat = "collision_asphalt" if coarse else secmat
    buf.add(layer, mat, V, UV, T[~on_bridge], footprint=not coarse, src=c.id)
    buf.add("collision" if coarse else "bridge", mat, V, UV, T[on_bridge], footprint=False, src=c.id)
    # sides
    for side, sgn in (("L", 1.0), ("R", -1.0)):
        build_side_strip(buf, c, st, side, sgn, P, N, hw, br, coarse)
    if not coarse:
        build_bridge_extras(buf, c, st, P, N, hw, br)
    # dead-end skirts (not at tile-boundary cuts)
    for end, s in (("a", s0), ("b", s1)):
        node = c.node_a if end == "a" else c.node_b
        if net.nodes[node]["deg"] == 1 and not net.nodes[node]["boundary"] and not coarse:
            i = 0 if end == "a" else len(st) - 1
            top = V.reshape(len(st), len(q), 3)[i]
            bot = top.copy()
            bot[:, 2] -= S.FLANGE_DEPTH
            VV = np.concatenate([top, bot])
            n = len(q)
            tt = [(k, n + k, n + k + 1) for k in range(n - 1)] + [(k, n + k + 1, k + 1) for k in range(n - 1)]
            tt = np.array(tt)
            if end == "b":
                tt = tt[:, [0, 2, 1]]
            buf.add("road", "curb_concrete", VV, VV[:, :2], tt, src=c.id + ":deadend")


def _profile_rows(kind, h, w, depth, mat, coarse):
    prof = side_profile(kind, h, w, depth, mat)
    if coarse:
        prof = prof[:-1]          # no flange in collision
    return prof


def build_side_strip(buf, c, st, side, sgn, P, N, hw, br, coarse):
    params = [side_params(c, side, s) for s in st]
    kinds = {p[0] for p in params}
    # inner side of curves: compress the profile so it does not fold
    kap = c.line.curvature(st) * sgn
    zg = c.crossfall_z(st, sgn * hw)
    _emit_strip(buf, P + N * (sgn * hw)[:, None], N * sgn, zg, params, kap, hw, side == "R",
                br, coarse, c.id + ":" + side)


def _emit_strip(buf, G, OUT, zg, params, kap_toward, hw, flip, br, coarse, src):
    """G: gutter points (n,2), OUT: unit outward vectors (n,2) (may be miter-scaled), zg gutter z,
    params: per-point side params, kap_toward: curvature toward this side (>0 = side is inside)."""
    n = len(G)
    if n < 2:
        return
    kinds = [p[0] for p in params]
    # unify family: all points must share topology
    if len(set(kinds)) > 1:
        params = [(URBAN, p[1], (p[2] if p[0] == URBAN else 0.0), p[3], p[4] if p[0] == URBAN else 0) for p in params]
    profs = [_profile_rows(*p, coarse) for p in params]
    nseg = len(profs[0])
    # fold protection
    umax = np.array([pr[-1][2] for pr in profs])
    scale = np.ones(n)
    inside = kap_toward > 1e-6
    if inside.any():
        R = 1.0 / np.maximum(kap_toward[inside], 1e-6)
        allow = np.maximum(0.3, 0.9 * R - hw[inside] if np.ndim(hw) else 0.9 * R - hw)
        scale[inside] = np.minimum(1.0, allow / np.maximum(umax[inside], 1e-6))
    layer = "collision" if coarse else "road"
    for k in range(nseg):
        mats = [pr[k][4] for pr in profs]
        mat = max(set(mats), key=mats.count)
        rows = []
        for i in range(n):
            u0, d0, u1, d1, _ = profs[i][k]
            p0 = G[i] + OUT[i] * (u0 * scale[i])
            p1 = G[i] + OUT[i] * (u1 * scale[i])
            rows.append([[p0[0], p0[1], zg[i] + d0], [p1[0], p1[1], zg[i] + d1]])
        V = np.array(rows).reshape(-1, 3)
        # UV: u = along (cumulative), v = across profile
        along = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(G, axis=0).T))])
        if abs(profs[0][k][2] - profs[0][k][0]) < 1e-6:     # vertical segment
            UV = np.column_stack([np.repeat(along, 2), np.tile([0.0, 1.0], n) * abs(profs[0][k][3] - profs[0][k][1])])
            if mat in ("sidewalk_paving", "apron_sett", "verge_grass", "shoulder_gravel"):
                mat = "curb_concrete" if mat != "verge_grass" else "verge_grass"
        else:
            UV = V[:, :2].copy()
        T = grid_tris(n, 2, flip=flip)
        vertical = abs(profs[0][k][2] - profs[0][k][0]) < 1e-6
        is_flange = vertical and k == nseg - 1 and not coarse
        cmat = ("collision_" + ("curb" if mat == "curb_concrete" else "paving" if mat in
                                ("sidewalk_paving", "apron_sett", "bridge_concrete") else "grass")) if coarse else mat
        if br is not None and np.any(br):
            tri_st = np.minimum(T.min(1) // 2, n - 2)
            onb = br[tri_st] | br[np.minimum(tri_st + 1, n - 1)]
            buf.add(layer, cmat, V, UV, T[~onb], footprint=(not coarse and not vertical), src=src)
            buf.add("collision" if coarse else "bridge", cmat, V, UV, T[onb], footprint=False, src=src)
        else:
            buf.add(layer, cmat, V, UV, T, footprint=(not coarse and not vertical and not is_flange), src=src)


def build_bridge_extras(buf, c, st, P, N, hw, br):
    if not br.any():
        return
    idx = np.where(br)[0]
    # contiguous runs
    runs = np.split(idx, np.where(np.diff(idx) > 1)[0] + 1)
    for run in runs:
        if len(run) < 2:
            continue
        i0, i1 = max(0, run[0] - 1), min(len(st) - 1, run[-1] + 1)
        sel = np.arange(i0, i1 + 1)
        ss = st[sel]
        outer = {}
        for side, sgn in (("L", 1.0), ("R", -1.0)):
            pts, tops = [], []
            for s, p, nn, h in zip(ss, P[sel], N[sel], hw[sel]):
                kind, kh, w, depth, mat = side_params(c, side, s)
                prof = side_profile(kind, kh, w, depth, mat)
                u_end = prof[-1][2]
                zg = float(c.crossfall_z(s, sgn * h))
                q = p + nn * sgn * (h + u_end)
                pts.append([q[0], q[1], zg + prof[-1][3]])          # fascia bottom
                tops.append([q[0], q[1], zg + prof[-1][1]])         # cap outer top
            outer[side] = (np.array(pts), np.array(tops))
        # deck soffit: from right bottom to left bottom, facing down
        Lb, Rb = outer["L"][0], outer["R"][0]
        V = np.concatenate([Rb[:, None, :], Lb[:, None, :]], axis=1).reshape(-1, 3)
        buf.add("bridge", "bridge_concrete", V, V[:, :2], grid_tris(len(ss), 2, flip=True), src=c.id + ":soffit")
        # parapets (balustrade as a solid low-poly band 0.25 m thick, 1.10 m high) on both cap edges
        for side, sgn in (("L", 1.0), ("R", -1.0)):
            top = outer[side][1]
            _, nn = c.line.frame(ss)
            inner = top.copy()
            inner[:, :2] -= nn * sgn * 0.25
            hi_o = top.copy(); hi_o[:, 2] += S.BRIDGE_PARAPET_H
            hi_i = inner.copy(); hi_i[:, 2] += S.BRIDGE_PARAPET_H
            for a, b in ((inner, hi_i), (hi_i, hi_o), (hi_o, top)):
                V = np.concatenate([a[:, None, :], b[:, None, :]], axis=1).reshape(-1, 3)
                buf.add("bridge", "barrier_steel", V, V[:, :2], grid_tris(len(ss), 2, flip=(side == "L")),
                        src=c.id + ":parapet")


def box(buf, layer, mat, center_xy, along, half_l, half_w, z0, z1, src):
    """Vertical box: footprint rectangle (along = unit vector), from z0 up to z1."""
    a = np.asarray(along, float)
    n = np.array([-a[1], a[0]])
    c = np.asarray(center_xy, float)
    corners = [c - a * half_l - n * half_w, c + a * half_l - n * half_w, c + a * half_l + n * half_w,
               c - a * half_l + n * half_w]
    V, T = [], []
    for i in range(4):
        p, q = corners[i], corners[(i + 1) % 4]
        b = len(V)
        V += [[p[0], p[1], z0], [q[0], q[1], z0], [q[0], q[1], z1], [p[0], p[1], z1]]
        T += [(b, b + 1, b + 2), (b, b + 2, b + 3)]
    b = len(V)
    V += [[p[0], p[1], z1] for p in corners]
    T += [(b, b + 1, b + 2), (b, b + 2, b + 3)]
    V = np.array(V)
    buf.add(layer, mat, V, np.column_stack([V[:, 0] + V[:, 2], V[:, 1] + V[:, 2]]), np.array(T), src=src)


def build_bridge_supports(buf, c, hf, ground_footprint, report):
    """Abutments at both ends of each bridge run and piers every <= BRIDGE_PIER_SPACING (low confidence)."""
    if not c.bridge.any() or c.meta.get("absorbed"):
        return
    s = c.line.s
    idx = np.where(c.bridge)[0]
    runs = np.split(idx, np.where(np.diff(idx) > 1)[0] + 1)
    for run in runs:
        sa, sb = s[run[0]], s[run[-1]]
        if sb - sa < 4:
            continue
        hwmax = float(c.hw[run].max())
        width = 2 * (hwmax + S.KERB_TOP_W + S.BRIDGE_CAP_W)
        for s_end in (sa, sb):
            p = c.line.point(s_end)
            t, _ = c.line.frame(s_end)
            zt = float(c.zc(s_end)) - S.BRIDGE_DECK_THICKNESS
            zg = float(hf.sample(p[0], p[1]))
            box(buf, "bridge", "bridge_concrete", p, t, 0.6, width / 2, min(zg, zt) - 1.0, zt, c.id + ":abutment")
        span = sb - sa
        npier = int(math.floor(span / S.BRIDGE_PIER_SPACING))
        placed = 0
        for k in range(1, npier + 1):
            s0 = sa + span * k / (npier + 1)
            for shift in (0, 4, -4, 8, -8, 12, -12):
                sp_ = s0 + shift
                p = c.line.point(sp_)
                t, nn = c.line.frame(sp_)
                cols = [p + nn * f * hwmax * 0.6 for f in (-1, 1)]
                if ground_footprint is not None and any(ground_footprint(q) for q in cols):
                    continue
                zt = float(c.zc(sp_)) - S.BRIDGE_DECK_THICKNESS
                for q in cols:
                    zg = float(hf.sample(q[0], q[1]))
                    if zt - zg > 0.5:
                        box(buf, "bridge", "bridge_concrete", q, t, S.BRIDGE_PIER_W / 2, S.BRIDGE_PIER_W / 2,
                            zg - 0.5, zt, c.id + ":pier")
                placed += 1
                break
        report.append({"chain": c.id, "span_m": round(span, 1), "piers": placed, "confidence": "low",
                       "note": "deck height interpolated between abutments; piers placed by rule (no data)"})


# ---------------------------------------------------------------------------------------------
class PatchHeight:
    """Height inside a junction patch: inverse-distance blend of the arms' end-section planes."""

    def __init__(self, j):
        self.arms = []
        for i, a in enumerate(j.arms):
            t = j.trims[i]
            s = float(a.s(t))
            c = a.chain
            P = c.line.point(s)
            d = a.direction(t)
            n = np.array([-d[1], d[0]])
            hw = float(c.hw_at(s))
            g = float(c.grade(s)) * a.lat_sign()
            self.arms.append((a, s, P, d, n, hw, g, float(c.zc(s))))

    def arm_plane(self, i, p):
        a, s, P, d, n, hw, g, z0 = self.arms[i]
        v = p - P
        along = float(v @ d)
        lat = float(np.clip(v @ n, -hw, hw))
        cf = float(a.chain.crossfall_z(s, lat * a.lat_sign())) - z0
        return z0 + g * along + cf

    def blend(self, p):
        num = den = 0.0
        for i, (a, s, P, d, n, hw, g, z0) in enumerate(self.arms):
            A, B = P - n * hw, P + n * hw
            ab = B - A
            t = np.clip(float((p - A) @ ab) / max(float(ab @ ab), 1e-9), 0, 1)
            dist2 = float(np.sum((p - (A + t * ab)) ** 2))
            w = 1.0 / (dist2 + 1e-6) ** 1.5
            num += w * self.arm_plane(i, p)
            den += w
        return num / den

    def boundary_z(self, j, p, tag):
        if tag[0] == "end":
            _, i, q = tag
            a, s, P, d, n, hw, g, z0 = self.arms[i]
            return float(a.chain.crossfall_z(s, q * hw * a.lat_sign()))
        if tag[0] == "gutter":
            _, i, dd, side = tag
            a = j.arms[i]
            s = float(a.s(dd))
            hw = float(a.chain.hw_at(s))
            return float(a.chain.crossfall_z(s, side * hw * a.lat_sign()))
        return self.blend(p)


def _kernel(poly):
    """Kernel of a CCW polygon (intersection of the inner half-planes of all edges), convex or empty."""
    lo, hi = poly.min(0) - 1, poly.max(0) + 1
    K = [np.array([lo[0], lo[1]]), np.array([hi[0], lo[1]]), np.array([hi[0], hi[1]]), np.array([lo[0], hi[1]])]
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        e = b - a
        if np.hypot(*e) < 1e-9:
            continue

        def side(p):
            return e[0] * (p[1] - a[1]) - e[1] * (p[0] - a[0])
        out = []
        m = len(K)
        for k in range(m):
            p, q = K[k], K[(k + 1) % m]
            sp_, sq = side(p), side(q)
            if sp_ >= 0:
                out.append(p)
            if (sp_ >= 0) != (sq >= 0):
                t = sp_ / (sp_ - sq)
                out.append(p + t * (q - p))
        K = out
        if len(K) < 3:
            return None
    return np.array(K)


def _star_center(poly):
    cands = []
    K = _kernel(poly)
    if K is not None and abs(polygon_area(K)) > 1e-4:
        cands.append(K.mean(axis=0))
    cands.append(poly.mean(axis=0))
    for c in cands:
        nxt = np.roll(poly, -1, axis=0)
        cr = (poly[:, 0] - c[0]) * (nxt[:, 1] - c[1]) - (poly[:, 1] - c[1]) * (nxt[:, 0] - c[0])
        if (cr > 1e-9).all():
            return c
    return None


def build_patch(buf, net, j, coarse=False, stats=None):
    bnd = j.boundary
    if len(bnd) < 3:
        return
    if coarse:
        keep = []
        for k, (p, tag) in enumerate(bnd):
            if tag[0] == "end" and abs(tag[2]) not in (0.0, 1.0):
                continue
            if tag[0] in ("gutter", "arc") and k % 2 == 1:
                continue
            keep.append((p, tag))
        bnd = keep
    ph = PatchHeight(j)
    poly = np.array([p for p, _ in bnd])
    zb = np.array([ph.boundary_z(j, p, tag) for p, tag in bnd])
    mat = "collision_asphalt" if coarse else _patch_mat(net, j)
    layer = "collision" if coarse else ("bridge" if _patch_on_bridge(j) else "road")
    c = _star_center(poly)
    if c is not None:
        rmax = float(np.max(np.hypot(*(poly - c).T)))
        K = max(1, int(math.ceil(rmax / (6.0 if coarse else 2.5))))
        V = [np.array([c[0], c[1], ph.blend(c)])]
        rings = []
        for k in range(1, K + 1):
            f = k / K
            ring = []
            for p, z in zip(poly, zb):
                q = c + (p - c) * f
                ring.append([q[0], q[1], z if k == K else ph.blend(q)])
            rings.append(ring)
        n = len(poly)
        V = np.array([V[0]] + [v for r in rings for v in r])
        T = []
        for i in range(n):
            T.append((0, 1 + i, 1 + (i + 1) % n))
        for k in range(K - 1):
            b0, b1 = 1 + k * n, 1 + (k + 1) * n
            for i in range(n):
                i1 = (i + 1) % n
                T.append((b0 + i, b1 + i, b1 + i1))
                T.append((b0 + i, b1 + i1, b0 + i1))
        buf.add(layer, mat, V, V[:, :2].copy(), np.array(T), footprint=(layer == "road" and not coarse), src=j.id)
        if stats is not None:
            stats["polar"] = stats.get("polar", 0) + 1
    else:
        res = _delaunay_fill(poly, 6.0 if coarse else 2.5)
        if res is None:
            res = _repair_fill(poly, zb, ph, 6.0 if coarse else 2.5)
            if res is not None:
                V, T = res
                buf.add(layer, mat, V, V[:, :2].copy(), T, footprint=(layer == "road" and not coarse), src=j.id)
                if stats is not None:
                    stats["repaired"] = stats.get("repaired", 0) + 1
                    stats.setdefault("repaired_ids", []).append(j.id)
                import shapely
                from shapely.geometry import Polygon
                outline = shapely.make_valid(Polygon(poly)).boundary
                build_corner_strips(buf, net, j, bnd, zb, coarse, outline=outline)
                return
        if res is not None:
            P2, T = res
            V = np.column_stack([P2, np.concatenate([zb, [ph.blend(q) for q in P2[len(poly):]]])])
            kind = "delaunay"
        else:
            T = np.array(ear_clip(poly))
            V = np.column_stack([poly, zb])
            kind = "earclip"
        buf.add(layer, mat, V, V[:, :2].copy(), T, footprint=(layer == "road" and not coarse), src=j.id)
        if stats is not None:
            stats[kind] = stats.get(kind, 0) + 1
            if kind == "earclip":
                stats.setdefault("earclip_ids", []).append(j.id)
    # kerb corner strips
    build_corner_strips(buf, net, j, bnd, zb, coarse)


def _delaunay_fill(poly, spacing):
    """Boundary-conforming fill of a non-star polygon: Delaunay of boundary + interior grid points,
    triangles kept if their centroid is inside. Returns None if any boundary edge is not recovered."""
    from scipy.spatial import Delaunay
    import shapely
    from shapely.geometry import Polygon
    pg = Polygon(poly)
    if not pg.is_valid or pg.area < 0.5:
        return None
    lo, hi = poly.min(0), poly.max(0)
    gx = np.arange(lo[0] + spacing / 2, hi[0], spacing)
    gy = np.arange(lo[1] + spacing / 2, hi[1], spacing)
    G = np.array([(x, y) for y in gy for x in gx]) if len(gx) and len(gy) else np.zeros((0, 2))
    if len(G):
        inner = pg.buffer(-0.6 * spacing)
        m = shapely.contains_xy(inner, G[:, 0], G[:, 1]) if not inner.is_empty else np.zeros(len(G), bool)
        G = G[m]
    P2 = np.vstack([poly, G]) if len(G) else poly.copy()
    try:
        tri = Delaunay(P2)
    except Exception:
        return None
    T = tri.simplices
    cen = P2[T].mean(1)
    keep = shapely.contains_xy(pg.buffer(1e-6), cen[:, 0], cen[:, 1])
    T = T[keep]
    # orientation CCW
    a, b, c = P2[T[:, 0]], P2[T[:, 1]], P2[T[:, 2]]
    cr = (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])
    T[cr < 0] = T[cr < 0][:, [0, 2, 1]]
    edges = set()
    for t in T:
        for u, v in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            edges.add((min(u, v), max(u, v)))
    n = len(poly)
    for i in range(n):
        u, v = i, (i + 1) % n
        if (min(u, v), max(u, v)) not in edges:
            return None
    return P2, T


def _repair_fill(poly, zb, ph, spacing):
    """Self-intersecting patch outline (overlapping forks / dense clusters): fill the valid union of
    its lobes. Seam vertices that end up on the outline keep their exact heights; the rest overlaps the
    ribbons (no crack, possible overlap) and is listed in the QA report as `repaired`."""
    import shapely
    from shapely.geometry import Polygon
    fixed = shapely.make_valid(Polygon(poly))
    geoms = [g for g in getattr(fixed, "geoms", [fixed]) if g.geom_type == "Polygon" and g.area > 0.3]
    if not geoms:
        return None
    exact = {(round(p[0], 3), round(p[1], 3)): z for p, z in zip(poly, zb)}
    Vs, Ts, base = [], [], 0
    for g in sorted(geoms, key=lambda g: -g.area):
        ring = np.array(g.exterior.coords)[:-1]
        if polygon_area(ring) < 0:
            ring = ring[::-1]
        res = _delaunay_fill(ring, spacing)
        if res is None:
            P2, T = ring, np.array(ear_clip(ring))
        else:
            P2, T = res
        if len(T) == 0:
            continue
        z = np.array([exact.get((round(q[0], 3), round(q[1], 3)), None) for q in P2], dtype=object)
        z = np.array([float(v) if v is not None else ph.blend(q) for v, q in zip(z, P2)])
        Vs.append(np.column_stack([P2, z]))
        Ts.append(np.asarray(T) + base)
        base += len(P2)
    if not Vs:
        return None
    return np.vstack(Vs), np.vstack(Ts)


def _patch_mat(net, j):
    mats = [a.chain.section(a.s(1.0), net.sec_list).surface_mat for a in j.arms]
    return max(sorted(set(mats)), key=mats.count)


def _patch_on_bridge(j):
    return all(bool(a.chain.bridge[a.chain.idx(a.s(j.trims[i]))]) for i, a in enumerate(j.arms))


def _outward(j, p, tag, nxt_tag=None):
    if tag[0] in ("end", "gutter"):
        i = tag[1]
        a = j.arms[i]
        side = 1.0 if (tag[0] == "end" and tag[2] > 0) or (tag[0] == "gutter" and tag[3] > 0) else -1.0
        d = tag[2] if tag[0] == "gutter" else j.trims[i]
        dirv = a.direction(d)
        n = np.array([-dirv[1], dirv[0]])
        return n * side
    corner = j.corners[tag[1]]
    if corner.kind in ("fillet", "nose") and corner.center is not None:
        v = corner.center - p
        nv = np.hypot(*v)
        return v / nv if nv > 1e-9 else np.array([0.0, 0.0])
    return None


def build_corner_strips(buf, net, j, bnd, zb, coarse, outline=None):
    n = len(bnd)
    # indices of arm end-left (start of corner) and next arm end-right (end of corner)
    starts = [k for k, (_, t) in enumerate(bnd) if t[0] == "end" and t[2] == 1.0]
    for k0 in starts:
        i = bnd[k0][1][1]
        seq = [k0]
        k = (k0 + 1) % n
        while not (bnd[k][1][0] == "end" and bnd[k][1][2] == -1.0):
            seq.append(k)
            k = (k + 1) % n
            if len(seq) > n:
                break
        seq.append(k)
        i1 = bnd[k][1][1]
        G = np.array([bnd[q][0] for q in seq])
        if outline is not None:
            import shapely
            d = shapely.distance(outline, shapely.points(G))
            if np.mean(d < 0.5) < 0.8:      # corner swallowed by an overlapping neighbour: no kerb
                continue
        Z = np.array([zb[q] for q in seq])
        OUT = []
        for q in seq:
            o = _outward(j, bnd[q][0], bnd[q][1])
            OUT.append(o)
        # straight joins: miter of neighbours
        for m in range(len(OUT)):
            if OUT[m] is None:
                a_ = next((OUT[x] for x in range(m - 1, -1, -1) if OUT[x] is not None), None)
                b_ = next((OUT[x] for x in range(m + 1, len(OUT)) if OUT[x] is not None), None)
                if a_ is None or b_ is None:
                    OUT[m] = a_ if a_ is not None else b_
                else:
                    OUT[m] = (a_ + b_) / max(1.0 + float(a_ @ b_), 0.2)
        OUT = np.array(OUT)
        A, B = j.arms[i], j.arms[i1]
        sideA = "L" if A.end == "a" else "R"     # arm-left in chain terms
        sideB = "R" if B.end == "a" else "L"     # arm-right in chain terms
        pa = side_params(A.chain, sideA, float(A.s(j.trims[i])))
        pb = side_params(B.chain, sideB, float(B.s(j.trims[i1])))
        along = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(G, axis=0).T))])
        f = along / max(along[-1], 1e-9)
        params = []
        for ff in f:
            if pa[0] == pb[0]:
                params.append((pa[0], pa[1] + (pb[1] - pa[1]) * ff, pa[2] + (pb[2] - pa[2]) * ff,
                               pa[3] + (pb[3] - pa[3]) * ff, pa[4] if ff < 0.5 else pb[4]))
            else:
                params.append(pa if ff < 0.5 else pb)
        # fold protection on arcs: limit outward extent to 0.8 R
        kap = np.zeros(len(seq))
        hwz = np.zeros(len(seq))
        for m, q in enumerate(seq):
            tag = bnd[q][1]
            if tag[0] == "arc":
                corner = j.corners[tag[1]]
                if corner.kind in ("fillet", "nose") and corner.R > 0:
                    kap[m] = 1.0 / (0.8 / 0.9 * corner.R)
        # the corner polyline runs CCW around the patch, outward = right of travel -> mirrored strip
        _emit_strip(buf, G, OUT, Z, params, kap, hwz, True, None, coarse, j.id + f":corner{i}")
