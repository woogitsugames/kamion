"""Road surface meshes: chain ribbons (carriageway + side strips), junction patches (polar
triangulation of the CCW patch polygon) with kerb corner strips, bridge decks/abutments/piers, and the
simplified collision mesh. Coordinates: local E, N, U (metres). Triangles CCW seen from outside.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

import numpy as np

from . import standards as S
from .geom import ear_clip, polygon_area
from .network import FLUSH_FILL_MAX_M, ISLAND, MAT_FLUSH_ROAD, MEDIAN_RURAL, RURAL, URBAN, side_params, side_profile


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
            if getattr(sec_mid, "lane_edges", None):
                lanec = sec_mid.lane_coord(latv, hwv, int(c.dirn[c.idx(0.5 * (s0 + s1))]) or 1)
            elif sec_mid.oneway or sec_mid.roundabout:
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
    _wl = c.meta.get("walled")      # ADR 0146: stations of the spans proper (coated cap), not of the walled ramps
    capm = np.asarray(br, bool) if br is not None else np.zeros(len(st), bool)
    if _wl is not None:
        capm = capm & ~(c.interp(_wl.astype(float), st) > 0.5)
    kinds = {p[0] for p in params}
    # inner side of curves: compress the profile so it does not fold
    kap = c.line.curvature(st) * sgn
    zg = c.crossfall_z(st, sgn * hw)
    G = P + N * (sgn * hw)[:, None]
    # flush edge shared with another carriageway (asphalt, no kerb): its own strip, like a profile family
    if not coarse and c.side[side].get("verge") is not None:
        vg = c.side[side]["verge"]
        wl = c.meta.get("walled")
        vw = np.array([float(c.interp(vg, s)) if (p[0] == URBAN and p[2] < 0.05 and p[4] == 0 and p[1] > 0.05) else 0.0
                       for s, p in zip(st, params)])
        if br is not None:
            vw[br] = 0.0
        if wl is not None:
            vw[c.interp(wl.astype(float), st) > 0.01] = 0.0
        _emit_verge(buf, G, N * sgn, zg, np.array([p[1] for p in params]), vw, kap, hw, side == "R",
                    f"{c.id}:{side}:vg")
        nofl = vw > 0.05
    else:
        nofl = None
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
            if r and c.meta.get("gore_flush") and len(prm) > 1:
                # the station borrowed from the previous run carries the height of ANOTHER profile family. Next to
                # a paved gore (ADR 0077) that is the dropped kerb (-0.06, which side_profile reads as "default
                # ditch 0.6 m": a 0.2 m swale jumped to 0.6 m over one station = 0.5-0.7 m steep grass faces at
                # E 786 N -831, E 321 N -603, E 48 N -460) or a ditch depth used as a kerb height (a concrete fin
                # where the hidden kerb starts). The borrowed station continues this run's own height instead.
                prm[0] = (kr, prm[1][1], *prm[0][2:])
            _emit_strip(buf, G[sl], (N * sgn)[sl], zg[sl], prm, kap[sl], hw[sl], side == "R",
                        br[sl] if br is not None else None, coarse, f"{c.id}:{side}:{r}",
                        noflange=None if nofl is None else nofl[sl], capm=capm[sl])
        return
    _emit_strip(buf, G, N * sgn, zg, params, kap, hw, side == "R",
                br, coarse, c.id + ":" + side, noflange=nofl, capm=capm)


def _emit_verge(buf, G, OUT, zg, H, VW, kap_toward, hw, flip, src):
    """ADR 0110: grass strip behind a kerb without a sidewalk, from the back of the kerb top at the kerb crown
    (rising SIDEWALK_CROSSFALL outward), VW m wide per station, ending in a battered grass skirt
    (1 : VERGE_SKIRT_SLOPE, FLANGE_DEPTH deep) instead of the kerb's vertical concrete flange. Visual only (the
    collision ground behind a kerb stays the terrain). Exported inside the terrain primitives of its chunk
    (build_world.merge_verge_into_terrain): same grass, no extra draw call."""
    n = len(G)
    VW = np.asarray(VW, float).copy()
    if n < 2 or VW.max() < 0.05:
        return
    VW[VW < 0.05] = 0.0
    along = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(G, axis=0).T))])
    # ends: the strip and its skirt run out over 2 m (a strip that stopped within one station next to a dense corner
    # arc left a near-vertical grass face, terrain_walls b1)
    zero = np.where(VW <= 0.0)[0]
    dist = np.full(n, 1e9) if not len(zero) else np.abs(along[:, None] - along[zero][None, :]).min(1)
    VW = np.minimum(VW, 0.5 * dist)
    depth = np.minimum(S.FLANGE_DEPTH, 0.06 * dist)
    tw = S.KERB_TOP_W
    scale = np.ones(n)
    inside = kap_toward > 1e-6
    if inside.any():
        R = 1.0 / np.maximum(kap_toward[inside], 1e-6)
        allow = np.maximum(0.3, 0.9 * R - (hw[inside] if np.ndim(hw) else hw))
        scale[inside] = np.minimum(1.0, allow / np.maximum(tw + VW[inside] + S.FLANGE_DEPTH * S.VERGE_SKIRT_SLOPE, 1e-6))
    on = VW > 0.0
    u0 = tw * scale
    u1 = (tw + VW) * scale
    depth = np.where(on, depth, 0.0) * scale          # squeezed on the inside of a curve: shallower, same 1:2 slope
    u2 = u1 + depth * S.VERGE_SKIRT_SLOPE
    z0 = zg + H
    z1 = z0 + S.SIDEWALK_CROSSFALL * VW
    z2 = z1 - depth
    P0 = np.column_stack([G + OUT * u0[:, None], z0])
    P1 = np.column_stack([G + OUT * u1[:, None], z1])
    P2 = np.column_stack([G + OUT * u2[:, None], z2])
    # straights: one quad per run (Douglas-Peucker on the three edge lines, 1-2 cm; the kerb beside it keeps every
    # station, the hairline between them is under the tolerance, 2.5 cm)
    from .geom import dp_keep
    kp = dp_keep(P0, 0.025) | dp_keep(P1, 0.025) | dp_keep(P2, 0.03)
    P0, P1, P2, u0, u1, u2, along = P0[kp], P1[kp], P2[kp], u0[kp], u1[kp], u2[kp], along[kp]
    n = len(P0)
    T = grid_tris(n, 2, flip=flip)
    for A, B, ua, ub, fp in ((P0, P1, u0, u1, True), (P1, P2, u1, u2, False)):
        V = np.concatenate([A[:, None, :], B[:, None, :]], axis=1).reshape(-1, 3)
        UV1 = np.column_stack([np.repeat(along, 2), np.column_stack([ua, ub]).ravel()])
        # not footprint: the conformed terrain under the strip stays as it was (road edge - 0.03 m, below the crown), so
        # the footprint mask the streetscape stage reads (plantings in island holes, yards, trees) is unchanged
        buf.add("road", "verge_grass", V, V[:, :2].copy(), T, footprint=False, src=src, UV1=UV1)


# ADR 0100 (REVIEW s10-0095 P1-8): a concrete strip wider than a kerb top (walk material code 0 = curb_concrete, e.g.
# the 2 m strip north of DK8 at E -830...-770) got the kerb-top UV (u along, v across, 1 m joints) and read as streaks
# across the strip; rows wider than this are mapped in plan metres like every other horizontal surface.
KERB_TOP_UV_MAX_W = 0.4


def _emit_strip(buf, G, OUT, zg, params, kap_toward, hw, flip, br, coarse, src, noflange=None, capm=None):
    """G: gutter points (n,2), OUT: unit outward vectors (n,2) (may be miter-scaled), zg gutter z,
    params: per-point side params, kap_toward: curvature toward this side (>0 = side is inside)."""
    n = len(G)
    if n < 2:
        return
    kinds = [p[0] for p in params]
    # unify family: all points must share topology
    if len(set(kinds)) > 1:
        # ADR 0110: `h` of a rural station is its DITCH depth (0.2-0.6 m), not a kerb height: a corner between a kerbed
        # and a rural arm rose to a 0.6 m concrete wall (j:n1847317049:corner0, kerb_rise.py)
        params = [(URBAN, p[1] if p[0] == URBAN else S.KERB_HEIGHT, (p[2] if p[0] == URBAN else 0.0), p[3],
                   p[4] if p[0] == URBAN else 0) for p in params]
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
    _w = re.search(r"w(\d+)", str(src))
    cap_mat = BRIDGE_STYLES.get(_w.group(1), {}).get("cap_mat") if _w else None
    for k in range(nseg):
        mats = [pr[k][4] for pr in profs]
        # majority material; a tie goes to the one met first along the strip. `max(set(mats), ...)` broke ties by
        # str-hash order = PYTHONHASHSEED: kerb vs sidewalk flipped between runs (ADR 0096)
        mat = max(dict.fromkeys(mats), key=mats.count)
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
        rw = max(abs(pr[k][2] - pr[k][0]) for pr in profs)   # row width over ALL stations (ADR 0100)
        if rw < 1e-6:     # vertical segment (a walk row 0 m wide at the first station only is NOT one: strip N 82)
            UV = np.column_stack([np.repeat(along, 2), np.tile([0.0, 1.0], n) * abs(profs[0][k][3] - profs[0][k][1])])
            if mat in ("sidewalk_paving", "apron_sett", "verge_grass", "shoulder_gravel"):
                mat = "curb_concrete" if mat != "verge_grass" else "verge_grass"
        elif mat == "curb_concrete" and rw <= KERB_TOP_UV_MAX_W:
            # kerb top: u along (1 m segment joints)
            UV = np.column_stack([np.repeat(along, 2), np.tile([0.0, 1.0], n) * abs(profs[0][k][2] - profs[0][k][0])])
        else:
            UV = V[:, :2].copy()
            if mat == "curb_concrete":
                # a walk strip wider than a kerb top coded as concrete (walk mat 0): the kerb texture set has 1 m
                # joints and striations along u - mapped in plan metres it still reads as streaks across the strip
                # (render b6, N 82). Paving, as the strip was before ADR 0095 and as the orthophoto shows it.
                mat = "sidewalk_paving"
        # UV1 = (metres along the edge, metres from the gutter) -> joints, dirt bands, weeds at the kerb line
        UV1 = np.column_stack([np.repeat(along, 2),
                               np.array([[profs[i][k][0] * scale[i], profs[i][k][2] * scale[i]] for i in range(n)]).ravel()])
        T = grid_tris(n, 2, flip=flip)
        vertical = rw < 1e-6
        is_flange = vertical and k == nseg - 1 and not coarse
        if is_flange and noflange is not None and len(T):
            # ADR 0110: behind a verge strip (meshing._emit_verge) the buried flange is never seen - not meshed
            # (about half of all kerb triangles of the region were flanges of kerbs without a sidewalk)
            ts = np.minimum(T.min(1) // 2, n - 2)
            both = noflange[ts] & noflange[ts + 1]
            # ADR 0123 (REVIEW s10-0117 P1-6, the lone wall of r2_fork_link_eye, third round): where a verge strip
            # starts or ends (one station with the strip, the next without: a change of profile family, a dropped
            # kerb) the 0.5 m concrete flange stood bare above the lower ground beside the road (DK8 0.5-0.7 m above
            # the link to Rondo Putry at E -353 N -134). There the flange becomes a grass batter
            # (1 : VERGE_SKIRT_SLOPE), like the skirt of the verge strip it joins.
            one = noflange[ts] ^ noflange[ts + 1]
            if one.any():
                Vg = V.copy()
                dep = np.abs(Vg[0::2, 2] - Vg[1::2, 2])
                Vg[1::2, :2] += np.asarray(OUT, float) * (dep * S.VERGE_SKIRT_SLOPE)[:, None]
                buf.add("road", "verge_grass", Vg, Vg[:, :2].copy(), T[one], footprint=False, src=src + ":vg")     # ":vg" = merged into the terrain mesh
            T = T[~(both | one)]
        # ADR 0146: coated deck cap (bridge_style `cap_mat`) on the SPANS only (`capm`: bridge and not a walled ramp;
        # Mapillary 494288258686575 on the deck: red-brown coat, 810896133189484 on the ramp: bare light concrete).
        # Kerb and fascia stay concrete. The coat keeps a lighter road film (CAP_COAT_GRIME).
        groups = [(mat, T)]
        if not coarse and not vertical and mat == "bridge_concrete" and cap_mat and capm is not None and len(T):
            ts = np.minimum(T.min(1) // 2, n - 2)
            on = capm[ts] & capm[np.minimum(ts + 1, n - 1)]
            groups = [(cap_mat, T[on]), (mat, T[~on])]
        for mat, T in groups:
            cmat = ("collision_" + ("curb" if mat == "curb_concrete" else "asphalt" if mat.startswith("road_") else
                                    "paving" if mat in ("sidewalk_paving", "apron_sett", "bridge_concrete") else
                                    "grass")) if coarse else mat
            # ADR 0123 (REVIEW s10-0117 P1-3): the top of a bridge cap (kapa: the concrete strip behind the kerb of a
            # deck or a walled ramp) carries road film in COLOR_0.r (Kamion/World PBR _VERTEX_GRIME, manifest
            # `vertex_grime` of the material): heaviest at the kerb, where spray and grit land - no extra draw call
            COL = None
            if not coarse and not vertical and mat in ("bridge_concrete", cap_mat):
                g0, g1 = S.CAP_GRIME if mat == "bridge_concrete" else S.CAP_COAT_GRIME
                COL = np.zeros((2 * n, 4))
                COL[0::2, 0], COL[1::2, 0] = g0, g1
            if not len(T):
                continue
            if br is not None and np.any(br):
                tri_st = np.minimum(T.min(1) // 2, n - 2)
                onb = br[tri_st] | br[np.minimum(tri_st + 1, n - 1)]
                buf.add(layer, cmat, V, UV, T[~onb], footprint=(not coarse and not vertical), src=src, UV1=UV1, COL=COL)
                buf.add("collision" if coarse else "bridge", cmat, V, UV, T[onb], footprint=False, src=src, UV1=UV1,
                        COL=COL)
            else:
                buf.add(layer, cmat, V, UV, T, footprint=(not coarse and not vertical and not is_flange), src=src,
                        UV1=UV1, COL=COL)


# Per-bridge look from authored overrides `kind: bridge_style` (keyed by OSM way id, set by roads.pipeline):
#   fascia        painted deck-edge band colour (red / green / None = bare concrete)
#   pier_mat      material of the round piers (bridge_concrete, pier_yellow)
#   noise_screen  transparent noise-screen panels on the deck edge ("transparent") and their height
# Default: bare concrete, round grey piers, no screen. Ground truth: CC0 photos in docs/REFERENCES.md.
BRIDGE_STYLES = {}
FASCIA_BAND_H = 0.55        # WORKING_VALUE: painted band height read off the CC0 photos (vs ~1.1 m railing)
#   screen_side   "both" (default) or "travel_right": the screen stands only on the right-hand edge in the direction
#                 of travel (the outer edge of a one-way carriageway of a dual road); the other edge keeps the railing
DEFAULT_BRIDGE_STYLE = {"fascia": None, "pier_mat": "bridge_concrete", "noise_screen": None, "screen_h": 3.0,
                        "pier_r": 0.6, "screen_side": "both"}


SCREEN_POST_M = 2.0       # post spacing of deck noise screens (m), WORKING_VALUE read off Mapillary 494288258686575
SCREEN_POST_W = 0.22      # post width along the road (m), WORKING_VALUE (HEB 200-220 class)


def screen_sides(c, style):
    """Deck edges ("L" / "R" of the chain direction) that carry the noise screen (ADR 0125)."""
    if not style.get("noise_screen"):
        return ()
    if style.get("screen_side", "both") != "travel_right":
        return ("L", "R")
    d = np.asarray(c.dirn)
    fwd = int(np.sum(d > 0)) >= int(np.sum(d < 0))        # travel runs with the chain direction
    return ("R",) if fwd else ("L",)


def bridge_style(c):
    for eid, _ in c.edges:
        w = str(eid).split(":")[0].lstrip("w")
        if w in BRIDGE_STYLES:
            return {**DEFAULT_BRIDGE_STYLE, **BRIDGE_STYLES[w]}
    return DEFAULT_BRIDGE_STYLE


def bridge_cap_w(c):
    """Width of the deck cap behind the kerb (ADR 0117): `cap_w` of the bridge_style override, else BRIDGE_CAP_W."""
    return float(bridge_style(c).get("cap_w") or S.BRIDGE_CAP_W)


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
                # ADR 0146 (REVIEW s14-0139 P2-3): `ramp_fascia` - the band on top of the retaining walls of the
                # ramps has its own colour (Mapillary 810525063224609 / 209622370971977: green on the spans over the
                # roundabout, red on the block-faced ramp walls)
                wl_ = c.meta.get("walled")
                if style.get("ramp_fascia") and wl_ is not None:
                    prt = buf.parts[-1]
                    wk = c.interp(wl_.astype(float), 0.5 * (ss[:-1] + ss[1:])) > 0.5
                    wt = np.tile(wk, 2)
                    if wt.any() and len(prt.T) == len(wt):
                        buf.add("bridge", f"bridge_fascia_{style['ramp_fascia']}", prt.V, prt.UV, prt.T[wt],
                                src=c.id + ":fascia")
                        if (~wt).any():
                            prt.T = prt.T[~wt]
                        else:
                            buf.parts.remove(prt)
            if side in screen_sides(c, style) and not hero:    # transparent noise screen on posts at the deck edge
                e = top - np.column_stack([nn0 * sgn * 0.05, np.zeros(len(ss))])
                _strip(buf, "bridge", "noise_glass_lined", e + [0, 0, 0.25], e + [0, 0, style["screen_h"]],
                       c.id + ":screen")
                # glass dust mask (Kamion/World Car Glass: film where max(|u|, |v|) > 0.58): v = 1 at the foot of the
                # sheet -> -0.25 at the top, so road spray covers the lowest ~0.9 m; u = 0 (posts hide the panel ends)
                for prt in buf.parts[-2:]:
                    k = len(prt.V) // 2
                    prt.UV = np.column_stack([np.zeros(2 * k), np.concatenate([np.ones(k), np.full(k, -0.25)])])
                run_len = float(ss[-1] - ss[0])
                # ADR 0127: H-section posts every SCREEN_POST_M, SCREEN_POST_W wide along the road (Mapillary
                # 494288258686575: ~12 posts per 25 m, flange about a quarter of the bay). Were 0.14 m every 3 m.
                for k in range(int(run_len // SCREEN_POST_M) + 1):
                    s_p = float(ss[0]) + SCREEN_POST_M * k
                    pi = np.interp(s_p, ss, np.arange(len(ss)))
                    p3 = np.array([np.interp(pi, np.arange(len(ss)), e[:, d]) for d in range(3)])
                    # ADR 0146 (REVIEW s14-0139 P2-2): H-section, not a deep square box - road-side flange
                    # SCREEN_POST_W wide + web behind it. The 0.18 m deep box showed its dark side through the glass
                    # (a ~30 px band behind every near post on 494288). Two boxes, 20 triangles per post.
                    t_p, n_p = c.line.frame(s_p)
                    pm = style.get("screen_post_mat") or "barrier_steel"
                    z0p, z1p = p3[2] - 0.05, p3[2] + style["screen_h"] + 0.1
                    box(buf, "bridge", pm, p3[:2] - n_p * sgn * 0.03, t_p, SCREEN_POST_W / 2, 0.008, z0p, z1p,
                        c.id + ":screen")
                    box(buf, "bridge", pm, p3[:2] + n_p * sgn * 0.06, t_p, 0.006, 0.09, z0p, z1p, c.id + ":screen")
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
                    # ADR 0146 r2: the block facing ends under the painted band of the cap edge. It ran up to the cap
                    # top 5 mm in front of the band, so the red band of `ramp_fascia` was never seen (slab section
                    # at E -428 N -79: ramp_wall_blocks to 135.24, bridge_fascia_red 134.69-135.26 behind it).
                    vtop = top.copy()
                    if style["fascia"] and not hero:
                        vtop[:, 2] -= FASCIA_BAND_H - 0.02
                    vbot = bot.copy()
                    vbot[:, 2] = np.minimum(vbot[:, 2], vtop[:, 2] - 0.05)
                    for layer, mat in (("bridge", "ramp_wall_blocks"), ("collision", "collision_fence")):
                        vis = layer == "bridge"
                        _strip(buf, layer, mat, (vbot if vis else bot) + off, (vtop if vis else top) + off,
                               c.id + ":ramp_wall", both=False)
                        if sgn > 0:
                            buf.parts[-1].T = buf.parts[-1].T[:, [0, 2, 1]]
        # balustrade on both cap edges (WORKING_VALUE geometry, low confidence): open steel railing =
        # handrail band at 1.0-1.1 m + mid rail at 0.45-0.60 m + posts every 2 m, set 0.15 m in from the edge
        tt, nn = c.line.frame(ss)
        # ADR 0110: no balustrade where a noise screen stands on the same edge (the screen is the edge protection; with
        # the barrier-railing that made three rail systems side by side, REVIEW s10-0100 P1-6 p0_lamp_w1101181473_eye)
        scr = screen_sides(c, style)                 # ADR 0125: an edge without a screen keeps its railing
        for side, sgn in (() if hero else tuple(x for x in (("L", 1.0), ("R", -1.0)) if x[0] not in scr)):
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


MEDIAN_FILL_MAX_GAP_M = 14.0     # WORKING_VALUE: widest gap between the inner cap edges that is filled


def build_median_fills(buf, net):
    """ADR 0146: grass median between the two carriageways of a dual road on a shared retained embankment
    (`median_fill` of a profile tie, `<region>/profile_ties.json`). Each carriageway is its own walled ramp
    (profile.mark_walled_ramps); without the fill the median was a slot down to the NMT between two retaining walls,
    and from one carriageway the other stood on a wall (Mapillary 810896133189484: both carriageways level, grass
    median with a guardrail; orthophoto 0.08 m: grass from the abutment at E -462 to the junction).
    The strip joins the inner cap edges of both chains over the tied stretch where both are walled, with an end
    wall at each end. Returns the report rows."""
    out = []
    for tie in getattr(net, "profile_ties", []) or []:
        if not tie.get("median_fill"):
            continue
        c = next((x for x in net.chains if any(str(e) == tie["chain_edge"] for e, _ in x.edges)), None)
        g = next((x for x in net.chains if any(str(e) == tie["follow_edge"] for e, _ in x.edges)), None)
        wc = None if c is None else c.meta.get("walled")
        wg = None if g is None else g.meta.get("walled")
        if wc is None or wg is None:
            out.append({"id": tie.get("id"), "filled_m": 0.0, "why": "chain not found or not walled"})
            continue
        sa = c.line.project(np.asarray(tie["from_en"], float))[0]
        sb = c.line.project(np.asarray(tie["to_en"], float))[0]
        sa, sb = min(sa, sb), max(sa, sb)

        def edge(ch, s, sgn):
            side = "L" if sgn > 0 else "R"
            kind, kh, w, depth, mat = side_params(ch, side, s)
            prof = side_profile(kind, kh, w, depth, mat)
            h = float(ch.hw_at(s))
            q = ch.line.point(s) + ch.line.frame(s)[1] * sgn * (h + prof[-1][2])
            return np.array([q[0], q[1], float(ch.crossfall_z(s, sgn * h)) + prof[-1][1]])

        A, B, low = [], [], []
        span = {}                                  # ADR 0159: filled stations per chain side (streetscape.furniture)
        for s_c in np.arange(sa, sb + 1e-6, 2.0):
            if c.interp(wc.astype(float), s_c) < 0.5:
                continue
            p = c.line.point(s_c)
            s_g, lat = g.line.project(p)
            if not (0.0 < s_g < g.length) or g.interp(wg.astype(float), s_g) < 0.5:
                continue
            sg_c = 1.0 if c.line.project(g.line.point(s_g))[1] > 0 else -1.0      # side of c that faces g
            sg_g = 1.0 if lat > 0 else -1.0                                        # side of g that faces c
            a, b = edge(c, s_c, sg_c), edge(g, s_g, sg_g)
            if not (0.3 < np.hypot(*(a[:2] - b[:2])) < MEDIAN_FILL_MAX_GAP_M):
                continue
            A.append(a); B.append(b)
            for ch, sd, sv in ((c, "L" if sg_c > 0 else "R", float(s_c)), (g, "L" if sg_g > 0 else "R", float(s_g))):
                lo_, hi_ = span.get((id(ch), sd), (sv, sv))
                span[(id(ch), sd)] = (min(lo_, sv), max(hi_, sv))
                ch.meta.setdefault("median_fill_s", {})[sd] = span[(id(ch), sd)]
            low.append(min(float(c.interp(c.meta["walled_zg"]["L" if sg_c > 0 else "R"], s_c)),
                           float(g.interp(g.meta["walled_zg"]["L" if sg_g > 0 else "R"], s_g))) - 0.5)
        if len(A) < 2:
            out.append({"id": tie.get("id"), "filled_m": 0.0, "why": "no station where both chains are walled"})
            continue
        A, B = np.array(A), np.array(B)
        n = len(A)
        V = np.concatenate([A[:, None, :], B[:, None, :]], axis=1).reshape(-1, 3)
        up = np.cross(A[1] - A[0], B[0] - A[0])[2] > 0            # (A0, A1, B0) faces up?
        T = grid_tris(n, 2, flip=False)
        t0 = V[T[0]]
        if np.cross(t0[1] - t0[0], t0[2] - t0[0])[2] < 0:
            T = T[:, [0, 2, 1]]
        src = f"{c.id}:median_fill"
        buf.add("bridge", "verge_grass", V, V[:, :2].copy(), T, src=src)
        buf.add("collision", "collision_grass", V, V[:, :2].copy(), T, src=src)
        for k, o in ((0, -1.0), (n - 1, 1.0)):                    # end walls (both windings: seen from either side)
            a, b = A[k], B[k]
            zb = min(low[k], a[2] - 0.3, b[2] - 0.3)
            W = np.array([[a[0], a[1], zb], [b[0], b[1], zb], [b[0], b[1], b[2]], [a[0], a[1], a[2]]])
            wd = float(np.hypot(*(a[:2] - b[:2])))
            UVw = np.array([[0, 0], [wd, 0], [wd, b[2] - zb], [0, a[2] - zb]])
            buf.add("bridge", "ramp_wall_blocks", W, UVw, np.array([[0, 1, 2], [0, 2, 3], [0, 2, 1], [0, 3, 2]]),
                    src=src + ":end")
        L = float(np.hypot(*np.diff(A[:, :2], axis=0).T).sum())
        out.append({"id": tie.get("id"), "filled_m": round(L, 1), "stations": n,
                    "width_m": [round(float(np.hypot(*(A - B)[:, :2].T).min()), 2),
                                round(float(np.hypot(*(A - B)[:, :2].T).max()), 2)],
                    "dz_edges_max_m": round(float(np.abs(A[:, 2] - B[:, 2]).max()), 2)})
    return out


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
        width = 2 * (hwmax + S.KERB_TOP_W + bridge_cap_w(c))
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
        if along < 0.0:
            # beside the trimmed part of the arm (the gore of a 45 m merge patch): the arm's own surface at its
            # nearest edge, not the end-section plane carried 15-40 m along a changing grade (0.18 m ridge between
            # the Putry viaduct ramp and its on-ramp, MA-012)
            sp_, lat_ = a.chain.line.project(p)
            if 1e-3 < sp_ < a.chain.length - 1e-3:
                hw_ = float(a.chain.hw_at(sp_))
                return float(a.chain.crossfall_z(sp_, float(np.clip(lat_, -hw_, hw_))))
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
        buf.add(layer, mat, V, V[:, :2].copy(), np.array(T), footprint=(layer == "road" and not coarse), src=j.id,
                UV1=None if coarse else _patch_uv1(net, j, V))
        if stats is not None:
            stats["polar"] = stats.get("polar", 0) + 1
    else:
        res = _delaunay_fill(poly, S.PATCH_COLLISION_SPACING_M if coarse else 2.5)
        if res is None:
            res = _repair_fill(poly, zb, ph, S.PATCH_COLLISION_SPACING_M if coarse else 2.5)
            if res is not None:
                V, T = res
                buf.add(layer, mat, V, V[:, :2].copy(), T, footprint=(layer == "road" and not coarse), src=j.id,
                UV1=None if coarse else _patch_uv1(net, j, V))
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
        buf.add(layer, mat, V, V[:, :2].copy(), T, footprint=(layer == "road" and not coarse), src=j.id,
                UV1=None if coarse else _patch_uv1(net, j, V))
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


def _patch_uv1(net, j, V):
    """UV1 = (lane coordinate, distance to the carriageway edge) of a junction plate, in the frame of its through
    road: the widest arm and the arm opposite to it (ADR 0110, REVIEW s10-0100 P1-2). Plates had no UV1 (the exporter
    default -1 / 5 m = no wheel paths, no gutter dirt), so every plate in a weathered carriageway read as a cleaner,
    lighter rectangle across the lanes (p0_fork_putry_eye, eye_putry_n). Vertices outside the through road keep the
    default."""
    P = np.asarray(V, float)[:, :2]
    lane = np.full(len(P), -1.0)
    edge = np.full(len(P), 5.0)
    score = np.full(len(P), np.inf)
    if not j.arms:
        return np.column_stack([lane, edge])
    hws = [float(a.chain.hw_at(float(a.s(j.trims[i])))) for i, a in enumerate(j.arms)]
    i0 = int(np.argmax(hws))
    d0 = j.arms[i0].direction(float(j.trims[i0]))
    ref = [i0]
    best = None
    for i, a in enumerate(j.arms):
        if i == i0:
            continue
        dot = float(np.dot(a.direction(float(j.trims[i])), d0))
        if dot < -0.8 and (best is None or dot < best[0]):
            best = (dot, i)
    if best is not None:
        ref.append(best[1])
    for i in ref:
        a = j.arms[i]
        c = a.chain
        d = float(j.trims[i])
        s0 = float(a.s(d))
        sec = c.section(s0, net.sec_list)
        lo, hi = (0.0, d + 5.0) if a.end == "a" else (c.length - d - 5.0, c.length)
        idx = np.where((c.line.s >= lo - 1e-6) & (c.line.s <= hi + 1e-6))[0]
        if len(idx) < 2:
            continue
        pts = c.line.p[idx]
        A, B = pts[:-1], pts[1:]
        AB = B - A
        l2 = np.maximum((AB ** 2).sum(1), 1e-12)
        t = np.clip(((P[:, None, :] - A[None]) * AB[None]).sum(2) / l2[None], 0.0, 1.0)
        C = A[None] + AB[None] * t[..., None]
        D = np.hypot(P[:, None, 0] - C[..., 0], P[:, None, 1] - C[..., 1])
        k = D.argmin(1)
        dist = D[np.arange(len(P)), k]
        cross = AB[k, 0] * (P[:, 1] - A[k, 1]) - AB[k, 1] * (P[:, 0] - A[k, 0])
        lat = np.copysign(dist, cross)
        hw = hws[i]
        if getattr(sec, "lane_edges", None):
            lc = sec.lane_coord(lat, hw, int(c.dirn[c.idx(s0)]) or 1)
        elif sec.oneway or sec.roundabout:
            lc = (lat + hw - sec.edge_strip) / max(float(sec.lane_w), 2.0)
        else:
            lc = np.abs(lat) / max(float(sec.lane_w), 2.0)
        better = (dist < score) & (dist <= hw + 0.3)
        lane[better] = np.asarray(lc, float)[better]
        edge[better] = np.maximum(hw - dist, 0.0)[better]
        score[better] = dist[better]
    return np.column_stack([lane, edge])


def _patch_mat(net, j):
    # ADR 0100 (REVIEW s10-0095 P1-6): the majority of the arms' ENGINE materials (incl. the resurfaced share,
    # standards.surface_material). Taking the raw section material made every plate between two resurfaced arms a
    # lighter worn rectangle across the carriageway (n10015785253, the bay at s 1060, the fork at s 1440).
    mats = [S.surface_material(a.chain, a.chain.section(a.s(1.0), net.sec_list)) for a in j.arms]
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
        va = A.chain.side[sideA].get("verge")
        vb = B.chain.side[sideB].get("verge")
        cv = None
        if va is not None and vb is not None and not coarse:
            va_ = float(A.chain.interp(va, float(A.s(j.trims[i]))))
            vb_ = float(B.chain.interp(vb, float(B.s(j.trims[i1]))))
            cv = va_ + (vb_ - va_) * f
        # another carriageway (not an arm of this junction) right beside the corner: the strip is flush asphalt up
        # to it. The kerb of a median that two carriageways close on used to end 3 m before they met and left a
        # slot down to the terrain (j:n10015785253, 0.5 m deep, terrain_walls QA; ADR 0076)
        gaps, rise = _corner_gaps(net, j, G, OUT, Z)
        params = [(URBAN, float(r), float(g), p[3], MAT_FLUSH_ROAD) if (p[0] == URBAN and np.isfinite(g)) else
                  ((p[0], 0.0, p[2], p[3], p[4]) if (p[0] == URBAN and p[4] == MAT_FLUSH_ROAD) else p)
                  for p, g, r in zip(params, gaps, rise)]
        fl = [p[0] == URBAN and p[4] == MAT_FLUSH_ROAD for p in params]
        nofl = None
        if cv is not None and not _patch_on_bridge(j):
            # ADR 0110: the grass behind the kerb runs round the corner / median nose too
            vw = np.array([v if (q[0] == URBAN and q[2] < 0.05 and q[4] == 0 and q[1] > 0.05) else 0.0
                           for v, q in zip(cv, params)])
            # a corner whose kerb line jumps in height (plates of two levels meeting: j:n2591872092, +-1 m between
            # stations) gets no grass - the strip would repeat the jumps as 1-2 m grass faces
            dsz = np.maximum(np.hypot(*np.diff(G, axis=0).T), 0.25)
            if len(Z) > 1 and float(np.max(np.abs(np.diff(Z)) / dsz)) > 0.15:
                vw[:] = 0.0
            _emit_verge(buf, G, OUT, Z, np.array([q[1] for q in params]), vw, kap, hwz, True, j.id + f":corner{i}:vg")
            nofl = vw > 0.05
        # the corner polyline runs CCW around the patch, outward = right of travel -> mirrored strip
        if len(set(fl)) > 1:
            # one strip per run of flush / kerbed stations sharing the boundary station (as build_side_strip): the
            # material of a strip is the majority of its stations
            cuts = [0] + [m for m in range(1, len(fl)) if fl[m] != fl[m - 1]] + [len(fl)]
            for r, (a_, b_) in enumerate(zip(cuts, cuts[1:])):
                lo = max(0, a_ - 1) if r else a_
                if b_ - lo < 2:
                    continue
                sl = slice(lo, b_)
                # the shared station of a kerbed run is a flush one: kerb height 0 there (its `h` is a rise)
                prm = [((q[0], q[1], q[2], q[3], MAT_FLUSH_ROAD) if fl[a_] else
                        ((q[0], 0.0, 0.0, q[3], 0) if q[4] == MAT_FLUSH_ROAD else q))
                       if q[0] == URBAN else q for q in params[lo:b_]]
                _emit_strip(buf, G[sl], OUT[sl], Z[sl], prm, kap[sl], hwz[sl], True, None, coarse,
                            j.id + f":corner{i}" + (f":{r}" if r else ""), noflange=None if nofl is None else nofl[sl])
        else:
            _emit_strip(buf, G, OUT, Z, params, kap, hwz, True, None, coarse, j.id + f":corner{i}", noflange=nofl)


CORNER_FILL_DZ_M = 0.15      # the neighbour's edge must be this close in height to the corner (WORKING_VALUE)


def _corner_gaps(net, j, G, OUT, Z):
    """Per corner station: (clear gap [m] to the carriageway of another ground chain lying outward of the corner and
    running along it, height of that carriageway's edge above the corner), when the gap is under FLUSH_FILL_MAX_M
    (0 where it overlaps) and the height difference under CORNER_FILL_DZ_M - the flush strip then slopes onto that
    edge. Carriageways further apart in height (ramps beside a through road: 0.4-0.5 m at j:n1883469484) keep
    their kerb. nan elsewhere."""
    from shapely import STRtree
    from shapely.geometry import LineString, Point
    if getattr(net, "_cw_tree", None) is None:
        ch = [c for c in net.chains if not c.meta.get("absorbed") and len(c.line.p) >= 2]
        net._cw_tree = (STRtree([LineString(c.line.p) for c in ch]), ch)
    tree, ch = net._cw_tree
    own = {a.chain.id for a in j.arms} | {c.id for c in getattr(j, "internal", [])}
    out = np.full(len(G), np.nan)
    rise = np.zeros(len(G))
    if _patch_on_bridge(j):
        return out, rise
    for m, (p, o) in enumerate(zip(G, OUT)):
        best = None
        for k in tree.query(Point(*p).buffer(FLUSH_FILL_MAX_M + 12.0)):
            oc = ch[int(k)]
            if oc.id in own:
                continue
            s_o, lat_o = oc.line.project(p)
            if s_o <= 1e-3 or s_o >= oc.length - 1e-3:
                continue
            io = oc.idx(s_o)
            if bool(oc.bridge[io]) or abs(float(np.dot(oc.line.t[io], o))) > 0.5:
                continue
            if float(np.dot(oc.line.point(s_o) - p, o)) <= 0.0:          # the other road is behind the corner
                continue
            hw_o = float(oc.hw_at(s_o))
            gap = max(abs(lat_o) - hw_o, 0.0)
            if gap >= FLUSH_FILL_MAX_M or (best is not None and gap >= best):
                continue
            z_o = float(oc.crossfall_z(s_o, float(np.clip(lat_o, -hw_o, hw_o))))     # its edge nearest the corner
            if abs(z_o - float(Z[m])) > CORNER_FILL_DZ_M:
                continue
            best = gap
            rise[m] = z_o - float(Z[m])
        if best is not None:
            out[m] = best
    return out, rise


# ---------------------------------------------------------------------------------------------
CULL_CARRIAGEWAY = {"road_asphalt", "road_asphalt_new", "road_concrete", "road_paving", "road_sett", "road_gravel"}
CULL_KERB = {"curb_concrete", "collision_curb"}
CULL_SIDE = {"sidewalk_paving", "verge_grass", "shoulder_gravel", "collision_paving", "collision_grass"}
CULL_RING_M = 0.30          # = consistency.KERB_RING_M: carriageway under the kerb and all around it at this radius
CULL_DZ_M = 0.8             # = consistency.DZ_M: decks / underpasses are further apart


def cull_sides_on_carriageway(buf: MeshBuf) -> dict:
    """Kerbs / side strips of one ribbon or junction corner that lie on the carriageway of another (ADR 0076).

    Where two elements overlap (a junction patch over a service road, two patches of a split junction, the gore of
    a merge) each used to keep its own kerb, so a 12-15 cm kerb ran across the neighbour's lane: wheel collider in
    Unity, the truck was launched at speed (owner 2026-11-10, MA-001 / MA-002). network.assign_sides(trims=True)
    already makes ribbon edges flush beside another carriageway; this pass removes what is left, by the same
    criterion as consistency.kerb_on_carriageway: a kerb triangle (top or face, render and collision) with a
    carriageway under its centre and under 8 points around it at CULL_RING_M; a sidewalk / verge / shoulder
    triangle with a carriageway under its centre and its three vertices. The asphalt under it stays."""
    import shapely
    polys, zs = [], []
    for p in buf.parts:
        if p.layer not in ("road", "bridge") or p.mat not in CULL_CARRIAGEWAY or len(p.T) == 0:
            continue
        tri = p.V[p.T]
        a2 = 0.5 * np.abs((tri[:, 1, 0] - tri[:, 0, 0]) * (tri[:, 2, 1] - tri[:, 0, 1])
                          - (tri[:, 2, 0] - tri[:, 0, 0]) * (tri[:, 1, 1] - tri[:, 0, 1]))
        tri = tri[a2 > 1e-4]
        if len(tri):
            polys.append(shapely.polygons(np.concatenate([tri[:, :, :2], tri[:, :1, :2]], axis=1)))
            zs.append(tri[:, :, 2].mean(1))
    out = {"kerb_tris": 0, "side_tris": 0, "parts": 0}
    if not polys:
        return out
    polys, zs = np.concatenate(polys), np.concatenate(zs)
    tree = shapely.STRtree(polys)

    def on_cw(P):
        res = np.zeros(len(P), bool)
        pi, ti = tree.query(shapely.points(P[:, :2]), predicate="intersects")
        ok = np.abs(zs[ti] - P[pi, 2]) < CULL_DZ_M
        res[np.unique(pi[ok])] = True
        return res

    ang = np.arange(8) * (math.pi / 4)
    ring = np.column_stack([np.cos(ang), np.sin(ang)]) * CULL_RING_M
    keep_parts = []
    for p in buf.parts:
        kerb, side = p.mat in CULL_KERB, p.mat in CULL_SIDE
        if (p.layer not in ("road", "bridge", "collision") or not (kerb or side) or len(p.T) == 0
                or p.src.startswith("island:")):       # authored islands lie on a carriageway by design (ADR 0077/0093)
            keep_parts.append(p)
            continue
        tri = p.V[p.T]
        cen = tri.mean(1)
        drop = on_cw(cen)
        if p.src.endswith(":vg"):
            # ADR 0110: grass behind a kerb never lies on a carriageway, not even with one vertex (a strip reaching
            # onto the lane of a merging road stood 0.13 m above its asphalt: marking_off_carriageway 2 -> 11 in b1)
            for k in range(3):
                drop |= on_cw(tri[:, k] + (cen - tri[:, k]) * 0.05)
        elif kerb:
            for o in ring:
                if not drop.any():
                    break
                q = cen.copy()
                q[:, :2] += o
                drop &= on_cw(q)
        else:
            for k in range(3):
                if not drop.any():
                    break
                drop &= on_cw(tri[:, k])
        if drop.any():
            out["kerb_tris" if kerb else "side_tris"] += int(drop.sum())
            out["parts"] += 1
            p.T = p.T[~drop]
        if len(p.T):
            keep_parts.append(p)
    buf.parts[:] = keep_parts
    return out
