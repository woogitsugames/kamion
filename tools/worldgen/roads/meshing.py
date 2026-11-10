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
from .network import ISLAND, MAT_FLUSH_ROAD, MEDIAN_RURAL, RURAL, URBAN, side_params, side_profile


@dataclass
class Part:
    layer: str          # "road", "bridge", "markings", "collision"
    mat: str
    V: np.ndarray       # (n, 3) E, N, U
    UV: np.ndarray      # (n, 2)
    T: np.ndarray       # (m, 3) int
    footprint: bool = False     # rasterised into the terrain conform (ground-level surfaces)
    src: str = ""
    UV1: np.ndarray | None = None   # (n, 2) second UV set (roads: lane coordinate, distance to edge)
    COL: np.ndarray | None = None   # (n, 4) per-vertex weathering masks (0..1)


@dataclass
class MeshBuf:
    parts: list = field(default_factory=list)

    def add(self, layer, mat, V, UV, T, footprint=False, src="", UV1=None, COL=None):
        V = np.asarray(V, float)
        T = np.asarray(T, np.int64).reshape(-1, 3)
        if len(T) == 0:
            return
        # drop degenerate triangles
        a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
        area = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)
        T = T[area > 1e-6]
        if len(T):
            self.parts.append(Part(layer, mat, V, np.asarray(UV, float), T, footprint, src,
                                   None if UV1 is None else np.asarray(UV1, float),
                                   None if COL is None else np.asarray(COL, float)))


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
    sec_mid = c.section(0.5 * (s0 + s1), net.sec_list)
    secmat = S.surface_material(c, sec_mid)
    UV1 = None
    if not coarse:
        lw = max(sec_mid.lane_w, 2.0)
        latv = lat.ravel()
        hwv = np.repeat(hw, len(q))
        if secmat == "road_concrete":
            # concrete pavement (ADR 0019): UV1 = (metres along the chain, lane-scaled metres across) so the 5 m
            # sawn joints of concrete_cast_5m_joints run across the road and longitudinal joints sit on the lane
            # lines (one 5 m texture slab = one lane width)
            UV1 = np.column_stack([np.repeat(st, len(q)), (latv + hwv - sec_mid.edge_strip) / lw * 5.0])
        else:
            # UV1 = (lane coordinate, distance to the nearer carriageway edge) for wheel-path / gutter weathering
            if sec_mid.oneway or sec_mid.roundabout:
                lanec = (latv + hwv - sec_mid.edge_strip) / lw
            else:
                lanec = np.abs(latv) / lw
            UV1 = np.column_stack([lanec, hwv - np.abs(latv)])
    # split carriageway into ground / bridge parts so bridges are not rasterised into the terrain
    tri_station = np.minimum(T.min(1) // len(q), len(st) - 2)      # station row of each quad
    on_bridge = br[tri_station] | br[np.minimum(tri_station + 1, len(st) - 1)]
    mat = "collision_asphalt" if coarse else secmat
    buf.add(layer, mat, V, UV, T[~on_bridge], footprint=not coarse, src=c.id, UV1=UV1)
    buf.add("collision" if coarse else "bridge", mat, V, UV, T[on_bridge], footprint=False, src=c.id, UV1=UV1)
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
    G = P + N * (sgn * hw)[:, None]
    # flush edge shared with another carriageway (asphalt, no kerb): its own strip, like a profile family
    kl = [(p[0], p[4] == MAT_FLUSH_ROAD) for p in params]
    if len(set(kl)) > 1 and (len(kinds - {URBAN, ISLAND}) > 0 or any(k[1] for k in kl)):
        # rural/urban mix (e.g. a bridge on a rural road): one strip per run of the same profile family,
        # sharing the boundary station so the strips meet
        cuts = [0] + [i for i in range(1, len(kl)) if kl[i] != kl[i - 1]] + [len(kl)]
        for r, (a, b) in enumerate(zip(cuts, cuts[1:])):
            lo, hi = max(0, a - 1) if r else a, b
            sl = slice(lo, hi)
            kr, fl = kl[a]
            prm = [(kr, p[1], p[2], p[3], MAT_FLUSH_ROAD if fl else (0 if p[4] == MAT_FLUSH_ROAD else p[4]))
                   for p in params[lo:hi]]
            _emit_strip(buf, G[sl], (N * sgn)[sl], zg[sl], prm, kap[sl], hw[sl], side == "R",
                        br[sl] if br is not None else None, coarse, f"{c.id}:{side}:{r}")
        return
    _emit_strip(buf, G, N * sgn, zg, params, kap, hw, side == "R",
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
    # rural ditch profiles squeezed on the inside of a curve keep their 1:1.5 slopes: depths shrink with the
    # widths (a shallower ditch), otherwise a 0.6 m ditch compressed to 40 % reads as a 55-60 deg green wall
    # (REVIEW r4 W-H5, Andersa slip lane, ADR 0033). The bottom skirt keeps its full depth.
    vscale = np.where(np.array([p[0] in (RURAL, MEDIAN_RURAL) for p in params]), scale, 1.0)
    layer = "collision" if coarse else "road"
    for k in range(nseg):
        mats = [pr[k][4] for pr in profs]
        mat = max(set(mats), key=mats.count)
        rows = []
        # grass verge skirt: battered 1:EMBANKMENT_SLOPE outward instead of a vertical flange, so a terrain node
        # left lower than the verge edge shows a grass slope, not a green wall (REVIEW r4 W-H5). Plan footprint
        # and the carriageway profile are unchanged (the skirt is not rasterised into the conform).
        batter = (not coarse and k == nseg - 1 and mat == "verge_grass"
                  and abs(profs[0][k][2] - profs[0][k][0]) < 1e-6)
        for i in range(n):
            u0, d0, u1, d1, _ = profs[i][k]
            if vscale[i] < 1.0:
                vert = abs(u1 - u0) < 1e-6 and k == nseg - 1
                d0, d1 = d0 * vscale[i], (d0 * vscale[i] + (d1 - d0)) if vert else d1 * vscale[i]
            p0 = G[i] + OUT[i] * (u0 * scale[i])
            p1 = G[i] + OUT[i] * (u1 * scale[i])
            if batter and (br is None or not br[i]):
                p1 = p1 + OUT[i] * (abs(d1 - d0) * S.EMBANKMENT_SLOPE)
            rows.append([[p0[0], p0[1], zg[i] + d0], [p1[0], p1[1], zg[i] + d1]])
        V = np.array(rows).reshape(-1, 3)
        # UV: u = along (cumulative), v = across profile
        along = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(G, axis=0).T))])
        if abs(profs[0][k][2] - profs[0][k][0]) < 1e-6:     # vertical segment
            UV = np.column_stack([np.repeat(along, 2), np.tile([0.0, 1.0], n) * abs(profs[0][k][3] - profs[0][k][1])])
            if mat in ("sidewalk_paving", "apron_sett", "verge_grass", "shoulder_gravel"):
                mat = "curb_concrete" if mat != "verge_grass" else "verge_grass"
        elif mat == "curb_concrete":                           # kerb top: u along (1 m segment joints)
            UV = np.column_stack([np.repeat(along, 2), np.tile([0.0, 1.0], n) * abs(profs[0][k][2] - profs[0][k][0])])
        else:
            UV = V[:, :2].copy()
        # UV1 = (metres along the edge, metres from the gutter) -> joints, dirt bands, weeds at the kerb line
        UV1 = np.column_stack([np.repeat(along, 2),
                               np.array([[profs[i][k][0] * scale[i], profs[i][k][2] * scale[i]] for i in range(n)]).ravel()])
        T = grid_tris(n, 2, flip=flip)
        vertical = abs(profs[0][k][2] - profs[0][k][0]) < 1e-6
        is_flange = vertical and k == nseg - 1 and not coarse
        cmat = ("collision_" + ("curb" if mat == "curb_concrete" else "asphalt" if mat.startswith("road_") else
                                "paving" if mat in ("sidewalk_paving", "apron_sett", "bridge_concrete") else
                                "grass")) if coarse else mat
        if br is not None and np.any(br):
            tri_st = np.minimum(T.min(1) // 2, n - 2)
            onb = br[tri_st] | br[np.minimum(tri_st + 1, n - 1)]
            buf.add(layer, cmat, V, UV, T[~onb], footprint=(not coarse and not vertical), src=src, UV1=UV1)
            buf.add("collision" if coarse else "bridge", cmat, V, UV, T[onb], footprint=False, src=src, UV1=UV1)
        else:
            buf.add(layer, cmat, V, UV, T, footprint=(not coarse and not vertical and not is_flange), src=src, UV1=UV1)


# Per-bridge look from authored overrides `kind: bridge_style` (keyed by OSM way id, set by roads.pipeline):
#   fascia        painted deck-edge band colour (red / green / None = bare concrete)
#   pier_mat      material of the round piers (bridge_concrete, pier_yellow)
#   noise_screen  transparent noise-screen panels on the deck edge ("transparent") and their height
# Default: bare concrete, round grey piers, no screen. Ground truth: CC0 photos in docs/REFERENCES.md.
BRIDGE_STYLES = {}
FASCIA_BAND_H = 0.55        # WORKING_VALUE: painted band height read off the CC0 photos (vs ~1.1 m railing)
DEFAULT_BRIDGE_STYLE = {"fascia": None, "pier_mat": "bridge_concrete", "noise_screen": None, "screen_h": 3.0,
                        "pier_r": 0.6}


def bridge_style(c):
    for eid, _ in c.edges:
        w = str(eid).split(":")[0].lstrip("w")
        if w in BRIDGE_STYLES:
            return {**DEFAULT_BRIDGE_STYLE, **BRIDGE_STYLES[w]}
    return DEFAULT_BRIDGE_STYLE


def _strip(buf, layer, mat, A, B, src, both=True):
    """Vertical strip between polylines A (bottom) and B (top), both windings (thin decorative parts)."""
    n = len(A)
    V = np.concatenate([A, B])
    T = [(k, k + 1, n + k + 1) for k in range(n - 1)] + [(k, n + k + 1, n + k) for k in range(n - 1)]
    T = np.array(T)
    s_ = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(A[:, :2], axis=0).T))])
    UV = np.column_stack([np.tile(s_, 2), np.concatenate([np.zeros(n), B[:, 2] - A[:, 2]])])
    buf.add(layer, mat, V, UV, T, src=src)
    if both:
        buf.add(layer, mat, V, UV, T[:, [0, 2, 1]], src=src)


