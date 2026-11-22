"""Road surface decals that are placed by rule (layer 'markings', below the paint): asphalt repair patches
and oil stains. Both lie on the road surface (crossfall + vertical profile; patches on a 2.5 x 2 m grid and never
across the crown of a two-way road, where the surface is not planar) and are
lifted LESS than the markings so they never z-fight with them:
    patch  DECAL_LIFT_PATCH (2 mm)  <  oil  DECAL_LIFT_OIL (3.5 mm)  <  paint MARKING_LIFT (6 mm).

Patches (`decal_patch`): 0-3 per 50 m of carriageway, never on a grid: per 50 m window the count is drawn from
(0.45, 0.30, 0.17, 0.08) (WORKING_VALUE, older industrial streets), position, length 1.2-7 m, width (a full
lane, a wheel path 0.8-1.4 m, or a small 0.6-1.5 m square), rotation +-6 deg and age (UV1.x: 0 fresh/black ..
1 old/grey) are hashed from the chain id + window. Bridges and roundabout rings are skipped. ADR 0194: the count is scaled
by road class (PATCH_RATE_CLASS) and junction approaches (JUNCTION_ZONE_M), and wheel-path repairs sit in a wheel path.
Oil (`decal_oil`): only where vehicles stand: the 2-8 m in front of the stop position of inbound lanes at
signalised junctions, roundabout entries and minor arms of priority junctions (gate and parking stains are
added by streetscape.life / gate). Each stain is an irregular 9-gon 0.25-0.6 m with radial UV (centre 0.5).
"""

from __future__ import annotations

import hashlib
import math

import numpy as np

from . import standards as S
from .markings import RANK, lane_layout
from .network import lane_w_of

LIFT_PATCH = 0.002
LIFT_OIL = 0.0035

# ADR 0194 (REVIEW s19-0179 P2 "ten sam brud wszędzie"): repairs follow the traffic, not a uniform rate.
# Expected-count multiplier per Polish road class (A/S/GP: younger, heavier pavement and frequent resurfacing; Z/L/D:
# older municipal and service streets, utility trenches) - WORKING_VALUE, judged against P11-076 (Dywizjonu 303: no
# repairs) and P11-129 (hospital access road: several patches).
PATCH_RATE_CLASS = {"A": 0.35, "S": 0.35, "GP": 0.55, "G": 0.85, "Z": 1.0, "L": 1.2, "D": 1.3}
# Junction approaches carry braking / turning shear and the utility crossings: more repairs within this distance of a
# junction-trimmed chain end, fewer mid-block (WORKING_VALUE).
JUNCTION_ZONE_M = 30.0
JUNCTION_BOOST = 1.8
MIDBLOCK_RATE = 0.75
# Wheel-path repairs sit in a wheel path of a lane: +-WHEEL_PATH_FRAC of the lane width from its centre (the same
# 0.26 / 0.74 lane coordinate as the polished wheel paths of Kamion/World PBR _ROADWEAR); the outer (kerb-side)
# path ruts more under heavy axles.
WHEEL_PATH_FRAC = 0.24
OUTER_PATH_SHARE = 0.65


# ADR 0323 (critic wave 6 pkt 2.2: "nikt tedy nigdy nie jezdzil"): pavement condition varies along a road. One hashed
# state per CONDITION_LEN_M of a chain: sound / average / distressed (share, multiplier of the patch and crack rates).
# WORKING_VALUE - no pavement-condition data (SOSN / DSN) in the repo; judged in the DW671 frames.
CONDITION_LEN_M = 250.0
CONDITION_STATES = ((0.30, 0.25), (0.45, 1.0), (0.25, 2.4))
# Bitumen-sealed cracks ("zalewki"): soft dark bands of the existing `decal_tyre` material (UV0 = metres along, 0..1
# across; UV1 = (-length, strength): negative length = short end fades, strength >= 2.5 = solid band). Lift between
# the patches and the oil, so the paint (6 mm, opaque, earlier queue) stays on top where a line crosses a seal.
LIFT_SEAL = 0.003
SEAL_MAT = "decal_seal"
WP_MAT = "decal_tyre"
# r2 (render r1, DW671: 1 crack per 140 m of road and 7-12 cm bands at alpha 0.67 read as nothing from the cab):
# overband 12-20 cm of geometry (visible core 7-12 cm), own nearly opaque material, rates x 3.6 / x 2.5.
SEAL_W_M = (0.12, 0.20)             # geometry width; the soft profile of the material leaves ~60 % of it dark
HAIRLINE_W_M = 0.06                 # unsealed crack: thin, broken up by the material's mottling (strength < 1.5)
TRANSVERSE_PER_50M = 2.0            # thermal cracks across the carriageway at condition 1.0 (WORKING_VALUE)
LONGITUDINAL_PER_50M = 1.0          # centre-joint / edge / wheel-path cracks starting per 50 m (WORKING_VALUE)
PATCH_DENSITY = 1.8                 # r2: multiplier of the ADR 0194 patch rates (r1: 147 patches on 9.9 km, none in frame)
SEAL_CLASS_RATE = {"A": 0.25, "S": 0.25, "GP": 0.6, "G": 1.0, "Z": 1.0, "L": 1.1, "D": 1.1}
SEAL_SURFACES = ("road_asphalt",)   # worn asphalt only: not the resurfaced share, setts, concrete, gravel


