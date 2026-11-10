"""Asphalt sets: fresh SMA, worn AC, patch fill, 16 m crack layer, oil-stain decal atlas.

All values marked WORKING_VALUE are visual estimates; albedo targets and their sources are in materials_spec.json.
"""
from __future__ import annotations

import numpy as np

from pbrkit import Ctx, SurfaceSet, noise, voronoi, edge_dist, sstep, hash01, blur, calibrate, LUM

# stone palette of crushed aggregate seen in Podlasie wearing courses (granite / gabbro-basalt / quartzite);
# relative tints, WORKING_VALUE
STONES = np.array([[1.00, 1.00, 1.00],    # grey granite
                   [1.06, 0.98, 0.93],    # pinkish granite
                   [0.86, 0.89, 0.93],    # dark basalt / gabbro
                   [1.10, 1.08, 1.03],    # light quartzite
                   [0.97, 0.97, 0.95]], np.float32)
STONE_P = np.array([0.42, 0.18, 0.25, 0.05, 0.10])


def _aggregate(c: Ctx, k: int, cell: float, gap: float, coverage: float, chip_h: float):
    """Packed crushed chips. Shape = min(distance to the Voronoi bisector, own radius - distance to own site):
    angular where neighbours press, rounded where the chip is free. Returns height, sharp chip mask, tint,
    per-chip random, signed inside distance, socket mask (lost chips) and chip index."""
    wx = noise(c, k + 1, cell * 0.8, cell * 6) * cell * 0.18
    wy = noise(c, k + 2, cell * 0.8, cell * 6) * cell * 0.18
    d1, d2, i1, _, n = voronoi(c, k, cell, warp=(wx, wy))
    e = edge_dist(d1, d2)
    rid = hash01(i1, k)
    rid2 = hash01(i1, k + 7)
    rad = cell * (0.36 + 0.22 * hash01(i1, k + 5))
    inside = np.minimum(e - gap * 0.5, rad - d1)
    present = (rid < coverage).astype(np.float32)
    aa = 0.7 * c.px
    shape = sstep(-aa, aa, inside)
    plate = sstep(0, 0.22 * cell, inside)
    h = present * plate * chip_h * (0.55 + 0.45 * rid2)
    stone = np.searchsorted(np.cumsum(STONE_P), hash01(i1, k + 11) * 0.9999)
    tint = STONES[stone]
    absent = (1 - present) * shape
    return h, present * shape, tint, rid2, inside, absent, i1


