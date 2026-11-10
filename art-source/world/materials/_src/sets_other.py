"""Concrete, kerb, paving (behaton I, rectangular 20x10), grass verge, compacted gravel, macro variation and the
photo-based asphalt detail layer. Dimensions and shares are WORKING_VALUE unless materials_spec.json cites a source.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from pbrkit import (Ctx, SurfaceSet, noise, voronoi, edge_dist, sstep, hash01, blur, calibrate, LUM,
                    tileable_crop_blend)


# ------------------------------------------------------------------------------------------------ concrete
def _seg_dist(X, Y, p0, p1):
    vx, vy = p1[0] - p0[0], p1[1] - p0[1]
    t = np.clip(((X - p0[0]) * vx + (Y - p0[1]) * vy) / (vx * vx + vy * vy), 0, 1)
    return np.hypot(X - (p0[0] + t * vx), Y - (p0[1] + t * vy))


def _crack_poly(c: Ctx, k, pts, w0, w1, warp_amp):
    """Hairline crack along a polyline in a warped domain; returns coverage."""
    X, Y = c.xy()
    wx = noise(c, k, 0.02, 1.0, beta=1.1) * warp_amp
    wy = noise(c, k + 1, 0.02, 1.0, beta=1.1) * warp_amp
    Xw, Yw = X + wx, Y + wy
    d = np.full(X.shape, 1e9, np.float32)
    for a, b in zip(pts[:-1], pts[1:]):
        d = np.minimum(d, _seg_dist(Xw, Yw, a, b))
    w = w0 + (w1 - w0) * sstep(-1, 1, noise(c, k + 2, 0.05, 0.6))
    return np.clip((w - d) / c.px + 0.5, 0, 1)


def _concrete_skin(c: Ctx, k, pore_share=0.004):
    """Cement skin: sand grain, pores (bug holes) and a faint trowel/broom drift. Returns lum mult, height."""
    sand = noise(c, k, c.px * 2.0, 0.006, beta=0.5)
    mid = noise(c, k + 1, 0.02, 0.4, beta=0.9)
    pores_n = noise(c, k + 2, c.px * 1.5, 0.004, beta=0.2)
    thr = np.quantile(pores_n, 1 - pore_share)
    pores = sstep(thr, thr + 0.6, pores_n)
    lum = 1 + 0.07 * sand + 0.05 * mid - 0.45 * pores
    h = 0.10e-3 * sand + 0.25e-3 * mid - 1.2e-3 * pores
    return lum, h, pores


def concrete_cast(n=2048):
    """Cast-in-place concrete slabs 5 x 5 m with sawn, sealed joints (yards, concrete roads). Tile 10 m (4 slabs)."""
    L = 10.0
    c = Ctx(n, n, L, L, seed=301)
    X, Y = c.xy()
    px = c.px
    jx = np.minimum(X % 5.0, 5.0 - X % 5.0)
    jy = np.minimum(Y % 5.0, 5.0 - Y % 5.0)
    dj = np.minimum(jx, jy)
    sid = (np.floor(X / 5.0).astype(int) * 7 + np.floor(Y / 5.0).astype(int))
    r1, r2, r3 = hash01(sid, 1), hash01(sid, 2), hash01(sid, 3)
    skin, h_skin, pores = _concrete_skin(c, 10)
    # broom finish across the slab (y direction), 2-4 mm grooves smeared by the broom, WORKING_VALUE
    broom = noise(c, 20, px * 2.0, 0.03, beta=0.3, aniso=0.08)
    worn = sstep(0.3, 1.4, noise(c, 21, 0.5, 6.0, beta=1.3))         # traffic-worn: broom gone, sand exposed
    h = h_skin + 0.2e-3 * broom * (1 - worn) + (r1 - 0.5) * 3e-3
    lum = 0.30 * skin * (1 + 0.03 * broom * (1 - worn)) * (1 + 0.10 * (r2 - 0.5)) * (1 + 0.04 * worn)
    # aggregate showing through worn skin
    d1, d2, i1, _, _ = voronoi(c, 22, 0.012)
    agg = sstep(0.0005, 0.0015, edge_dist(d1, d2)) * (hash01(i1, 5) < 0.5) * worn
    lum *= (1 + 0.12 * agg * (hash01(i1, 6) - 0.4))
    # joints: 8 mm sawn cut, sealant mostly present, open stretches collect dirt
    jw = 0.004
    seal_on = noise(c, 23, 0.3, 3.0) > -0.6
    joint = np.clip((jw - dj) / px + 0.5, 0, 1)
    seal_band = np.clip((0.007 - dj) / px + 0.5, 0, 1) * seal_on     # sealant overflows the cut slightly
    spall = (dj < 0.02) * sstep(1.2, 1.9, noise(c, 24, 0.008, 0.08)) * (1 - joint)
    h += -6e-3 * joint * (1 - seal_on) - 1.5e-3 * joint * seal_on - 2.5e-3 * spall
    # cracks: corner break + one transverse mid-slab crack (distinct features, period 10 m)
    cr = np.maximum(_crack_poly(c, 30, [(5.0, 6.6), (5.9, 6.1), (6.7, 5.0)], 0.4e-3, 1.4e-3, 0.06),
                    _crack_poly(c, 33, [(0.0, 2.3), (1.6, 2.45), (3.3, 2.2), (5.0, 2.5)], 0.3e-3, 1.2e-3, 0.08))
    h -= 2e-3 * cr
    lum *= (1 - 0.55 * cr) * (1 - 0.35 * spall)
    tint = np.dstack([1 + 0.025 * (r3 - 0.5) + 0 * X, 1 + 0 * X, 1 - 0.035 * (r3 - 0.5) + 0 * X])
    alb = lum[..., None] * np.array([1.0, 0.985, 0.955], np.float32) * tint
    seal_col = np.array([0.028, 0.027, 0.026], np.float32)
    dirt_col = np.array([0.075, 0.066, 0.055], np.float32)
    jm = np.maximum(seal_band, joint)[..., None]
    alb = alb * (1 - jm) + jm * np.where(seal_on[..., None], seal_col, dirt_col)
    # stains: tide-marked damp/dirt patches, low frequency
    st = sstep(0.3, 2.2, noise(c, 40, 0.3, 4.0, beta=1.3))
    alb *= (1 - 0.08 * st)[..., None]
    alb, _ = calibrate(alb, 0.30)
    rough = np.clip(0.88 - 0.10 * worn - 0.15 * seal_band * seal_on + 0.03 * noise(c, 41, 0.05, 0.5), 0.3, 1)
    return SurfaceSet("concrete_cast_5m_joints", c, alb.astype(np.float32), h.astype(np.float32), rough,
                      r1.astype(np.float32), np.maximum(joint * (1 - seal_on), cr).astype(np.float32),
                      detail_mask=(1 - jm[..., 0]).astype(np.float32), ao_k=0.5)


def concrete_jomb(n=2048):
    """Precast road plates 3.0 x 1.5 m ('płyty drogowe' type JOMB) in rows with irregular offsets, wide soil
    joints, chamfered/chipped edges, settlement steps and lifting-socket recesses. Tile 6 m (8 plates)."""
    L = 6.0
    c = Ctx(n, n, L, L, seed=302)
    X, Y = c.xy()
    px = c.px
    row = np.floor(Y / 1.5).astype(int)
    offs = np.array([0.0, 1.35, 0.6, 2.2])[row % 4]
    xr = (X - offs) % L
    col = np.floor(xr / 3.0).astype(int)
    pid = row * 2 + col
    u = xr - col * 3.0                 # 0..3 along the plate
    v = Y - row * 1.5                  # 0..1.5 across
    r1, r2, r3, r4 = (hash01(pid, i) for i in range(1, 5))
    # joint widths per plate edge (10-30 mm), WORKING_VALUE
    gx = 0.006 + 0.010 * hash01(pid, 11)
    gy = 0.006 + 0.008 * hash01(row, 12)
    du = np.minimum(u, 3.0 - u) - gx
    dv = np.minimum(v, 1.5 - v) - gy
    dj = np.minimum(du, dv)                        # signed: <0 = in the joint
    plate = sstep(-px, px, dj)
    cham = sstep(0.0, 0.015, dj)                   # 15 mm worn arris
    chip = (dj < 0.04) * sstep(1.1, 1.8, noise(c, 13, 0.01, 0.12))
    # settlement: per-plate step +-6 mm and tilt
    tilt = (r2 - 0.5) * 0.006 * (u - 1.5) + (r3 - 0.5) * 0.006 * (v - 0.75)
    skin, h_skin, pores = _concrete_skin(c, 20, pore_share=0.01)
    h = plate * ((r1 - 0.5) * 12e-3 + tilt + h_skin - 6e-3 * (1 - cham) - 4e-3 * chip) + (1 - plate) * (-25e-3)
    # lifting sockets: two notches on each long edge, 0.55 m from the ends (WORKING_VALUE)
    sock = np.zeros_like(X)
    for uc in (0.55 + 0.1 * float(hash01(np.array(7), 1)), 2.45):
        for vc in (gy + 0.025, 1.5 - gy - 0.025):
            sock = np.maximum(sock, (np.abs(u - uc) < 0.045) * (np.abs(v - vc) < 0.03))
    sock = blur(sock.astype(np.float32), 0.8)
    rust = sock * 0 + blur(sock, 0.02 / px) * 2.5 * (noise(c, 21, 0.005, 0.05) > -0.3)
    h -= 30e-3 * sock * plate
    lum = 0.27 * skin * (1 + 0.16 * (r4 - 0.5)) * (1 - 0.25 * chip) * (0.82 + 0.18 * cham)
    # weathering: darker, greenish lichen bloom toward plate edges (wet), lighter worn wheel band
    edge_w = 1 - sstep(0.0, 0.25, dj)
    lich = edge_w * sstep(0.2, 1.2, noise(c, 22, 0.02, 0.3))
    wheel = sstep(0.4, 1.4, noise(c, 23, 0.6, 5.0, beta=1.4))
    alb = lum[..., None] * np.array([1.0, 0.985, 0.95], np.float32)
    alb = alb * (1 - 0.35 * lich[..., None]) + lich[..., None] * np.array([0.10, 0.11, 0.075], np.float32) * 0.35
    alb *= (1 + 0.08 * wheel)[..., None]
    alb = alb * (1 - np.clip(rust, 0, 1)[..., None] * 0.6) + np.clip(rust, 0, 1)[..., None] * 0.6 * np.array(
        [0.13, 0.065, 0.035], np.float32)
    # joint fill: soil + sand, grass/moss in a share of joints
    soil = np.array([0.060, 0.050, 0.040], np.float32) * (1 + 0.25 * noise(c, 24, 0.002, 0.02))[..., None]
    green = sstep(0.0, 1.0, noise(c, 25, 0.03, 0.6)) * (hash01(pid, 26) < 0.6)
    soil = soil * (1 - green[..., None]) + green[..., None] * np.array([0.045, 0.065, 0.025], np.float32)
    jm = (1 - plate)[..., None]
    alb = alb * (1 - jm) + soil * jm
    alb = alb * (1 - 0.35 * sock[..., None])
    alb, _ = calibrate(alb, 0.27, weight=plate)
    rough = np.clip(0.9 + 0.03 * noise(c, 27, 0.05, 0.5), 0.5, 1)
    joint = np.maximum(1 - plate, sock)
    return SurfaceSet("concrete_slab_3x1.5", c, alb.astype(np.float32), h.astype(np.float32), rough,
                      r4.astype(np.float32), joint.astype(np.float32), detail_mask=plate.astype(np.float32),
                      ao_scales=(0.004, 0.02, 0.08), ao_k=0.35)


def kerb(nx=2048, ny=512):
    """Precast concrete kerb 15x30 cm in 1 m units (PN-EN 1340), u = metres along, v = metres across the profile.
    Tile 2 m x 0.5 m (two units). Mortar joints 6-8 mm, chipped arrises near joints, per-unit tone."""
    c = Ctx(nx, ny, 2.0, 0.5, seed=303)
    X, Y = c.xy()
    px = c.px
    uid = np.floor(X / 1.0).astype(int)
    dj = np.minimum(X % 1.0, 1.0 - X % 1.0)
    r1, r2 = hash01(uid, 1), hash01(uid, 2)
    jw = 0.0035
    joint = np.clip((jw - dj) / px + 0.5, 0, 1)
    skin, h_skin, pores = _concrete_skin(c, 10, pore_share=0.006)
    chip = (dj < 0.04) * sstep(1.6, 2.2, noise(c, 11, 0.008, 0.06)) * (hash01(uid, 3) < 0.6)
    h = h_skin - 4e-3 * joint - 3e-3 * chip + (r1 - 0.5) * 2e-3
    lum = 0.36 * skin * (1 + 0.10 * (r2 - 0.5)) * (1 + 0.10 * chip)
    alb = lum[..., None] * np.array([1.0, 0.99, 0.965], np.float32)
    mortar = np.array([0.16, 0.155, 0.145], np.float32) * (1 + 0.2 * noise(c, 12, 0.002, 0.02))[..., None]
    alb = alb * (1 - joint[..., None]) + mortar * joint[..., None]
    grime = sstep(0.4, 1.5, noise(c, 13, 0.03, 0.4))
    alb *= (1 - 0.15 * grime)[..., None]
    alb, _ = calibrate(alb, 0.28)
    rough = np.clip(0.86 + 0.03 * noise(c, 14, 0.02, 0.2), 0.5, 1)
    return SurfaceSet("kerb_concrete_1m", c, alb.astype(np.float32), h.astype(np.float32), rough,
                      r1.astype(np.float32), joint.astype(np.float32), detail_mask=1 - joint, ao_k=0.5)


# --------------------------------------------------------------------------------------------------- paving
def _pavers(c: Ctx, bid, dj, *, joint_half, chamfer, shades, target, k=0, name=""):
    """Shared paver look: per-block shade from a 'melange' palette, settlement, chamfer, chipped corners, sand
    joints with dirt and some moss, tyre-polished tops in traffic zones."""
    px = c.px
    r1, r2, r3, r4 = (hash01(bid, k + i) for i in range(1, 5))
    shade = np.asarray(shades, np.float32)[np.minimum((r1 * len(shades)).astype(int), len(shades) - 1)]
    block = sstep(-0.6 * px, 0.6 * px, dj - joint_half)
    cham = sstep(joint_half, joint_half + chamfer, dj)
    chip = (dj < joint_half + 0.012) * sstep(1.2, 1.9, noise(c, k + 10, 0.005, 0.05)) * (r4 < 0.35)
    skin = noise(c, k + 11, px * 2.0, 0.004, beta=0.5)
    pores_n = noise(c, k + 12, px * 1.5, 0.003, beta=0.2)
    pores = sstep(np.quantile(pores_n, 0.996), np.quantile(pores_n, 0.999), pores_n)
    settle = (r2 - 0.5) * 4e-3
    h = block * (settle - 3e-3 * (1 - cham) - 2.5e-3 * chip + 0.08e-3 * skin - 0.8e-3 * pores) \
        + (1 - block) * (-6e-3 + 0.6e-3 * noise(c, k + 13, 0.002, 0.02))
    traffic = sstep(0.0, 1.3, noise(c, k + 14, 0.8, 4.0, beta=1.4))
    tone = (1 + 0.06 * (r3 - 0.5)) * (1 + 0.05 * skin) * (1 - 0.5 * pores) * (1 - 0.25 * chip) * \
        (0.80 + 0.20 * cham)
    alb = shade * tone[..., None]
    # dirt in the chamfer and a darker band along the joint (traffic pushes dirt into it)
    near = 1 - sstep(joint_half, joint_half + 0.012, dj)
    alb *= (1 - 0.18 * near)[..., None]
    alb *= (1 - 0.05 * traffic)[..., None]                                  # tyre grime in traffic zones
    sand = np.array([0.13, 0.115, 0.095], np.float32) * (1 + 0.25 * noise(c, k + 15, 0.002, 0.02))[..., None]
    moss = sstep(0.6, 1.5, noise(c, k + 16, 0.05, 1.0)) * (1 - traffic)
    jfill = sand * (1 - 0.6 * moss[..., None]) + moss[..., None] * np.array([0.04, 0.06, 0.022], np.float32)
    jm = (1 - block)[..., None]
    alb = alb * (1 - jm) + jfill * 0.6 * jm
    alb, _ = calibrate(alb, target, weight=block)
    rough = np.clip(0.88 - 0.12 * traffic * block + 0.03 * noise(c, k + 17, 0.02, 0.3), 0.4, 1)
    return SurfaceSet(name, c, alb.astype(np.float32), h.astype(np.float32), rough.astype(np.float32),
                      r1.astype(np.float32), (1 - block).astype(np.float32), detail_mask=block.astype(np.float32),
                      ao_scales=(0.003, 0.012, 0.04), ao_k=0.5)


def behaton(n=2048):
    """Interlocking I-shaped (double-T) blocks, rows offset by half a block, boundaries a trapezoid wave.
    Block 200 mm long, 166 mm across the flanges, 120 mm at the waist (WORKING_VALUE, typical 'behaton' 8 cm)."""
    Lb, rows = 0.20, 28
    L = 4.0
    P = L / rows                       # row pitch 142.9 mm
    d = 0.0115                         # boundary wave amplitude: flange 166 mm, waist 120 mm
    c = Ctx(n, n, L, L, seed=304)
    X, Y = c.xy()

    def wave(ph):                      # +1 at the block ends (phase 0), -1 in the waist (phase 0.5), slanted flanks
        q = np.abs(((ph + 0.5) % 1.0) - 0.5)          # 0 at ends .. 0.5 at waist
        return 1 - 2 * sstep(0.18, 0.32, q)

    k0 = np.floor(Y / P).astype(int)
    best_row = k0.copy()
    # boundary between row k and k+1: y = (k+1) P + d * wave((x - o_k)/L)  (row k ends protrude upwards)
    def bnd(k):
        o = (k % 2) * Lb / 2
        return (k + 1) * P + d * wave((X - o) / Lb)

    lo = bnd(k0 - 1)
    hi = bnd(k0)
    best_row = np.where(Y < lo, k0 - 1, np.where(Y >= hi, k0 + 1, k0))
    kk = best_row
    o = (kk % 2) * Lb / 2
    j = np.floor((X - o) / Lb).astype(int)
    xin = (X - o) - j * Lb
    dv = np.minimum(np.abs(xin), np.abs(Lb - xin))
    yb0, yb1 = bnd(kk - 1), bnd(kk)
    dh = np.minimum(Y - yb0, yb1 - Y) / 1.12        # flank slope correction (approx.)
    dj = np.minimum(dv, dh)
    bid = (kk % rows) * 1000 + (j % int(round(L / Lb)))
    grey = [[0.25, 0.25, 0.24], [0.22, 0.22, 0.215], [0.27, 0.265, 0.25]]
    return _pavers(c, bid, dj, joint_half=0.0018, chamfer=0.004, shades=grey, target=0.23, k=40,
                   name="behaton_i_grey")


def rect_paving(n=2048):
    """Rectangular 200x100 mm blocks (6 cm footway 'holland'), running bond, grey melange. Tile 4 m."""
    L = 4.0
    c = Ctx(n, n, L, L, seed=305)
    X, Y = c.xy()
    r = np.floor(Y / 0.10).astype(int)
    o = (r % 2) * 0.10
    j = np.floor((X - o) / 0.20).astype(int)
    xin = (X - o) - j * 0.20
    dj = np.minimum(np.minimum(xin, 0.20 - xin), np.minimum(Y - r * 0.10, (r + 1) * 0.10 - Y))
    bid = (r % 40) * 1000 + (j % 20)
    shades = [[0.27, 0.27, 0.26], [0.24, 0.235, 0.23], [0.29, 0.285, 0.27], [0.22, 0.22, 0.215]]
    return _pavers(c, bid, dj, joint_half=0.0015, chamfer=0.003, shades=shades, target=0.26, k=60,
                   name="paving_20x10_grey")


# ------------------------------------------------------------------------------------------- ground cover
GRASS_CHROMA = 1.45          # D38: summer grass chroma gain (target rendered sat 35-40 HSV %)


def grass_verge(n=2048, ss=2):
    """Mown roadside verge seen from above: blades by z-buffer splatting (supersampled ss x), tufted, with
    thatch, bare soil, plantain/dandelion rosettes and clover. Tile 3 m. Albedo summer + late_autumn."""
    L = 3.0
    N = n * ss
    c = Ctx(N, N, L, L, seed=306)
    px = c.px
    rng = c.rng(1)
    zkey = np.zeros(N * N, np.int64)
    blades = []
    IDX_BITS = 23

    def splat(x0, y0, ang, ln, wd, ztop, cls, base_idx):
        m = len(x0)
        nsamp = int(np.ceil(ln.max() / (0.7 * px))) + 1
        t = np.linspace(0, 1, nsamp, dtype=np.float32)
        cx = x0[:, None] + np.cos(ang)[:, None] * ln[:, None] * t
        cy = y0[:, None] + np.sin(ang)[:, None] * ln[:, None] * t
        z = ztop[:, None] * (0.25 + 0.75 * t)
        idx = (base_idx + np.arange(m))[:, None].repeat(nsamp, 1)
        nx_, ny_ = -np.sin(ang), np.cos(ang)
        offs = [-0.5, 0.5] if wd.mean() > 1.5 * px else [0.0]
        for of in offs:
            w = wd[:, None] * of * (1 - 0.6 * t)
            xx = ((cx + nx_[:, None] * w) / px).astype(np.int64) % N
            yy = ((cy + ny_[:, None] * w) / px).astype(np.int64) % N
            zq = np.clip(z * 4000, 1, 2 ** 15).astype(np.int64)
            key = (zq << IDX_BITS) | idx
            np.maximum.at(zkey, (yy * N + xx).ravel(), key.ravel())

    count = 0
    cls_all, ztop_all = [], []
    # thatch: flat dead fibres on the ground
    m = 160000
    x0, y0 = rng.random(m) * L, rng.random(m) * L
    ang = rng.random(m) * 2 * np.pi
    for s0 in range(0, m, 40000):
        sl = slice(s0, s0 + 40000)
        splat(x0[sl], y0[sl], ang[sl], rng.uniform(0.01, 0.04, 40000), np.full(40000, 0.0008),
              rng.uniform(0.002, 0.006, 40000), 0, count + s0)
    cls_all.append(np.zeros(m, int)); ztop_all.append(np.full(m, 0.006)); count += m
    # rosettes (plantain/dandelion) and clover: broad leaves, mid height
    nros = 120
    for kind, nr, nleaf, lmin, lmax, wleaf, clsid in (("rosette", nros, 9, 0.03, 0.07, 0.012, 4),
                                                       ("clover", 260, 7, 0.004, 0.012, 0.006, 5)):
        cxs, cys = rng.random(nr) * L, rng.random(nr) * L
        x0 = np.repeat(cxs, nleaf); y0 = np.repeat(cys, nleaf)
        if kind == "clover":
            x0 += rng.normal(0, 0.02, x0.size); y0 += rng.normal(0, 0.02, y0.size)
        ang = rng.random(x0.size) * 2 * np.pi
        ln = rng.uniform(lmin, lmax, x0.size)
        wd = np.full(x0.size, wleaf)
        for wfrac in (-0.35, 0.0, 0.35):                   # broad leaf = 3 parallel strokes
            xo = x0 - np.sin(ang) * wd * wfrac
            yo = y0 + np.cos(ang) * wd * wfrac
            splat(xo, yo, ang, ln * (1 - abs(wfrac)), np.full(x0.size, px * 1.2), np.full(x0.size, 0.03),
                  clsid, count)
        cls_all.append(np.full(x0.size, clsid)); ztop_all.append(np.full(x0.size, 0.03)); count += x0.size
    # blades in tufts
    ntuft = int(L * L / 0.000225)                           # one tuft per 1.5x1.5 cm
    tx, ty = rng.random(ntuft) * L, rng.random(ntuft) * L
    dens = 1 / (1 + np.exp(-1.2 - 2.5 * noise(Ctx(256, 256, L, L, seed=306), 7, 0.08, 1.0)))   # clustered density
    keep = rng.random(ntuft) < dens[(ty / L * 256).astype(int) % 256, (tx / L * 256).astype(int) % 256]
    tx, ty = tx[keep], ty[keep]
    per = rng.integers(10, 26, tx.size)
    bx = np.repeat(tx, per) + rng.normal(0, 0.008, per.sum())
    by = np.repeat(ty, per) + rng.normal(0, 0.008, per.sum())
    lean = np.repeat(rng.random(tx.size) * 2 * np.pi, per)
    ang = lean + rng.normal(0, 0.9, bx.size)
    m = bx.size
    elev = rng.uniform(0.35, 1.3, m)                         # projected length shrinks for upright blades
    ln = rng.uniform(0.03, 0.09, m) * np.cos(elev) + 0.004
    ztop = rng.uniform(0.04, 0.09, m)
    cls = np.searchsorted(np.cumsum([0.62, 0.17, 0.11, 0.10]), rng.random(m))  # green, yellow-green, dark, dead
    cls = np.array([1, 2, 3, 6])[cls]
    for s0 in range(0, m, 40000):
        sl = slice(s0, s0 + 40000)
        splat(bx[sl] % L, by[sl] % L, ang[sl], ln[sl], rng.uniform(0.0015, 0.0035, len(bx[sl])), ztop[sl], 1,
              count + s0)
    cls_all.append(cls); ztop_all.append(ztop); count += m
    cls_all = np.concatenate([np.array([-1])] + cls_all)    # index 0 -> background (+1 shift below)
    ztop_all = np.concatenate([np.array([1.0])] + ztop_all)
    idx = (zkey & ((1 << IDX_BITS) - 1)).reshape(N, N)
    zq = (zkey >> IDX_BITS).reshape(N, N)
    has = zq > 0
    idx = np.where(has, idx + 1, 0)
    cl = cls_all[idx]
    z = zq / 4000.0
    tt = np.clip(z / ztop_all[idx], 0, 1)
    vid = hash01(idx, 3)
    pal = {   # linear albedo per class (summer, late autumn); WORKING_VALUE, tuned to photos of Podlasie verges
        -1: ([0.055, 0.045, 0.035], [0.055, 0.045, 0.035]),   # bare soil
        0: ([0.15, 0.13, 0.085], [0.15, 0.125, 0.08]),        # thatch
        1: ([0.065, 0.105, 0.030], [0.075, 0.085, 0.035]),    # green blade
        2: ([0.105, 0.125, 0.040], [0.12, 0.105, 0.045]),     # yellow-green
        3: ([0.040, 0.070, 0.025], [0.055, 0.060, 0.030]),    # dark green
        4: ([0.050, 0.085, 0.030], [0.060, 0.070, 0.030]),    # rosette leaves
        5: ([0.075, 0.120, 0.045], [0.070, 0.090, 0.040]),    # clover
        6: ([0.16, 0.135, 0.085], [0.17, 0.14, 0.09]),        # dead blade
    }
    out = {}
    for season, si in (("summer", 0), ("late_autumn", 1)):
        col = np.zeros((N, N, 3), np.float32)
        for k, v in pal.items():
            msk = cl == k
            col[msk] = v[si]
        shade = (0.55 + 0.45 * tt) * (0.80 + 0.40 * vid)
        col *= np.where(cl[..., None] >= 0, shade[..., None], 1.0)
        out[season] = col
    soilv = noise(c, 9, px * 2, 0.05, beta=0.6)
    for kk in out:
        out[kk][cl == -1] *= (1 + 0.25 * soilv[cl == -1])[..., None]
    # relief for the normal map is compressed (x0.12): blades are thin, a 5 cm cliff would read as black outlines
    h = 0.12 * np.where(has, z, -0.004 + 0.002 * soilv).astype(np.float32)
    h = blur(h, 1.2)
    rough = np.where(cl >= 1, 0.80, 0.95).astype(np.float32)
    bare = (cl <= 0).astype(np.float32)

    def ds(a):
        sh = a.shape
        return a.reshape(n, ss, n, ss, *sh[2:]).mean(axis=(1, 3))
    c2 = Ctx(n, n, L, L, seed=306)
    # D38 (owner, docs/11; ADR 0060): renders read washed out (grass sat 24-29 HSV % vs 33-58 in the Bialystok photos)
    # -> chroma of the summer albedo x GRASS_CHROMA about its own luminance (hue and mean luminance kept; the engine
    # takes the hue from the set). Material only, no post-processing / exposure change. WORKING_VALUE.
    summer = ds(out["summer"])
    lum = (summer @ LUM)[..., None]
    summer = np.clip(lum + GRASS_CHROMA * (summer - lum), 0.004, 1.0)
    alb, _ = calibrate(summer, 0.095)
    alb2, _ = calibrate(ds(out["late_autumn"]), 0.095)
    s = SurfaceSet("grass_verge", c2, alb.astype(np.float32), ds(h).astype(np.float32), ds(rough),
                   hash01(idx, 5)[::ss, ::ss].astype(np.float32), ds(bare), detail_mask=1 - ds(bare),
                   ao_scales=(0.004, 0.015, 0.04), ao_k=0.5)
    s.extra_albedo["late_autumn"] = alb2.astype(np.float32)
    return s


def gravel(n=2048):
    """Compacted crushed-stone shoulder / yard (kliniec + fines): stones of two sizes half-buried in dust."""
    L = 3.0
    c = Ctx(n, n, L, L, seed=307)
    px = c.px
    fines = noise(c, 1, px * 2, 0.008, beta=0.4)
    h = 0.3e-3 * fines
    pal = np.array([[0.24, 0.235, 0.22], [0.30, 0.27, 0.22], [0.16, 0.16, 0.16], [0.34, 0.31, 0.26],
                    [0.22, 0.18, 0.15]], np.float32)
    alb = np.array([0.20, 0.18, 0.15], np.float32) * (1 + 0.15 * fines)[..., None]
    alb = np.broadcast_to(alb, (n, n, 3)).copy()
    rid_all = np.zeros((n, n), np.float32)
    for k, cell, cov, hh in ((10, 0.010, 0.75, 3e-3), (20, 0.022, 0.40, 6e-3)):
        wx = noise(c, k + 1, cell, cell * 5) * cell * 0.25
        wy = noise(c, k + 2, cell, cell * 5) * cell * 0.25
        d1, d2, i1, _, _ = voronoi(c, k, cell, warp=(wx, wy))
        e = edge_dist(d1, d2)
        rad = cell * (0.30 + 0.20 * hash01(i1, k + 3))
        inside = np.minimum(e - cell * 0.06, rad - d1)
        on = hash01(i1, k + 4) < cov
        st = sstep(-px * 0.7, px * 0.7, inside) * on
        dome = np.sqrt(np.clip(inside / rad, 0, 1))
        hs = dome * hh * (0.5 + 0.5 * hash01(i1, k + 5)) + 0.4e-3
        top = (st > 0.5) & (hs > h)
        h = np.where(top, hs, h)
        sc = pal[np.minimum((hash01(i1, k + 6) * len(pal)).astype(int), len(pal) - 1)]
        sc = sc * (0.75 + 0.35 * dome)[..., None] * (1 + 0.08 * noise(c, k + 7, px * 2, cell, beta=0.3))[..., None]
        alb = np.where(top[..., None], sc, alb)
        rid_all = np.where(top, hash01(i1, k + 8), rid_all)
    dust = sstep(0.3, 1.6, noise(c, 30, 0.05, 0.8))
    alb = alb * (1 - 0.25 * dust[..., None]) + 0.25 * dust[..., None] * np.array([0.21, 0.19, 0.16], np.float32)
    alb, _ = calibrate(alb, 0.20)
    rough = np.clip(0.93 + 0.02 * fines, 0.6, 1).astype(np.float32)
    joint = (h < np.quantile(h, 0.2)).astype(np.float32)
    return SurfaceSet("gravel_compacted", c, alb.astype(np.float32), h.astype(np.float32), rough, rid_all,
                      joint, ao_k=0.4)


# ------------------------------------------------------------------------------------------ shared layers
def macro(n=1024):
    """64 m macro variation, R/G compatible with Kamion/World Surface (_MacroMap R = 1st octave, G = 2nd).
    B = wear/dirt blobs, A = 0.5-4 m mottling. All centred on 0.5."""
    c = Ctx(n, n, 64.0, 64.0, seed=308)
    r = noise(c, 1, 8.0, 64.0, beta=1.3)
    g = noise(c, 2, 2.0, 16.0, beta=1.1)
    b = noise(c, 3, 1.5, 24.0, beta=1.4)
    b = np.tanh(1.3 * b)
    a = noise(c, 4, 0.5, 4.0, beta=0.9)
    return c, np.dstack([0.5 + 0.17 * np.clip(x, -2.9, 2.9) for x in (r, g, b * 1.2, a)]).astype(np.float32)


def asphalt_detail_photo(photo: Path, n=1024):
    """1 m detail layer from the public-domain photo 'Worn_cracked_asphalt_pavement.jpg' (John Harvey, Wikimedia
    Commons): crack-free crop, luminance high-pass, local contrast normalised, made tileable. Scale assumed
    ~0.9 mm/px from the 8-11 mm aggregate (WORKING_VALUE). Returns detail albedo (neutral 0.5) and height."""
    im = Image.open(photo).convert("RGB")
    crop = im.crop((1830, 0, 2726, 896)).resize((n, n), Image.LANCZOS)
    a = np.asarray(crop, np.float32) / 255.0
    lin = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    lum = np.log(lin @ LUM + 1e-3)
    from scipy import ndimage
    hp = lum - ndimage.gaussian_filter(lum, 40, mode="reflect")
    sd = np.sqrt(ndimage.gaussian_filter(hp ** 2, 60, mode="reflect")) + 1e-4
    hp = hp / sd
    hp = np.clip(hp, -3.5, 3.5)
    hp = tileable_crop_blend(hp - hp.mean())
    hp = (hp - hp.mean()) / hp.std()
    return hp.astype(np.float32)