def hf(*key):
    return int(hashlib.sha1(":".join(str(k) for k in key).encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def _surf(c, s, lat, lift):
    p = c.line.offset_point(s, lat)
    z = c.crossfall_z(s, lat) + lift
    return np.column_stack([p, z])


def patch(buf, c, s_c, lat_c, length, width, rot, age, src):
    """Rectangle in the chain frame (s along, lat across) rotated by `rot`, subdivided on a 2.5 x 2 m grid."""
    hw = float(c.hw_at(s_c))
    nu = max(1, int(math.ceil(length / 2.5)))       # surface is planar across a side; vertical curve is slight
    nv = max(1, int(math.ceil(width / 2.0)))
    U, Vv = np.meshgrid(np.linspace(-length / 2, length / 2, nu + 1), np.linspace(-width / 2, width / 2, nv + 1))
    cr, sr = math.cos(rot), math.sin(rot)
    ds = U * cr - Vv * sr
    dl = U * sr + Vv * cr
    s = s_c + ds
    lat = np.clip(lat_c + dl, -hw + 0.05, hw - 0.05)
    P = _surf(c, s.ravel(), lat.ravel(), LIFT_PATCH)
    T = []
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i
            b, cc, d = a + 1, a + nu + 2, a + nu + 1
            T += [(a, b, cc), (a, cc, d)]
    T = np.array(T)
    # winding: chain frame (s, lat) is right-handed seen from above -> CCW faces up
    uv = np.column_stack([U.ravel() + length / 2, Vv.ravel() + width / 2])
    uv1 = np.column_stack([np.full(len(P), age), np.full(len(P), hf(src, "seed"))])
    buf.add("markings", "decal_patch", P, uv, T, src=src, UV1=uv1)


def condition(c, s):
    """Pavement condition multiplier of the stretch of chain c around station s (ADR 0323)."""
    u = hf(c.id, int(s // CONDITION_LEN_M), "cond")
    acc = 0.0
    for share, mult in CONDITION_STATES:
        acc += share
        if u < acc:
            return mult
    return CONDITION_STATES[-1][1]


def _meander(n, step, key, amp):
    """Low-frequency lateral wander (m) of a crack sampled at n points `step` apart: three hashed sines, wavelengths
    1.2-9 m, plus a little per-point jitter - a crack is never a ruler line."""
    x = np.arange(n) * step
    out = np.zeros(n)
    for k, (lo, hi, w) in enumerate(((5.0, 9.0, 0.6), (2.5, 4.5, 0.3), (1.2, 2.2, 0.1))):
        wl = lo + hf(*key, "wl", k) * (hi - lo)
        out += w * np.sin(x / wl * 2 * math.pi + hf(*key, "ph", k) * 6.283)
    out += (np.array([hf(*key, "j", i) for i in range(n)]) - 0.5) * 0.35
    return out * amp


def seal_band(buf, c, s, lat, width, strength, src):
    """Soft band along the chain-frame polyline (s, lat): vertices on the road surface (crossfall + profile)."""
    s = np.asarray(s, float)
    lat = np.asarray(lat, float)
    if len(s) < 2:
        return 0
    C = c.line.offset_point(s, lat)
    t = np.gradient(C, axis=0)
    t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-9)
    nn = np.column_stack([-t[:, 1], t[:, 0]])
    w = np.broadcast_to(np.asarray(width, float), (len(C),))[:, None]
    A, B = C - nn * w / 2, C + nn * w / 2
    z = np.asarray(c.crossfall_z(s, lat), float) + LIFT_SEAL        # 5 cm half width: the surface height of the axis
    m = len(C)
    V = np.vstack([np.column_stack([A, z]), np.column_stack([B, z])])
    ss = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(C, axis=0).T))])
    T = np.array([(i, i + 1, m + i + 1) for i in range(m - 1)] + [(i, m + i + 1, m + i) for i in range(m - 1)])
    uv = np.column_stack([np.tile(ss, 2), np.repeat([0.0, 1.0], m)])
    uv1 = np.column_stack([np.full(2 * m, -ss[-1]), np.full(2 * m, strength)])
    buf.add("markings", SEAL_MAT, V, uv, T, src=src, UV1=uv1)
    return len(T)