def asphalt_base(c: Ctx, *, cell, gap, coverage, chip_h, mastic_lum, chip_lum, chip_var, pit_depth,
                 dust_share, target, rough_chip, rough_mastic, k0=10, hairline=0.0) -> SurfaceSet:
    h_chip, chip, tint, rid, e, absent, cid = _aggregate(c, k0, cell, gap, coverage, chip_h)
    sand = noise(c, k0 + 20, c.px * 2.2, 0.01, beta=0.6)                     # fines in the mastic
    mastic_h = -0.25e-3 + 0.12e-3 * sand
    # lost chips leave sockets below the mastic level
    sock = absent * (hash01(cid, k0 + 3) < 0.65)          # lost chip -> open socket; the rest is flush mastic
    h = np.maximum(h_chip, mastic_h) - pit_depth * sock
    low = noise(c, k0 + 30, 0.25, 4.0, beta=1.2)                              # in-tile tone drift
    mid = noise(c, k0 + 31, 0.03, 0.25, beta=0.8)
    # stone face: per-chip tone, faint internal grain, darker toward its rim (rounded edge falls into shadow)
    grain = noise(c, k0 + 22, c.px * 2.0, cell * 0.5, beta=0.4)
    chip_tone = chip_lum * (1 + chip_var * (rid - 0.5) * 2) * (1 + 0.05 * mid + 0.06 * grain)
    chip_tone *= 0.72 + 0.28 * sstep(0, 0.18 * cell, e)
    lum_mastic = mastic_lum * (1 + 0.10 * sand + 0.06 * mid)
    # thin dark ring around each stone where the binder meets it (meniscus shadow)
    ring = (1 - chip) * (1 - sstep(0, 0.0012, -e))
    lum_mastic = lum_mastic * (1 - 0.45 * ring)
    lum = lum_mastic * (1 - chip) + chip_tone * chip
    col = tint * chip[..., None] + np.array([1.0, 0.995, 0.985], np.float32) * (1 - chip[..., None])
    alb = lum[..., None] * col
    # dust caught in sockets (old surfaces): light warm grey instead of black
    dust = sock * (hash01(cid, k0 + 4) < dust_share)
    alb = alb * (1 - dust[..., None]) + dust[..., None] * np.array([0.105, 0.098, 0.088], np.float32) * (1 + 0.1 * sand[..., None])
    h = h * (1 - dust) + dust * (-0.4e-3)
    dust = dust > 0.5
    alb *= (1 + 0.035 * low)[..., None]
    joint = np.clip(sock * (~dust), 0, 1).astype(np.float32)
    if hairline > 0:
        # homogeneous fine shrinkage micro-cracking (low contrast, no distinctive features -> safe to tile)
        wx = noise(c, k0 + 40, 0.01, 0.3) * 0.02
        wy = noise(c, k0 + 41, 0.01, 0.3) * 0.02
        d1, d2, i1, i2, _ = voronoi(c, k0 + 42, 0.09, warp=(wx, wy))
        ee = edge_dist(d1, d2)
        on = hash01(np.minimum(i1, i2), np.maximum(i1, i2), k0) < hairline
        zone = sstep(0.2, 0.9, noise(c, k0 + 43, 0.2, 1.5))
        w = 0.35e-3 + 0.35e-3 * sstep(-1, 1, noise(c, k0 + 44, 0.02, 0.2))
        cr = on * zone * np.clip((w - ee) / c.px + 0.5, 0, 1)
        alb *= (1 - 0.55 * cr)[..., None]
        h -= 0.6e-3 * cr
        joint = np.maximum(joint, cr)
    alb, _ = calibrate(alb, target)
    rough = rough_mastic * (1 - chip) + rough_chip * chip
    rough = np.clip(rough + 0.03 * noise(c, k0 + 50, 0.05, 0.5), 0.05, 1)
    return SurfaceSet("", c, alb.astype(np.float32), h.astype(np.float32), rough.astype(np.float32),
                      rid.astype(np.float32), joint, detail_mask=np.ones_like(h), ao_k=0.6)


def sma_fresh(n=2048):
    c = Ctx(n, n, 4.0, 4.0, seed=101)
    s = asphalt_base(c, cell=0.0085, gap=0.0012, coverage=0.86, chip_h=1.6e-3, mastic_lum=0.032, chip_lum=0.055,
                     chip_var=0.15, pit_depth=1.2e-3, dust_share=0.05, target=0.075, rough_chip=0.70,
                     rough_mastic=0.62)
    s.name = "asphalt_sma_fresh"
    return s


def worn(n=2048):
    c = Ctx(n, n, 4.0, 4.0, seed=102)
    s = asphalt_base(c, cell=0.0080, gap=0.0016, coverage=0.84, chip_h=2.0e-3, mastic_lum=0.075, chip_lum=0.17,
                     chip_var=0.30, pit_depth=2.5e-3, dust_share=0.45, target=0.08, rough_chip=0.86,
                     rough_mastic=0.92, hairline=0.35)
    s.name = "asphalt_worn"
    return s


def patch(n=2048):
    c = Ctx(n, n, 4.0, 4.0, seed=103)
    s = asphalt_base(c, cell=0.0065, gap=0.0010, coverage=0.88, chip_h=1.2e-3, mastic_lum=0.034, chip_lum=0.058,
                     chip_var=0.25, pit_depth=1.0e-3, dust_share=0.08, target=0.062, rough_chip=0.74,
                     rough_mastic=0.66)
    # hand-raked fill: faint roller/rake streaks
    streak = noise(c, 160, 0.03, 0.6, aniso=6.0)
    s.albedo *= (1 + 0.04 * streak)[..., None]
    s.name = "asphalt_patch"
    return s


