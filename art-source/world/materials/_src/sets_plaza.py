"""Stone sett sets of authored town squares (ADR 0325): Plac Czarnieckiego in Tykocin.

Reference only (no pixel of a photo is used): Commons "Mglisty poranek na placu Czarnieckiego w Tykocinie z pomnikiem"
(K. Poplawski, CC BY 4.0) for the look - light grey granite setts laid in segmental arcs inside the fields, bands of
small red setts in straight rows - and the GUGiK orthophoto 2024 for the layout: a square lattice at 45 degrees to the
tile, period LATTICE_M (2.255 m measured, residuals < 0.10 m). Band width, sett sizes and colours are WORKING_VALUE.

  sett_lattice_tykocin   tile = LATTICE_M * sqrt(2): bands on both diagonals of the tile (two fields per tile), sampled
                         through mesh UV0 in the plaza frame (paved_area `uv_frame`), calibrated colours
  sett_rows_tint         straight rows of small setts, neutral modulation map (mean 0.5): colour from the manifest
                         (red border band of the plaza, grey walks around the lawns)
  granite_honed_tint     honed grey granite of a monument plinth (Knyszyn), neutral modulation map
"""
from __future__ import annotations

import math

import numpy as np

from pbrkit import Ctx, SurfaceSet, calibrate, hash01, noise, sstep, voronoi

LATTICE_M = 2.255            # measured on the orthophoto (EPSG:2180), both band families
BAND_M = 0.48                # WORKING_VALUE: 5 rows of ~9 cm setts (photo); the orthophoto blur gives FWHM 0.57 m
TILE_M = LATTICE_M * math.sqrt(2.0)
ROW_M = BAND_M / 5.0         # row pitch of the band setts and of the arcs
BAND_STONES = 40             # stones per 2 lattice periods along a band (periodicity of the tile): 113 mm long
GREY = [[0.33, 0.33, 0.325], [0.29, 0.292, 0.295], [0.36, 0.355, 0.345], [0.26, 0.262, 0.268], [0.34, 0.325, 0.31]]
RED = [[0.175, 0.072, 0.058], [0.145, 0.066, 0.056], [0.20, 0.088, 0.066], [0.125, 0.064, 0.058], [0.16, 0.085, 0.074]]
JOINT_FILL = np.array([0.085, 0.078, 0.066], np.float32)      # sand, soil and fines between the stones


def _stone_surface(c, k, sid, dj, joint_half, shade):
    """Split-face sett: cushion top, rough split texture, mineral speckle, worn (smoother, lighter) crown, sand joints.
    Returns albedo, height, roughness, block mask."""
    px = c.px
    r2, r3 = hash01(sid, k + 2), hash01(sid, k + 3)
    block = sstep(-0.6 * px, 0.6 * px, dj - joint_half)
    cushion = sstep(joint_half, joint_half + 0.022, dj)                 # rounded arrises of hand-split stone
    split = noise(c, k + 10, 0.006, 0.05, beta=1.3)                     # facets of the split face
    grain = noise(c, k + 11, px * 2.0, 0.006, beta=0.3)                 # feldspar / mica speckle
    mott = noise(c, k + 15, 0.01, 0.06, beta=1.0)                       # mineral clouds inside a stone
    crown = sstep(0.012, 0.035, dj) * sstep(-0.3, 0.9, split)           # high spots polished by feet and tyres
    h = block * ((r2 - 0.5) * 5e-3 - 7e-3 * (1 - cushion) + 1.6e-3 * split * cushion + 0.1e-3 * grain) \
        + (1 - block) * (-11e-3 + 1.2e-3 * noise(c, k + 12, 0.003, 0.03))
    tone = (1 + 0.26 * (r3 - 0.5)) * (1 + 0.17 * grain) * (1 + 0.07 * mott) * (0.80 + 0.20 * cushion) * (1 + 0.06 * crown)
    alb = shade * tone[..., None]
    near = 1 - sstep(joint_half, joint_half + 0.010, dj)                # dirt band along the joint
    alb = alb * (1 - 0.22 * near)[..., None]
    fill = JOINT_FILL * (1 + 0.3 * noise(c, k + 13, 0.003, 0.03))[..., None]
    moss = sstep(0.9, 1.8, noise(c, k + 14, 0.08, 0.9))[..., None]
    fill = fill * (1 - 0.5 * moss) + moss * np.array([0.045, 0.06, 0.028], np.float32) * 0.5
    jm = (1 - block)[..., None]
    alb = alb * (1 - jm) + fill * jm
    rough = np.clip(0.86 - 0.14 * crown * block + 0.08 * (1 - block), 0.4, 1.0)
    return alb.astype(np.float32), h.astype(np.float32), rough.astype(np.float32), block.astype(np.float32)


def _rdist(d1, d2, r=0.014):
    """Distance to the outline of a stone with rounded corners from the distances to its two pairs of sides."""
    return r - np.hypot(np.maximum(r - d1, 0.0), np.maximum(r - d2, 0.0)) + np.maximum(np.minimum(d1, d2) - r, 0.0)