def seal_cracks(buf, net, cnt):
    """ADR 0323: sealed (and a few open) cracks of worn asphalt carriageways, by rule and hashed per 50 m window:
    transverse thermal cracks across the carriageway or one half of it, longitudinal cracks along the centre joint of
    two-way roads, 0.3-0.7 m inside the carriageway edge and along a wheel path. Rates scale with the road class and
    the pavement condition of the stretch; bridges, roundabouts, construction sections and junction plates have none."""
    secs = net.sec_list
    n_t = n_l = tris = 0
    for c in net.chains:
        if c.meta.get("absorbed") or c.roundabout:
            continue
        s0, s1 = c.t_a + 2.0, c.length - c.t_b - 2.0
        if s1 - s0 < 12.0:
            continue
        sec_mid = c.section(0.5 * (s0 + s1), secs)
        if S.surface_material(c, sec_mid) not in SEAL_SURFACES:
            continue
        cls_rate = SEAL_CLASS_RATE.get(sec_mid.cls, 1.0)
        for w0 in np.arange(s0, s1, 50.0):
            w1 = min(w0 + 50.0, s1)
            key = (c.id, round(float(w0), 1), "seal")
            rate = cls_rate * condition(c, 0.5 * (w0 + w1)) * (w1 - w0) / 50.0
            # ---- transverse
            for i in range(int(math.floor(TRANSVERSE_PER_50M * rate + hf(*key, "nt")))):
                sc = float(w0 + hf(*key, i, "ts") * (w1 - w0))
                if c.bridge[c.idx(sc)]:
                    continue
                sec = c.section(sc, secs)
                if getattr(sec, "construction", False):
                    continue
                hw = float(c.hw_at(sc))
                u = hf(*key, i, "span")
                lo, hi = -hw + 0.06, hw - 0.06
                if u > 0.6 and not sec.oneway:               # one half of a two-way road only
                    lo, hi = (0.0, hi) if hf(*key, i, "half") < 0.5 else (lo, 0.0)
                elif u > 0.85:                                # a crack that dies out before the far edge
                    hi = lo + (hi - lo) * (0.45 + 0.4 * hf(*key, i, "part"))
                n = max(3, int(math.ceil((hi - lo) / 0.35)) + 1)
                lat = np.linspace(lo, hi, n)
                skew = (hf(*key, i, "skew") - 0.5) * 0.18     # +-5 deg off square
                ss = sc + (lat - lat[0]) * skew + _meander(n, 0.35, key + (i, "t"), 0.16)
                ss = np.clip(ss, s0 - 1.0, s1 + 1.0)
                sealed = hf(*key, i, "sealed") < 0.7
                wd = SEAL_W_M[0] + hf(*key, i, "w") * (SEAL_W_M[1] - SEAL_W_M[0]) if sealed else HAIRLINE_W_M
                tris += seal_band(buf, c, ss, lat, wd, 2.6 if sealed else 1.3, f"seal:t:{c.id}:{w0:.0f}:{i}")
                n_t += 1
            # ---- longitudinal
            for i in range(int(math.floor(LONGITUDINAL_PER_50M * rate + hf(*key, "nl")))):
                sa = float(w0 + hf(*key, i, "ls") * (w1 - w0))
                length = 8.0 + hf(*key, i, "ll") ** 2 * 45.0
                sb = min(sa + length, s1)
                if sb - sa < 4.0:
                    continue
                n = int(math.ceil((sb - sa) / 0.6)) + 1
                ss = np.linspace(sa, sb, n)
                if any(bool(c.bridge[c.idx(float(x))]) for x in ss[::8]):
                    continue
                sec = c.section(0.5 * (sa + sb), secs)
                if getattr(sec, "construction", False):
                    continue
                hw = np.asarray(c.hw_at(ss), float)
                kind = hf(*key, i, "lk")
                if kind < 0.4 and not sec.oneway:             # centre construction joint
                    base = np.zeros(n)
                    amp = 0.05
                elif kind < 0.8:                              # edge crack, 0.3-0.7 m inside the carriageway edge
                    sgn = 1.0 if hf(*key, i, "side") < 0.5 else -1.0
                    base = sgn * (hw - (0.3 + 0.4 * hf(*key, i, "eo")))
                    amp = 0.12
                else:                                         # along a wheel path
                    base = np.full(n, wheel_path_lat(c, sec, float(hw[n // 2]), key + (i,)))
                    amp = 0.10
                lat = np.clip(base + _meander(n, 0.6, key + (i, "l"), amp), -hw + 0.06, hw - 0.06)
                sealed = hf(*key, i, "lsealed") < 0.65
                wd = SEAL_W_M[0] + hf(*key, i, "lw") * (SEAL_W_M[1] - SEAL_W_M[0]) if sealed else HAIRLINE_W_M
                tris += seal_band(buf, c, ss, lat, wd, 2.6 if sealed else 1.3, f"seal:l:{c.id}:{w0:.0f}:{i}")
                n_l += 1
    cnt["seal_cracks"] = {"transverse": n_t, "longitudinal": n_l, "tris": int(tris)}


# ADR 0323 (critic wave 6 pkt 2.3): wheel paths of a compact roundabout. The junction plate carried the lane coordinate
# of the arm axes (straight, interpolated over 2.5 m triangles): parallel dark stripes that ran on under the splitter
# islands. The plate now has no shader wheel paths (meshing._patch_uv1); the polished tracks are soft `decal_tyre`
# bands along the lines the vehicles drive: arm lane -> designed entry / exit lane (compact_roundabout.lay_lanes) ->
# ring axis, and one track round the ring. Two bands per track, WP_GAUGE_HALF_M either side (= the 0.24 lane-width
# offset of the ribbon wheel paths at a 3.5 m lane), broken up by the material's mottling (strength < 1.5).
WP_GAUGE_HALF_M = 0.84
WP_BAND_W_M = 0.80
WP_STRENGTH = 0.9            # WORKING_VALUE: alpha 0.45 x 0.9 over 0.08 asphalt ~ the ribbon wheel-path darkening
WP_RING_STRENGTH = 0.7       # the ring polishes less evenly (every vehicle takes its own radius)
WP_STEP_M = 0.5
LIFT_WP = 0.0025


def _smooth_polyline(Q, win=5, step=WP_STEP_M):
    Q = np.asarray(Q, float)
    if len(Q) < 3:
        return Q
    d = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(Q, axis=0).T))])
    keep = np.concatenate([[True], np.diff(d) > 1e-6])
    Q, d = Q[keep], d[keep]
    if len(Q) < 3 or d[-1] < 2 * step:
        return Q
    x = np.linspace(0.0, d[-1], max(3, int(math.ceil(d[-1] / step)) + 1))
    R = np.column_stack([np.interp(x, d, Q[:, 0]), np.interp(x, d, Q[:, 1])])
    k = np.ones(win) / win
    pad = win // 2
    for a in range(2):
        col = np.concatenate([np.full(pad, R[0, a]), R[:, a], np.full(pad, R[-1, a])])
        sm = np.convolve(col, k, mode="valid")
        sm[0], sm[-1] = R[0, a], R[-1, a]
        R[:, a] = sm
    return R