def cracks_layer(n=2048):
    """16 m crack layer (R open crack, G sealant band, B alligator zone, A ravelled halo). Distinctive features
    live here, at a 4x longer period than the base, so the 4 m base stays statistically uniform."""
    L = 16.0
    c = Ctx(n, n, L, L, seed=104)
    px = c.px
    X, Y = c.xy()
    # long cracks: Voronoi edges in a strongly warped domain; whole edges kept or dropped -> broken network
    wx = noise(c, 1, 0.4, 6.0, beta=1.3) * 0.45 + noise(c, 2, 0.05, 0.4, beta=0.8) * 0.012
    wy = noise(c, 3, 0.4, 6.0, beta=1.3) * 0.45 + noise(c, 4, 0.05, 0.4, beta=0.8) * 0.012
    d1, d2, i1, i2, _ = voronoi(c, 5, 3.2, warp=(wx, wy))
    e = edge_dist(d1, d2)
    a, b = np.minimum(i1, i2), np.maximum(i1, i2)
    keep = hash01(a, b, 1)
    long_on = keep < 0.60
    sealed = keep < 0.34
    # partial edges: a slow noise along the network cuts edges into 2-12 m runs
    run = noise(c, 6, 1.5, 10.0) > -0.35
    width = 1.2e-3 + 4.0e-3 * sstep(-1.2, 1.5, noise(c, 7, 0.15, 2.0))
    open_long = long_on & run & ~sealed
    cov_long = open_long * np.clip((width - e) / px + 0.5, 0, 1)
    # sealant: 2.5-4 cm band, hand-poured edges
    sw = 0.0125 + 0.0075 * sstep(-1, 1, noise(c, 8, 0.3, 3.0)) + 0.003 * noise(c, 9, 0.02, 0.15)
    seal = (long_on & sealed) * np.clip((sw - e) / px + 0.5, 0, 1)
    # branches: smaller cells, only close to an open long crack
    d1b, d2b, j1, j2, _ = voronoi(c, 10, 0.7, warp=(wx * 0.5, wy * 0.5))
    eb = edge_dist(d1b, d2b)
    near = blur(cov_long, 0.25 / px) > 0.01
    br_on = (hash01(np.minimum(j1, j2), np.maximum(j1, j2), 2) < 0.35) & near
    wb = 0.8e-3 + 1.5e-3 * sstep(-1, 1, noise(c, 11, 0.1, 1.0))
    cov_br = br_on * np.clip((wb - eb) / px + 0.5, 0, 1)
    # alligator zones: 2-4 blobs, fine polygon network 12-25 cm
    zone = sstep(1.3, 1.9, noise(c, 12, 1.0, 6.0, beta=1.5))
    d1a, d2a, k1, k2, _ = voronoi(c, 13, 0.17, warp=(wx * 0.15, wy * 0.15))
    ea = edge_dist(d1a, d2a)
    wa = 0.8e-3 + 1.6e-3 * sstep(-1, 1, noise(c, 14, 0.05, 0.5))
    cov_al = zone * (hash01(np.minimum(k1, k2), np.maximum(k1, k2), 3) < 0.85) * np.clip((wa - ea) / px + 0.5, 0, 1)
    crack = np.clip(cov_long + cov_br + cov_al, 0, 1)
    crack *= (1 - seal)
    halo = np.clip(blur(crack, 0.012 / px) * 6, 0, 1) * (1 - crack)
    height = -6e-3 * crack - 0.4e-3 * halo + 0.6e-3 * seal
    # the layer carries its own albedo multipliers for preview; the engine uses the mask channels
    mask = np.dstack([crack, seal, zone, halo]).astype(np.float32)
    return c, mask, height.astype(np.float32)