def _warp(c, k, X, Y, amp=0.007):
    """Hand-laid stones: joints wander by a few millimetres (periodic, so the tile still wraps)."""
    return X + amp * noise(c, k, 0.12, 0.6, beta=1.5), Y + amp * noise(c, k + 1, 0.12, 0.6, beta=1.5)


def _pick(shades, r):
    s = np.asarray(shades, np.float32)
    return s[np.minimum((r * len(s)).astype(int), len(s) - 1)]


def sett_lattice(n=2048):
    """Granite fields in segmental arcs inside a diagonal lattice of red sett bands. Tile = LATTICE_M * sqrt(2)."""
    c = Ctx(n, n, TILE_M, TILE_M, seed=3251)
    X, Y = c.xy()
    X, Y = _warp(c, 90, X, Y)
    Yv = TILE_M - Y                                   # +v up, so the pattern is not mirrored against the mesh UV
    s2 = math.sqrt(0.5)
    pa, pb = (X + Yv) * s2, (X - Yv) * s2             # lattice axes; the tile translations are (1, 1) and (1, -1) periods
    ia, ib = np.floor(pa / LATTICE_M + 0.5).astype(int), np.floor(pb / LATTICE_M + 0.5).astype(int)
    la, lb = pa - ia * LATTICE_M, pb - ib * LATTICE_M  # distance to the nearest band axis of either family
    hb = BAND_M / 2
    in_a, in_b = np.abs(la) < hb, np.abs(lb) < hb     # band along b (a = const) / along a (b = const)
    band_a = in_a                                     # the a = const family runs through the crossings
    band_b = in_b & ~in_a
    band = band_a | band_b

    # ---- band setts: straight rows along the band, stones staggered row by row
    across = np.where(band_a, la, lb)
    along = np.where(band_a, pb - ia * LATTICE_M, pa - ib * LATTICE_M)
    fam = np.where(band_a, 0, 1)
    row = np.clip(np.floor((across + hb) / ROW_M).astype(int), 0, 4)
    ln = 2 * LATTICE_M / BAND_STONES
    off = hash01(row, fam, 7) * ln
    kk = np.floor((along - off) / ln).astype(int)
    t = (along - off) - kk * ln
    ra = (across + hb) - row * ROW_M
    dj_band = _rdist(np.minimum(t, ln - t), np.minimum(ra, ROW_M - ra), 0.010)
    # the b = const bands butt against the a = const band at a crossing
    dj_band = np.where(band_b, np.minimum(dj_band, np.abs(la) - hb), dj_band)
    sid_band = 500000 + fam * 100000 + row * 1000 + (kk % BAND_STONES)

    # ---- field setts: concentric segmental arcs, the fan turned by 90 degrees in every other field
    fa = pa - (np.floor(pa / LATTICE_M) + 0.5) * LATTICE_M      # field-centred coordinates
    fb = pb - (np.floor(pb / LATTICE_M) + 0.5) * LATTICE_M
    cls = (np.floor(pa / LATTICE_M).astype(int) + np.floor(pb / LATTICE_M).astype(int)) % 2
    hf = (LATTICE_M - BAND_M) / 2
    u = np.where(cls == 0, fa, fb)
    v = np.where(cls == 0, fb, -fa)
    cy = -1.55 * hf                                    # arc centre below the field: flat segmental arcs
    rho = np.hypot(u, v - cy)
    phi = np.arctan2(u, v - cy)
    arow = np.floor(rho / ROW_M).astype(int)
    rmid = (arow + 0.5) * ROW_M
    slen = 0.092 + 0.03 * hash01(arow, cls, 21)        # stone length along the arc, row by row
    s = phi * rmid + hash01(arow, cls, 22) * slen + 40.0
    ak = np.floor(s / slen).astype(int)
    st = s - ak * slen
    rr = rho - arow * ROW_M
    dj_field = _rdist(np.minimum(st, slen - st), np.minimum(rr, ROW_M - rr))
    dj_field = np.minimum(dj_field, hf - np.maximum(np.abs(fa), np.abs(fb)))     # cut stones against the band
    sid_field = cls * 200000 + arow * 1000 + (ak % 1000)

    sid = np.where(band, sid_band, sid_field)
    dj = np.where(band, dj_band, dj_field)
    r1 = hash01(sid, 1)
    shade = np.where(band[..., None], _pick(RED, r1), _pick(GREY, r1))
    jh = np.where(band, 0.0045, 0.006)                 # hand-laid granite: 8-11 mm joints
    alb, h, rough, block = _stone_surface(c, 30, sid, dj, jh, shade)
    return SurfaceSet("sett_lattice_tykocin", c, alb, h, rough, r1.astype(np.float32), 1 - block,
                      detail_mask=block, ao_scales=(0.004, 0.014, 0.05), ao_k=0.6)