def _wp_band(buf, top, Q, strength, src, zref, closed=False):
    """One soft band along Q, draped on the carriageway top; segments with a vertex off the carriageway are dropped."""
    Q = np.asarray(Q, float)
    if len(Q) < 2:
        return 0
    t = np.gradient(Q, axis=0)
    t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-9)
    nn = np.column_stack([-t[:, 1], t[:, 0]])
    A, B = Q - nn * WP_BAND_W_M / 2, Q + nn * WP_BAND_W_M / 2
    za, zb = top.z(A, zref), top.z(B, zref)
    ok = np.isfinite(za) & np.isfinite(zb)
    m = len(Q)
    V = np.vstack([np.column_stack([A, np.nan_to_num(za) + LIFT_WP]), np.column_stack([B, np.nan_to_num(zb) + LIFT_WP])])
    T = []
    for i in range(m - 1):
        if ok[i] and ok[i + 1]:
            T += [(i, i + 1, m + i + 1), (i, m + i + 1, m + i)]
    if not T:
        return 0
    ss = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(Q, axis=0).T))])
    if closed:      # no end fades on a loop: the material fades over 2.5 m / 4 m from u = 0 / u = length
        u, length = ss + 10.0, ss[-1] + 30.0
    else:
        u, length = ss, -ss[-1]            # negative length = short end fades (0.65 / 0.9 m)
    uv = np.column_stack([np.tile(u, 2), np.repeat([0.0, 1.0], m)])
    uv1 = np.column_stack([np.full(2 * m, length), np.full(2 * m, strength)])
    buf.add("markings", WP_MAT, V, uv, np.array(T), src=src, UV1=uv1)
    return len(T)