def oil_atlas(n=2048):
    """2x2 atlas of oil stains in radial decal space (centre 0.5/0.5 of each cell). Variant = floor(seed*4)."""
    half = n // 2
    alb = np.zeros((n, n, 3), np.float32)
    alpha = np.zeros((n, n), np.float32)
    rough = np.ones((n, n), np.float32)
    height = np.zeros((n, n), np.float32)
    kinds = ["drip_pool", "smear", "old_ring", "drip_cluster"]
    for v, kind in enumerate(kinds):
        c = Ctx(half, half, 1.0, 1.0, seed=200 + v)
        X, Y = c.xy()
        x, y = X - 0.5, Y - 0.5
        warp = noise(c, 1, 0.02, 0.4, beta=1.2)
        if kind == "smear":
            r = np.sqrt((x / 0.42) ** 2 + (y / 0.13) ** 2) + 0.12 * warp
            core = 1 - sstep(0.55, 1.0, r)
            streaks = sstep(-0.2, 1.2, noise(c, 2, 0.01, 0.3, aniso=0.12))
            cov = core * (0.55 + 0.45 * streaks)
        else:
            rr = np.sqrt(x ** 2 + y ** 2)
            base_r = {"drip_pool": 0.26, "old_ring": 0.40, "drip_cluster": 0.12}[kind]
            r = rr / base_r + 0.22 * warp
            cov = 1 - sstep(0.75, 1.0, r)
            if kind == "old_ring":
                ring = np.exp(-((r - 0.82) / 0.05) ** 2) * 0.6
                cov = cov * (0.35 + 0.25 * sstep(-1, 1, noise(c, 3, 0.03, 0.3))) + ring
            # satellite drops
            rng = c.rng(9)
            nd = {"drip_pool": 14, "old_ring": 6, "drip_cluster": 26}[kind]
            for _ in range(nd):
                a = rng.random() * 2 * np.pi
                dist = rng.uniform(0.6, 1.5) * base_r if kind != "drip_cluster" else rng.uniform(0.0, 0.38)
                cx, cy = 0.5 + np.cos(a) * dist, 0.5 + np.sin(a) * dist
                rad = rng.uniform(0.008, 0.03) if kind != "drip_cluster" else rng.uniform(0.01, 0.05)
                dd = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2) / rad + 0.3 * warp
                cov = np.maximum(cov, (1 - sstep(0.7, 1.0, dd)) * rng.uniform(0.5, 0.95))
        cov = np.clip(cov, 0, 1) * (0.75 + 0.25 * sstep(-1, 1, noise(c, 4, 0.01, 0.15)))
        # edge fade to zero at the cell border so mips never bleed between variants
        border = sstep(0.0, 0.04, np.minimum(np.minimum(X, 1 - X), np.minimum(Y, 1 - Y)))
        cov *= border
        fresh = {"drip_pool": 0.9, "smear": 0.6, "old_ring": 0.15, "drip_cluster": 0.8}[kind]
        wet = cov * fresh * sstep(0.3, 0.9, cov)
        # oil-soaked asphalt: near-black brown; iridescence is not modelled (WORKING_VALUE)
        col = np.array([0.020, 0.017, 0.013], np.float32) * (1 + 0.25 * noise(c, 5, 0.01, 0.2))[..., None]
        col = np.maximum(col, 0.0135)   # gate 3 albedo check (docs/06): never below sRGB 30 (linear 0.0130) after the noise modulation
        sl = (slice((v // 2) * half, (v // 2 + 1) * half), slice((v % 2) * half, (v % 2 + 1) * half))
        alb[sl] = col
        alpha[sl] = np.clip(cov * 0.92, 0, 1)
        rough[sl] = np.clip(0.80 - 0.50 * wet, 0.25, 1)
        height[sl] = 0.15e-3 * wet
    c = Ctx(n, n, 2.0, 2.0, seed=200)
    return SurfaceSet("oil_stain_alpha", c, alb, height, rough, np.zeros_like(alpha), alpha,
                      detail_mask=np.zeros_like(alpha), alpha=alpha, ao_k=0.0)