def cylinder(buf, layer, mat, center_xy, r, z0, z1, src, seg=14):
    a = np.linspace(0, 2 * math.pi, seg + 1)
    ring = np.column_stack([np.cos(a), np.sin(a)]) * r + center_xy
    V = np.concatenate([np.column_stack([ring, np.full(seg + 1, z0)]), np.column_stack([ring, np.full(seg + 1, z1)])])
    n = seg + 1
    T = [(i, i + 1, n + i + 1) for i in range(seg)] + [(i, n + i + 1, n + i) for i in range(seg)]
    UV = np.column_stack([np.tile(a * r, 2), np.repeat([0.0, z1 - z0], n)])
    buf.add(layer, mat, V, UV, np.array(T), src=src)


def build_bridge_extras(buf, c, st, P, N, hw, br):
    if not br.any():
        return
    style = bridge_style(c)
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
        Ts = grid_tris(len(ss), 2, flip=True)
        if c.meta.get("walled") is not None:      # no soffit over walled ramps (hidden between the walls)
            open_ = c.interp(c.meta["walled"].astype(float), ss) < 0.5
            Ts = Ts[open_[np.minimum(Ts // 2, len(ss) - 1)].any(axis=1)]
        hero = bool(c.meta.get("hero"))    # authored viaduct asset (streetscape.hero_bridge, ADR 0067): the asset
        # brings its own girder, cornice, railing and supports; only the ramp walls below stay generated
        if not hero:
            buf.add("bridge", "bridge_soffit", V, V[:, :2], Ts, src=c.id + ":soffit")
        tt0, nn0 = c.line.frame(ss)
        for side, sgn in (("L", 1.0), ("R", -1.0)):
            bot, top = outer[side]
            off = np.column_stack([nn0 * sgn * 0.015, np.zeros(len(ss))])
            if style["fascia"] and not hero:          # painted band at the cap edge (top FASCIA_BAND_H of the edge), 1.5 cm proud;
                # below it the bare concrete edge beam, as on both CC0 photos of the Andersa viaducts
                fb = np.column_stack([bot[:, :2], np.maximum(bot[:, 2], top[:, 2] - FASCIA_BAND_H)])
                _strip(buf, "bridge", f"bridge_fascia_{style['fascia']}", fb + off, top + off + [0, 0, 0.02],
                       c.id + ":fascia", both=False)
                # winding: the strip faces outward (left side reversed)
                if sgn > 0:
                    buf.parts[-1].T = buf.parts[-1].T[:, [0, 2, 1]]
            if style["noise_screen"] and not hero:    # transparent noise screen on posts at the deck edge (both sides)
                e = top - np.column_stack([nn0 * sgn * 0.05, np.zeros(len(ss))])
                _strip(buf, "bridge", "noise_glass", e + [0, 0, 0.25], e + [0, 0, style["screen_h"]], c.id + ":screen")
                # glass dust mask (Kamion/World Car Glass: film where max(|u|, |v|) > 0.58): v = 1 at the foot of the
                # sheet -> -0.25 at the top, so road spray covers the lowest ~0.9 m; u = 0 (posts hide the panel ends)
                for prt in buf.parts[-2:]:
                    k = len(prt.V) // 2
                    prt.UV = np.column_stack([np.zeros(2 * k), np.concatenate([np.ones(k), np.full(k, -0.25)])])
                run_len = float(ss[-1] - ss[0])
                for k in range(int(run_len // 3.0) + 1):
                    s_p = float(ss[0]) + 3.0 * k
                    pi = np.interp(s_p, ss, np.arange(len(ss)))
                    p3 = np.array([np.interp(pi, np.arange(len(ss)), e[:, d]) for d in range(3)])
                    box(buf, "bridge", "barrier_steel", p3[:2] + c.line.frame(s_p)[1] * sgn * 0.06,
                        c.line.frame(s_p)[0], 0.07, 0.07, p3[2] - 0.05, p3[2] + style["screen_h"] + 0.1,
                        c.id + ":screen")
        # retaining walls of a walled ramp (profile.mark_walled_ramps): block-faced wall from the deck edge down to
        # 0.5 m below the NMT beside it, facing outward; also a collision wall
        wl = c.meta.get("walled")
        if wl is not None:
            wsel = c.interp(wl.astype(float), ss) > 0.5
            widx = np.where(wsel)[0]
            for wr in (np.split(widx, np.where(np.diff(widx) > 1)[0] + 1) if len(widx) else []):
                wr = np.arange(max(0, wr[0] - 1), min(len(ss) - 1, wr[-1] + 1) + 1)
                if len(wr) < 2:
                    continue
                for side, sgn in (("L", 1.0), ("R", -1.0)):
                    top = outer[side][1][wr].copy()
                    zg = c.interp(c.meta["walled_zg"][side], ss[wr]) - 0.5
                    bot = top.copy()
                    bot[:, 2] = np.minimum(zg, top[:, 2] - 0.3)
                    off = np.column_stack([nn0[wr] * sgn * 0.02, np.zeros(len(wr))])
                    for layer, mat in (("bridge", "ramp_wall_blocks"), ("collision", "collision_fence")):
                        _strip(buf, layer, mat, bot + off, top + off, c.id + ":ramp_wall", both=False)
                        if sgn > 0:
                            buf.parts[-1].T = buf.parts[-1].T[:, [0, 2, 1]]
        # balustrade on both cap edges (WORKING_VALUE geometry, low confidence): open steel railing =
        # handrail band at 1.0-1.1 m + mid rail at 0.45-0.60 m + posts every 2 m, set 0.15 m in from the edge
        tt, nn = c.line.frame(ss)
        for side, sgn in (() if hero else (("L", 1.0), ("R", -1.0))):
            top = outer[side][1].copy()
            top[:, :2] -= nn * sgn * 0.15
            for z0, z1, th in ((S.BRIDGE_PARAPET_H - 0.10, S.BRIDGE_PARAPET_H, 0.06), (0.45, 0.60, 0.04)):
                o = top.copy()
                i = top.copy()
                i[:, :2] -= nn * sgn * th
                for a, b in (((i, z0), (i, z1)), ((i, z1), (o, z1)), ((o, z1), (o, z0)), ((o, z0), (i, z0))):
                    A, B = a[0].copy(), b[0].copy()
                    A[:, 2] += a[1]
                    B[:, 2] += b[1]
                    V = np.concatenate([A[:, None, :], B[:, None, :]], axis=1).reshape(-1, 3)
                    buf.add("bridge", "barrier_steel", V, V[:, :2], grid_tris(len(ss), 2, flip=(side == "L")),
                            src=c.id + ":parapet")
            run_len = float(ss[-1] - ss[0])
            for k in range(int(run_len // 2.0) + 1):
                s_p = float(ss[0]) + 2.0 * k
                pi = np.interp(s_p, ss, np.arange(len(ss)))
                p3 = np.array([np.interp(pi, np.arange(len(ss)), top[:, d]) for d in range(3)])
                t2 = c.line.frame(s_p)[0]
                box(buf, "bridge", "barrier_steel", p3[:2] - c.line.frame(s_p)[1] * sgn * 0.03, t2, 0.04, 0.03,
                    p3[2], p3[2] + S.BRIDGE_PARAPET_H, c.id + ":parapet")


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
    wl = c.meta.get("walled")
    idx = np.where(c.bridge & ~wl if wl is not None else c.bridge)[0]      # walled ramps stand on their walls
    if not len(idx):
        return
    runs = np.split(idx, np.where(np.diff(idx) > 1)[0] + 1)
    for run in runs:
        sa, sb = s[run[0]], s[run[-1]]
        if sb - sa < 4:
            continue
        hwmax = float(c.hw[run].max())
        width = 2 * (hwmax + S.KERB_TOP_W + S.BRIDGE_CAP_W)
        style = bridge_style(c)
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
                for q in cols:          # round columns in pairs (CC0 photos of both Andersa viaducts)
                    zg = float(hf.sample(q[0], q[1]))
                    if zt - zg > 0.5:
                        cylinder(buf, "bridge", style["pier_mat"], q, style["pier_r"], zg - 0.5, zt, c.id + ":pier")
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
        self.internal = list(getattr(j, "internal", []))

    def on_arm(self, i, p):
        """(surface z, clear distance outside the carriageway) when p lies in the trimmed part of arm i (between the
        junction and the arm's end section, within 0.5 m of its carriageway), else None."""
        a, s, P, d, n, hw, g, z0 = self.arms[i]
        if float((p - P) @ d) >= 0.0:
            return None
        sp_, lat_ = a.chain.line.project(p)
        if not 1e-3 < sp_ < a.chain.length - 1e-3:     # beyond the chain end the projection is clamped
            return None
        hw_ = float(a.chain.hw_at(sp_))
        out = abs(lat_) - hw_
        if out >= 0.5:
            return None
        d_node = sp_ if a.end == "a" else a.chain.length - sp_          # distance from the junction node
        return float(a.chain.crossfall_z(sp_, lat_)), out, d_node

    def arm_plane(self, i, p):
        on = self.on_arm(i, p)
        if on is not None:
            return on[0]
        a, s, P, d, n, hw, g, z0 = self.arms[i]
        v = p - P
        along = float(v @ d)
        lat = float(np.clip(v @ n, -hw, hw))
        cf = float(a.chain.crossfall_z(s, lat * a.lat_sign())) - z0
        return z0 + g * along + cf

    def blend(self, p):
        """IDW of the arms' heights. Inside an arm's own (trimmed) carriageway that arm's surface dominates (weight
        from the depth inside its carriageway): long trims at forks (65-68 m at the DK8 / Putry ramp fork) and
        merges otherwise mixed the rising ramp into the through road (0.13 m step on route_start, s = 1478 m)."""
        num = den = 0.0
        for i, (a, s, P, d, n, hw, g, z0) in enumerate(self.arms):
            on = self.on_arm(i, p)
            if on is not None:
                # weight grows with the depth inside the carriageway and falls to 0 at 0.5 m outside it (continuous);
                # where two arms overlap (fork / merge) the one whose axis is nearer wins, so a ramp's crossfall at
                # its edge does not lift the through lane
                # and fades out over the last 4 m before the node, so where the route passes from one arm to the next
                # through the node their surfaces (crossfall, banking) blend instead of stepping
                z, out, d_node = on
                w = 50.0 * (0.5 - out) ** 4 * float(np.clip(d_node / 4.0, 0.02, 1.0)) ** 2
            else:
                A, B = P - n * hw, P + n * hw
                ab = B - A
                t = np.clip(float((p - A) @ ab) / max(float(ab @ ab), 1e-9), 0, 1)
                dist2 = float(np.sum((p - (A + t * ab)) ** 2))
                w = 1.0 / (dist2 + 1e-6) ** 1.5
                z = self.arm_plane(i, p)
            num += w * z
            den += w
        for c in self.internal:          # absorbed chains (e.g. the 29 m slip w606396458 inside the Bieżeństwa merge)
            sp_, lat_ = c.line.project(p)
            if not 1e-3 < sp_ < c.length - 1e-3:
                continue
            out = abs(lat_) - float(c.hw_at(sp_))
            if out >= 0.5:
                continue
            w = 50.0 * (0.5 - out) ** 4
            num += w * float(c.crossfall_z(sp_, lat_))
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
    if c is not None and coarse and float(np.max(np.hypot(*(poly - c).T))) > 15.0:
        # long collision patches (fork trims of 65-68 m): the polar fan from one centre gave long slivers whose
        # linear facets cut 5-8 cm under the blended surface (route_start s = 1422 m); boundary-conforming
        # Delaunay with interior points instead
        c = None
    if c is not None:
        rmax = float(np.max(np.hypot(*(poly - c).T)))
        K = max(1, int(math.ceil(rmax / (S.PATCH_COLLISION_SPACING_M if coarse else 2.5))))
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
        res = _delaunay_fill(poly, S.PATCH_COLLISION_SPACING_M if coarse else 2.5)
        if res is None:
            res = _repair_fill(poly, zb, ph, S.PATCH_COLLISION_SPACING_M if coarse else 2.5)
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
            # narrow patches (forks: no interior point survives the inset, boundary edges not recovered): constrained
            # Delaunay of the outline before ear clipping. Ear clipping fanned j:n1847044961 (Rondo Putry) into a
            # 23 m triangle through three near-collinear outline vertices at different heights: a 0.13 m fin standing
            # 0.2-0.45 m over the terrain (ADR 0033 v3.5.2 open point, fixed in ADR 0049)
            T = _cdt_fill(poly)
            kind = "cdt"
            if T is None:
                T = np.array(ear_clip(poly))
                kind = "earclip"
            V = np.column_stack([poly, zb])
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


def _cdt_fill(poly):
    """Constrained Delaunay of a simple outline (no Steiner points: the vertex set and heights stay the seam with the
    ribbons). Returns CCW triangles indexing `poly`, or None when the outline is invalid / a vertex is not reused."""
    import shapely
    from shapely.geometry import Polygon
    pg = Polygon(poly)
    if not pg.is_valid or pg.area < 0.05:
        return None
    try:
        g = shapely.constrained_delaunay_triangles(pg)
    except Exception:
        return None
    key = {(round(float(x), 5), round(float(y), 5)): i for i, (x, y) in enumerate(poly)}
    T = []
    for tri in getattr(g, "geoms", []):
        ids = [key.get((round(float(x), 5), round(float(y), 5))) for x, y in np.asarray(tri.exterior.coords)[:3]]
        if None in ids:
            return None
        T.append(ids)
    if not T:
        return None
    T = np.array(T)
    a, b, c = poly[T[:, 0]], poly[T[:, 1]], poly[T[:, 2]]
    cr = (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])
    T[cr < 0] = T[cr < 0][:, [0, 2, 1]]
    if abs(0.5 * np.abs(cr).sum() - pg.area) > 1e-3 * pg.area + 1e-3:
        return None
    return T


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
            T = _cdt_fill(ring)          # constrained Delaunay before ear clipping (no 23 m fins, ADR 0049)
            P2, T = ring, (T if T is not None else np.array(ear_clip(ring)))
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