def compact_wheel_paths(buf, net, juncs, cnt):
    from .through_lines import _Top
    secs = net.sec_list
    top = None
    tracks = tris = 0
    for j in juncs:
        spec = getattr(j, "compact", None)
        if spec is None:
            continue
        top = top or _Top(buf.parts)
        ring_nodes = {x for c in spec.ring for x in (c.node_a, c.node_b)}
        zref = float(np.mean([float(c.zc(0.5 * c.length)) for c in spec.ring])) if spec.ring else None
        for f in spec.feeders:
            if f.node_a in ring_nodes and f.node_b in ring_nodes:
                continue
            far = f.node_b if f.node_a in ring_nodes else f.node_a
            P = np.asarray(f.line.p if f.node_a == far else f.line.p[::-1], float)
            Q = P
            ai = next((i for i, a in enumerate(j.arms) if a.node == far), None)
            if ai is not None and len(P) >= 2:
                arm = j.arms[ai]
                O = P[0]
                d = -np.asarray(arm.direction(0.0), float)          # along the arm axis towards the ring
                nl = np.array([-d[1], d[0]])
                x, y = (P - O) @ d, (P - O) @ nl
                sg = 1.0 if float(np.median(y[len(y) // 3:])) >= 0 else -1.0
                s1 = float(arm.s(1.0))
                sec = arm.chain.section(s1, secs)
                hw = float(arm.chain.hw_at(s1))
                dirn = int(arm.chain.dirn[arm.chain.idx(s1)]) or 1
                _, _, lanes = lane_layout(sec, hw, dirn)
                cand = [-lat * arm.lat_sign() for lat in list(lanes["fwd"]) + list(lanes["bwd"])]
                cand = [c_ for c_ in cand if c_ * sg > 0.05]
                off = min(cand, key=abs) * sg if cand else 0.5 * float(lane_w_of(sec, hw))
                r = np.hypot(*(P - spec.center).T)
                wgt = np.clip((r - (spec.r_out + 1.0)) / 4.0, 0.0, 1.0)
                y2 = y + (sg * np.maximum(np.abs(y), off) - y) * wgt
                head = O + np.outer(x, d) + np.outer(y2, nl)
                trim = float(j.trims[ai])
                tt = np.arange(trim + 0.3, 0.2, -WP_STEP_M)
                stub = O - np.outer(tt, d) + nl * sg * off
                Q = np.vstack([stub, head]) if len(tt) else head
            Q = _smooth_polyline(Q)
            if len(Q) < 4:
                continue
            t = np.gradient(Q, axis=0)
            t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-9)
            nn = np.column_stack([-t[:, 1], t[:, 0]])
            for k, sgn in enumerate((-1.0, 1.0)):
                tris += _wp_band(buf, top, Q + nn * sgn * WP_GAUGE_HALF_M, WP_STRENGTH * (0.85 + 0.3 * hf(f.id, k, "wps")),
                                 f"wheelpath:{spec.id}:{f.id}:{k}", zref)
            tracks += 1
        if spec.w_ring >= 2 * WP_GAUGE_HALF_M + WP_BAND_W_M + 0.4:
            n = max(24, int(math.ceil(2 * math.pi * spec.r_axis / WP_STEP_M)))
            ang = np.linspace(0.0, 2 * math.pi, n + 1)
            for k, sgn in enumerate((-1.0, 1.0)):
                rr = spec.r_axis + sgn * WP_GAUGE_HALF_M
                Q = spec.center + rr * np.column_stack([np.cos(ang), np.sin(ang)])
                tris += _wp_band(buf, top, Q, WP_RING_STRENGTH, f"wheelpath:{spec.id}:ring:{k}", zref, closed=True)
            tracks += 1
    if tracks:
        cnt["compact_wheel_paths"] = {"tracks": tracks, "tris": int(tris)}


def stain(buf, P0, z_of, r, key, src):
    """Irregular 9-gon around P0 (E, N); z_of(points) gives the surface height (already including the lift)."""
    n = 9
    ang = np.linspace(0, 2 * math.pi, n + 1)[:-1] + hf(key, "rot") * 6.283
    rad = r * (0.7 + 0.6 * np.array([hf(key, "r", k) for k in range(n)]))
    stretch = 1.0 + hf(key, "st") * 0.8
    pts = np.column_stack([np.cos(ang) * rad * stretch, np.sin(ang) * rad])
    ca, sa = math.cos(hf(key, "a") * 3.14), math.sin(hf(key, "a") * 3.14)
    pts = pts @ np.array([[ca, sa], [-sa, ca]])
    V2 = np.vstack([[0.0, 0.0], pts]) + P0
    Z = z_of(V2)
    V = np.column_stack([V2, Z])
    T = np.array([(0, 1 + k, 1 + (k + 1) % n) for k in range(n)])
    rr = max(rad.max() * stretch, 1e-3)
    uv = np.vstack([[0.5, 0.5], 0.5 + 0.5 * (V2[1:] - P0) / rr])
    # UV1.y = stain seed: the engine picks one of the 4 cells of the oil_stain_alpha atlas (ADR 0019)
    uv1 = np.column_stack([np.zeros(len(V)), np.full(len(V), hf(key, "cell"))])
    buf.add("markings", "decal_oil", V, uv, T, src=src, UV1=uv1)


GULLY_SPACING_M = 35.0        # WORKING_VALUE: street gullies every 30-40 m along kerbed carriageways
# ADR 0237 / R6-034 (review of PR #65): frame of a D400 kerb-side gully 620 x 420 mm (manufacturer's data sheet; the
# sheet's other variant is 500 x 500). Was 0.50 x 0.60 WORKING_VALUE. Parameter only: one quad per gully as before.
GULLY_SIZE = (0.42, 0.62)     # m; (across, along): long side along the kerb


def gullies(buf, net, report):
    """Road gullies at the kerb (odwodnienie, r4 brief): every ~GULLY_SPACING_M on kerbed edges, on the low side of
    one-way carriageways and on both sides of crowned two-way ones; grate in the gutter 0.05 m off the kerb face."""
    from .network import side_params, URBAN, ISLAND
    n = 0
    for c in net.chains:
        if c.meta.get("absorbed") or c.roundabout:
            continue
        s0, s1 = c.t_a + 3.0, c.length - c.t_b - 3.0
        if s1 - s0 < 10.0:
            continue
        sec = c.section(0.5 * (s0 + s1), net.sec_list)
        for side, sgn in (("L", 1.0), ("R", -1.0)):
            for k, s in enumerate(np.arange(s0 + hf(c.id, side, "g0") * GULLY_SPACING_M, s1, GULLY_SPACING_M)):
                s = float(s)
                if c.bridge[c.idx(s)]:
                    continue
                kind, h, w, depth, mat = side_params(c, side, s)
                if kind not in (URBAN, ISLAND) or h < 0.08:
                    continue
                hw = float(c.hw_at(s))
                if sec.oneway and float(c.crossfall_z(s, sgn * hw)) > float(c.crossfall_z(s, -sgn * hw)):
                    continue                                   # high side of a one-way carriageway
                lat = sgn * (hw - 0.05 - GULLY_SIZE[0] / 2)
                ds, dl = GULLY_SIZE[1] / 2, GULLY_SIZE[0] / 2
                ss = np.array([s - ds, s + ds, s + ds, s - ds])
                ll = np.array([lat - dl, lat - dl, lat + dl, lat + dl])
                P = _surf(c, ss, ll, LIFT_PATCH)
                T = np.array([(0, 1, 2), (0, 2, 3)])
                buf.add("markings", "drain_grate", P, [[0, 0], [1, 0], [1, 1], [0, 1]], T, src=f"gully:{c.id}:{side}:{k}")
                n += 1
    report["gullies"] = n


def wheel_path_lat(c, sec, hw, key):
    """ADR 0194: lateral offset of a wheel path of a hashed lane. Lanes are counted from the right edge strip like
    the trench patches; on two-way roads the kerb-side path of each half is the outer one."""
    lw = max(float(lane_w_of(sec, hw)), 2.0)
    nl = max(1, int(round((2 * hw - 2 * sec.edge_strip) / lw)))
    lane = int(hf(*key, "wl") * nl)
    centre = -hw + sec.edge_strip + (lane + 0.5) * lw
    outward = -1.0 if (sec.oneway or centre < 0) else 1.0        # towards the nearer kerb
    side = outward if hf(*key, "wp") < OUTER_PATH_SHARE else -outward
    return centre + side * WHEEL_PATH_FRAC * lw + (hf(*key, "wj") - 0.5) * 0.3


def build(buf, net, juncs, report):
    cnt = {"patches": 0, "oil": 0}
    gullies(buf, net, cnt)
    secs = net.sec_list
    for c in net.chains:
        if c.meta.get("absorbed") or c.roundabout:
            continue
        if S.surface_material(c, c.section(0.5 * (c.t_a + c.length - c.t_b), secs)) == "road_asphalt_new":
            continue                     # resurfaced recently (ADR 0019): no repair patches yet
        s0, s1 = c.t_a + 1.0, c.length - c.t_b - 1.0
        if s1 - s0 < 8.0:
            continue
        cls_rate = PATCH_RATE_CLASS.get(c.section(0.5 * (s0 + s1), secs).cls, 1.0)
        for w0 in np.arange(s0, s1, 50.0):
            w1 = min(w0 + 50.0, s1)
            key = (c.id, round(float(w0), 1))
            u = hf(*key, "n")
            k = 0 if u < 0.45 else 1 if u < 0.75 else 2 if u < 0.92 else 3
            # ADR 0194: scale by class and by the share of the window inside a junction approach zone
            jz = (np.clip(min(w1, s0 + JUNCTION_ZONE_M) - w0, 0, None) + np.clip(w1 - max(w0, s1 - JUNCTION_ZONE_M), 0, None))
            jshare = min(float(jz) / max(w1 - w0, 1e-6), 1.0)
            rate = cls_rate * (JUNCTION_BOOST * jshare + MIDBLOCK_RATE * (1.0 - jshare))
            rate *= PATCH_DENSITY * condition(c, 0.5 * (w0 + w1))   # ADR 0323: sound / average / distressed stretches
            kf = k * rate * (w1 - w0) / 50.0
            k = int(math.floor(kf + hf(*key, "frac")))
            for i in range(k):
                sc = w0 + hf(*key, i, "s") * (w1 - w0)
                if c.bridge[c.idx(sc)]:
                    continue
                sec = c.section(sc, secs)
                if getattr(sec, "construction", False):
                    continue             # ADR 0215: never opened to traffic - no repair patches
                hw = float(c.hw_at(sc))
                kind = hf(*key, i, "kind")
                if kind < 0.35:              # full-lane trench / overlay patch
                    width = min(float(lane_w_of(sec, hw)) * (0.9 + 0.2 * hf(*key, i, "w")), 2 * hw - 0.2)
                    length = 1.2 + hf(*key, i, "l") * 5.8
                    nl = max(1, sec.lanes)
                    lane = int(hf(*key, i, "lane") * nl)
                    lat = -hw + sec.edge_strip + (lane + 0.5) * float(lane_w_of(sec, hw))
                elif kind < 0.7:             # wheel-path patch (ADR 0194: in a wheel path of a lane)
                    width = 0.8 + hf(*key, i, "w") * 0.6
                    length = 2.0 + hf(*key, i, "l") * 5.0
                    if hf(*key, i, "strip") < 0.3:
                        # ADR 0323: long strip overlay along a rutted wheel path (Commons cs7403215, DW671: dark
                        # strips of 10-30 m along the lane); follows the chain on the 2.5 m grid of patch()
                        length = 8.0 + hf(*key, i, "l") * 17.0
                    lat = wheel_path_lat(c, sec, hw, key + (i,))
                else:                        # small square pothole repair (ADR 0194: 60 % in a wheel path)
                    width = 0.6 + hf(*key, i, "w") * 0.9
                    length = width * (0.8 + hf(*key, i, "l") * 0.8)
                    if hf(*key, i, "inwp") < 0.6:
                        lat = wheel_path_lat(c, sec, hw, key + (i,))
                    else:
                        lat = (hf(*key, i, "lat") * 2 - 1) * max(hw - 0.8, 0.2)
                if abs(lat) + width / 2 > hw - 0.05:
                    lat = math.copysign(max(hw - 0.05 - width / 2, 0.0), lat)
                if width > 2 * hw - 0.1:
                    continue
                if not sec.oneway and abs(lat) < width / 2 + 0.4:   # keep two-way patches off the crown
                    lat = math.copysign(width / 2 + 0.4, lat if lat != 0 else 1.0)
                    if abs(lat) + width / 2 > hw - 0.05:
                        continue
                rot = (hf(*key, i, "rot") - 0.5) * math.radians(12)
                patch(buf, c, sc, lat, length, width, rot, hf(*key, i, "age"), f"patch:{c.id}:{w0:.0f}:{i}")
                cnt["patches"] += 1
    # oil at stop positions
    for j in juncs:
        ranks = [RANK[a.cls(secs)] for a in j.arms]
        top = min(ranks)
        for ai, a in enumerate(j.arms):
            if a.is_ring():
                continue
            minor = RANK[a.cls(secs)] > top
            if not (j.signalized or j.roundabout or minor):
                continue
            c = a.chain
            t = j.trims[ai]
            s_stop = float(a.s(t + 1.5))
            sec = c.section(s_stop, secs)
            if getattr(sec, "construction", False):
                continue                 # ADR 0215: no traffic ever queued here - no oil stains
            hw = float(c.hw_at(s_stop))
            dirn_here = int(c.dirn[c.idx(s_stop)]) or 1
            _, _, lanes = lane_layout(sec, hw, dirn_here)
            # inbound = travel toward the junction: end 'a' -> travel -s, end 'b' -> travel +s
            inbound = lanes["bwd"] if (a.end == "a") != (dirn_here < 0) else lanes["fwd"]
            if sec.oneway:
                inb = a.inbound_dirn()
                if inb <= 0:
                    continue
                inbound = lanes["fwd"]
            for li, lat in enumerate(inbound):
                for m in range(1 + int(hf(j.id, ai, li, "m") * 3)):
                    d = t + 2.0 + m * (1.4 + hf(j.id, ai, li, m, "g") * 2.0)
                    if d > c.length - 2.0:
                        break
                    sc = float(a.s(d))
                    latj = lat + (hf(j.id, ai, li, m, "lat") - 0.5) * 0.5
                    P0 = c.line.offset_point(sc, latj)

                    def z_of(V2, c=c, sc=sc):
                        out = []
                        for q in V2:
                            ss, ll = c.line.project(q)
                            out.append(float(c.crossfall_z(ss, np.clip(ll, -c.hw_at(ss), c.hw_at(ss)))) + LIFT_OIL)
                        return np.array(out)
                    stain(buf, P0, z_of, 0.25 + hf(j.id, ai, li, m, "r") * 0.35, (j.id, ai, li, m),
                          f"oil:{j.id}:{ai}:{li}:{m}")
                    cnt["oil"] += 1
    seal_cracks(buf, net, cnt)
    compact_wheel_paths(buf, net, juncs, cnt)
    report["decals"] = cnt
    return cnt