def sett_rows(n=1024):
    """Small setts in straight staggered rows, neutral (modulation set, mean 0.5). Tile = 20 rows."""
    L = ROW_M * 20
    c = Ctx(n, n, L, L, seed=3252)
    X, Y = c.xy()
    X, Y = _warp(c, 92, X, Y)
    row = np.floor(Y / ROW_M).astype(int)
    ln = L / 17.0                                       # 113 mm stones
    off = hash01(row, 5) * ln
    kk = np.floor((X - off) / ln).astype(int)
    t = (X - off) - kk * ln
    ry = Y - row * ROW_M
    dj = _rdist(np.minimum(t, ln - t), np.minimum(ry, ROW_M - ry), 0.010)
    sid = (row % 20) * 1000 + (kk % 17)
    r1 = hash01(sid, 1)
    grey = np.array([[0.5, 0.5, 0.5], [0.44, 0.44, 0.44], [0.55, 0.55, 0.55], [0.40, 0.40, 0.40], [0.52, 0.52, 0.52]])
    alb, h, rough, block = _stone_surface(c, 60, sid, dj, 0.004, _pick(grey, r1))
    lum = alb.mean(-1)                                   # neutral: joints keep their darkness, no hue of their own
    alb = np.repeat(lum[..., None], 3, -1)
    alb, _ = calibrate(alb, 0.5)
    return SurfaceSet("sett_rows_tint", c, alb.astype(np.float32), h, rough, r1.astype(np.float32), 1 - block,
                      detail_mask=block, ao_scales=(0.004, 0.014, 0.05), ao_k=0.6)


def granite_honed(n=1024):
    """Honed grey granite of a monument plinth: interlocking feldspar / quartz / biotite grains, no joints. Neutral
    modulation map (mean 0.5), tile 0.8 m; the grains are too small to repeat visibly."""
    L = 0.8
    c = Ctx(n, n, L, L, seed=3253)
    warp = (0.0012 * noise(c, 1, 0.003, 0.02), 0.0012 * noise(c, 2, 0.003, 0.02))
    d1, d2, i1, _, _ = voronoi(c, 3, 0.0042, jitter=1.0, warp=warp)
    r = hash01(i1, 4)
    r2 = hash01(i1, 5)
    # light feldspar 52 %, grey quartz 33 %, black biotite / hornblende 15 %
    tone = np.where(r < 0.52, 0.66 + 0.10 * r2, np.where(r < 0.85, 0.44 + 0.10 * r2, 0.10 + 0.08 * r2))
    big, _, i2, _, _ = voronoi(c, 6, 0.011, jitter=1.0)            # scattered larger feldspar crystals
    tone = np.where(hash01(i2, 7) < 0.10, 0.72, tone)
    edge = sstep(0.0, 0.0006, 0.5 * (d2 - d1))                     # grain boundaries a touch darker
    tone = tone * (0.93 + 0.07 * edge) * (1 + 0.05 * noise(c, 8, 0.05, 0.4, beta=1.2))
    dark = (tone < 0.25).astype(np.float32)
    h = (-0.00015 * dark + 0.00004 * noise(c, 9, c.px * 2, 0.004, beta=0.4)).astype(np.float32)   # mica plucked by honing
    alb = np.repeat(tone[..., None], 3, -1).astype(np.float32)
    alb, _ = calibrate(alb, 0.5)
    rough = np.clip(0.34 + 0.20 * dark + 0.05 * noise(c, 10, 0.02, 0.3), 0.2, 0.8).astype(np.float32)
    return SurfaceSet("granite_honed_tint", c, alb, h, rough, r.astype(np.float32), dark, detail_mask=1 - dark,
                      ao_scales=(0.002, 0.006, 0.02), ao_k=0.2)


PLAZA_SETS = {
    "sett_lattice_tykocin": dict(
        fn=sett_lattice, tile_m=[round(TILE_M, 4), round(TILE_M, 4)], target=None, kind="tiling_set",
        uv="mesh_uv0_metres (plaza frame: paved_area uv_frame, lattice crossing at the origin)",
        slots=["plaza_sett_lattice"],
        note="ADR 0325: Plac Czarnieckiego, Tykocin. Light grey granite setts in segmental arcs inside a diagonal "
             "lattice (period 2.255 m, measured on the GUGiK orthophoto 2024) of 0.48 m bands of small red setts. "
             "Procedural; band width, sett sizes and colours WORKING_VALUE (Commons photo as reference only)."),
    "sett_rows_tint": dict(
        fn=sett_rows, tile_m=[round(ROW_M * 20, 4), round(ROW_M * 20, 4)], target=0.5, kind="modulation_set",
        uv="mesh_uv0_metres (u along the rows)",
        slots=["plaza_sett_red", "plaza_sett_grey"],
        note="ADR 0325: small setts in straight staggered rows, neutral modulation map (mean 0.5); colour from the "
             "manifest (red border band of the plaza, grey granite walks)."),
    "granite_honed_tint": dict(
        fn=granite_honed, tile_m=[0.8, 0.8], target=0.5, kind="modulation_set", uv="mesh_uv0_metres (u along, v up)",
        slots=["monument_granite"],
        note="ADR 0325: honed grey granite (feldspar / quartz / biotite grains 3-11 mm), neutral modulation map "
             "(mean 0.5); colour from the manifest. Plinth of the king's monument in Knyszyn."),
}
