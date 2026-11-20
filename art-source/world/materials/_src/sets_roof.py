"""Ceramic / cement roof tile sets (ADR 0316): S-tile (esowka), plain tile (karpiowka), flat interlocking tile
(zakladkowa). Procedural, no photo pixel is used; the owner photos (Data/raw/refs/owner-knyszyn-klattow-2026-11-19,
local only) and CC BY-SA frames were looked at for pattern, proportion and tone only.

Why (review D93 pkt 2): the 1.4 m `roof_tiles` set of ADR 0091 drew 7 x 4 identical tiles with a tone per tile on a
perfect lattice, so every slope read as an even grid ("krata") - flat rectangles in a checker of tones, the rolls
hardly visible. A real tile roof reads the other way round: the profile first (rolls / scallops with their own shade
and the dark hollows under every lower edge), the tone in soft clusters over many tiles, the course lines never
quite straight, single dark and pale tiles, lichen and moss where the water stays.

Like the other facade sets these are modulation maps (linear mean 0.5, tinted x 2 by the manifest colour).
UV = mesh TEXCOORD_0 in metres: u along the eave, v up the slope (streetscape.roofs.build).
Tile sizes are WORKING_VALUE inside the product ranges:
  esowka      cover width 0.20 m, gauge 0.35 m (holenderka / S-tile; PN-EN 1304 formats 20-24 x 33-40 cm)
  karpiowka   18 x 38 cm plain tile laid 'w luske' (double lap on every batten), gauge 0.15 m, courses half-offset
  zakladkowa  flat interlocking tile, cover width 0.233 m, gauge 0.35 m, courses half-offset (marsylka-like:
              two flat pans, a middle rib and a side roll)
"""
from __future__ import annotations

import numpy as np

from pbrkit import Ctx, SurfaceSet, noise, sstep, hash01, calibrate

MOD_MEAN = 0.5


def _finish(name, c, lum, h, rough, eid, joint, extra=None, ao_k=0.6):
    alb = np.clip(lum, 0, None)[..., None] * np.ones(3, np.float32)
    if extra is not None:
        alb = extra(alb)
    alb, _ = calibrate(alb.astype(np.float32), MOD_MEAN)
    return SurfaceSet(name, c, alb.astype(np.float32), h.astype(np.float32), np.clip(rough, 0.05, 1).astype(np.float32),
                      eid.astype(np.float32), np.clip(joint, 0, 1).astype(np.float32), ao_k=ao_k)


def _mix(alb, rgb, k):
    """Multiply the albedo by the tint rgb where the mask k (0..1) is set."""
    k = k[..., None]
    return alb * (1 - k) + alb * np.array(rgb, np.float32) * k


def _warp(c, L, row_wob, col_wob, seed0):
    """Slope coordinates (u, v) in metres with slow meanders: course lines sag and rise by +-row_wob over 0.7-3 m
    of eave, columns wander by +-col_wob up the slope (hand-laid battens are never ruler straight)."""
    X, Y = c.xy()
    v = L - Y
    vv = v + row_wob * 0.5 * noise(c, seed0, 0.7, min(3.0, L), beta=1.2, aniso=0.45)
    xx = X + col_wob * 0.5 * noise(c, seed0 + 1, 0.7, min(3.0, L), beta=1.2, aniso=2.2)
    return xx, vv


def _courses(vv, course, edge):
    """Resolve overlapping courses. edge(r) = offset (m, |.| < course / 2) of the lower edge of course r at every
    texel above its nominal line r * course; a texel belongs to the highest course whose edge lies below it.
    Returns (course index, metres above its own lower edge, metres below the edge of the course lying on it)."""
    r0 = np.floor(vv / course).astype(np.int64)
    e_m, e_0, e_p, e_pp = edge(r0 - 1), edge(r0), edge(r0 + 1), edge(r0 + 2)
    in_p = vv >= (r0 + 1) * course + e_p
    in_0 = vv >= r0 * course + e_0
    r = np.where(in_p, r0 + 1, np.where(in_0, r0, r0 - 1))
    e = np.where(in_p, e_p, np.where(in_0, e_0, e_m))
    e_up = np.where(in_p, e_pp, np.where(in_0, e_p, e_0))
    d = vv - r * course - e
    gap = (r + 1) * course + e_up - vv
    return r, d, gap


def _lichen(c, k, size, thr, soft=0.35):
    """Irregular blotches of crustose lichen: two bands of noise (specks at `size` m riding on patches 4-10 x that
    size), thresholded - single specks, groups that merge into crusts, bare stretches between them."""
    n = 0.75 * noise(c, k, size * 0.5, size * 2.5, beta=0.6) + 0.75 * noise(c, k + 50, size * 3.0, size * 10.0, beta=0.8)
    return sstep(thr, thr + soft, n)


# ---------------------------------------------------------------------------------------------------- esowka
def _s_profile(pu):
    """Cross-section of an S-tile over one cover width (pu 0..1) -> (height 0..1, roll mask 0..1): a round roll
    over 0..0.70 and a slightly dished pan over 0.70..1; the side lap sits where the roll meets the next pan."""
    roll = np.where(pu < 0.70, 0.5 - 0.5 * np.cos(2 * np.pi * pu / 0.70), 0.0)
    pan = np.where(pu >= 0.70, -0.08 * np.sin(np.pi * (pu - 0.70) / 0.30), 0.0)
    return roll + pan, roll


# age presets of the S-tile: `mid` = a ceramic roof 15-40 years old (the rule roofs), `old` = hand-laid, 60+ years
# (Dom Klattow, owner photos klattow-01 / -05)
_S_AGE = {
    "mid": dict(tone=0.15, cluster=0.20, dark=0.05, dark_k=0.24, pale=0.035, pale_k=0.20, jit_v=0.008, jit_u=0.003,
                tilt=0.7, row_wob=0.008, col_wob=0.003, pan=0.32, moss=0.0, lichen_thr=1.55, lichen_k=0.22,
                pale_lichen=0.10, soot=0.07, hue=0.5),
    "old": dict(tone=0.26, cluster=0.26, dark=0.14, dark_k=0.34, pale=0.05, pale_k=0.26, jit_v=0.013, jit_u=0.005,
                tilt=1.0, row_wob=0.014, col_wob=0.004, pan=0.34, moss=1.0, lichen_thr=1.05, lichen_k=0.36,
                pale_lichen=0.18, soot=0.09, hue=1.0),
}


def _s_tile(name, L, n, cols, rows, seed, age):
    A = _S_AGE[age]
    c = Ctx(n, n, L, L, seed=seed)
    wave, course = L / cols, L / rows
    xx, vv = _warp(c, L, A["row_wob"], A["col_wob"], 40)
    col = np.floor(xx / wave).astype(np.int64)
    colm = col % cols

    def edge(r):                                 # every tile hangs a little lower / higher than its neighbours
        return A["jit_v"] * (hash01(r % rows, colm, 21) - 0.5) * 2

    r, d, gap = _courses(vv, course, edge)
    row = r % rows
    tid = row * cols + colm
    pu = np.clip((xx - col * wave) / wave + A["jit_u"] / wave * (hash01(tid, 22) - 0.5) * 2, 0, 1)
    pv = d / course                              # 0 = exposed lower edge, 1 = under the next course
    prof, roll = _s_profile(pu)
    # the hollow of the roll above shows as a dark crescent on the course below; in the pan only a thin edge shadow
    r_up = (row + 1) % rows
    reach = (0.004 + 0.046 * roll ** 0.8) * (0.8 + 0.4 * hash01(r_up * cols + colm, 23))       # deepest under the crest
    hollow = sstep(1.0, 0.45, gap / reach)
    edge_line = sstep(0.007, 0.002, gap)
    shadow = np.clip(hollow + 0.35 * edge_line, 0, 1)
    lap = sstep(0.011, 0.003, np.abs(pu - 0.715) * wave)         # side lap: the roll's edge in the neighbour's pan
    t = hash01(tid, 1)
    tilt_u, tilt_v = hash01(tid, 2) - 0.5, hash01(tid, 3) - 0.5
    grain = noise(c, 1, c.px * 2, 0.012, beta=0.4)
    pores = noise(c, 2, 0.004, 0.03, beta=0.7)
    cluster = noise(c, 3, 0.5, min(2.8, L), beta=1.3)            # firing lots / weathering over many tiles
    streak = sstep(0.3, 2.0, noise(c, 4, 0.03, 0.9, beta=1.0, aniso=1.0 / 7.0))      # dirt runs down the slope
    dark = (hash01(tid, 5) < A["dark"]).astype(np.float32)       # soaked / sooty tiles
    pale = (hash01(tid, 6) > 1 - A["pale"]).astype(np.float32)   # replaced tiles
    lich = _lichen(c, 7, 0.016, A["lichen_thr"]) * sstep(-0.8, 0.6, cluster + 0.8 * (hash01(tid, 8) - 0.5))
    plich = _lichen(c, 9, 0.012, 1.9, 0.25) * A["pale_lichen"] / 0.18
    moss_n = noise(c, 10, 0.012, 0.25, beta=0.9)
    # moss keeps to the damp places: the pans and the laps under the lower edges, in patches of a few tiles
    moss = A["moss"] * np.clip(sstep(0.9, 1.9, moss_n + 0.8 * cluster) * (1 - roll) ** 2
                               + 0.6 * sstep(0.03, 0.0, gap) * sstep(0.4, 1.4, moss_n + 0.6 * cluster), 0, 1)
    h = (0.028 * prof + 0.016 * (1 - np.clip(pv, 0, 1.4)) - 0.004 * lap
         + A["tilt"] * (0.004 * tilt_u * (pu - 0.5) + 0.006 * tilt_v * (np.clip(pv, 0, 1) - 0.5))
         + 0.25e-3 * grain + 0.3e-3 * pores + 1.5e-3 * moss)
    bloom = noise(c, 12, 0.02, 0.12, beta=0.8)                   # pale mineral bloom / dust mottling on the faces
    lum = (1 + A["tone"] * (t - 0.5) + A["cluster"] * cluster * 0.5 + 0.035 * grain + 0.02 * pores + 0.05 * bloom)
    lum *= (1 - A["dark_k"] * dark) * (1 + A["pale_k"] * pale)
    lum *= 1 - A["pan"] * (1 - roll) ** 1.4                      # pans: less sky, the dirt stays there
    lum *= 1 + 0.12 * sstep(0.55, 1.0, roll)                     # crests: washed and sun-bleached
    lum *= (1 - 0.70 * shadow) * (1 - 0.22 * lap) * (1 - A["soot"] * streak * (0.4 + 0.6 * (1 - roll)))
    lum *= 1 - 0.10 * sstep(0.10, 0.0, pv)                       # weathered band at the exposed lower edge
    lum *= (1 - A["lichen_k"] * lich) * (1 + 0.30 * plich) * (1 - 0.30 * moss)
    rough = 0.80 + 0.08 * (1 - roll) + 0.08 * moss + 0.05 * lich

    def tint(alb):
        hue = hash01(tid, 11)
        out = _mix(alb, [1.07, 0.97, 0.87], A["hue"] * sstep(0.55, 1.0, hue))        # brighter orange tiles
        out = _mix(out, [0.93, 1.00, 1.10], A["hue"] * sstep(0.45, 0.0, hue))        # brown, greyed tiles
        out = _mix(out, [1.05, 0.98, 0.90], np.clip(0.5 * cluster, 0, 1) * 0.6)
        out = _mix(out, [0.86, 0.95, 1.06], dark * 0.6)
        out = _mix(out, [1.10, 1.00, 0.86], pale * 0.7)
        out = _mix(out, [0.80, 0.93, 1.04], lich * 0.8)                              # black-grey lichen crust
        out = _mix(out, [0.98, 1.14, 1.20], np.clip(plich, 0, 1) * 0.7)              # pale grey-green lichen
        return _mix(out, [0.70, 1.12, 0.78], moss * 0.75)                            # moss: olive over the red clay
    return _finish(name, c, lum, h, rough, t, shadow, extra=tint)


def roof_tiles(n=1024):
    """Ceramic S-tile (esowka), a roof a few decades old (ADR 0316; replaces the 1.4 m lattice of ADR 0091): roll
    pitch 0.20 m, gauge 0.35 m, rolls with dark pans and the hollow under every lower edge, tone in clusters, a few
    dark and pale tiles, dirt runs, sparse lichen. Tile 4.2 x 4.2 m (21 rolls x 12 courses)."""
    return _s_tile("roof_tiles", 4.2, n, 21, 12, 3160, "mid")


def roof_tiles_old(n=1024):
    """Old hand-laid S-tile (ADR 0305 Dom Klattow, rewritten in ADR 0316): as `roof_tiles` with uneven courses, every
    tile its own tone and tilt, sooty and replaced tiles, lichen crusts, moss in the pans and laps.
    Tile 2.8 x 2.8 m (14 rolls x 8 courses)."""
    return _s_tile("roof_tiles_old", 2.8, n, 14, 8, 3055, "old")


# ------------------------------------------------------------------------------------------------- karpiowka
def roof_karpiowka(n=1024):
    """Plain ceramic tile (karpiowka) laid in the scale pattern ("w luske"): tiles 0.183 m wide with a segmental
    lower edge, gauge 0.15 m, every course shifted by half a tile, so the roof reads as fish scales with a dark
    notch between the rounded corners. Butt joints 3 mm, drawn-clay brushing along the tile, tone in clusters,
    weathered lower edges, lichen. Tile 4.2 x 4.2 m (23 tiles x 28 courses). ADR 0316."""
    L, cols, rows = 4.2, 23, 28
    c = Ctx(n, n, L, L, seed=3161)
    w, course = L / cols, L / rows
    sag = 0.034                                   # rise of the segmental edge from its middle to the tile corner, m
    xx, vv = _warp(c, L, 0.005, 0.003, 40)

    def cell(r):
        xs = xx + 0.5 * w * (r % 2)
        k = np.floor(xs / w).astype(np.int64)
        return k % cols, xs - (k + 0.5) * w       # column, metres from the centre line of the tile

    def edge(r):
        k, dx = cell(r)
        return sag * (2 * dx / w) ** 2 + 0.004 * (hash01(r % rows, k, 21) - 0.5) * 2

    r, d, gap = _courses(vv, course, edge)
    row = r % rows
    k, dx = cell(r)
    tid = row * cols + k
    pv = d / course                               # 0 = lower edge; the notch shows the tile up to pv ~ 1.25
    joint = sstep(0.0030, 0.0012, 0.5 * w - np.abs(dx))                  # butt joint to the neighbour in the course
    shadow = np.clip(sstep(0.026, 0.003, gap) * 0.85 + sstep(0.007, 0.001, gap) * 0.4, 0, 1)
    t = hash01(tid, 1)
    tilt_u, tilt_v = hash01(tid, 2) - 0.5, hash01(tid, 3) - 0.5
    grain = noise(c, 1, c.px * 2, 0.012, beta=0.4)
    brush = noise(c, 2, 0.004, 0.02, beta=0.5, aniso=8.0)                # drawing marks run along the tile (v)
    cluster = noise(c, 3, 0.5, 2.8, beta=1.3)
    streak = sstep(0.4, 2.0, noise(c, 4, 0.03, 0.9, beta=1.0, aniso=1.0 / 7.0))
    dark = (hash01(tid, 5) < 0.06).astype(np.float32)
    pale = (hash01(tid, 6) > 0.965).astype(np.float32)
    lich = _lichen(c, 7, 0.03, 1.6) * sstep(-0.6, 0.9, cluster + 0.6 * (hash01(tid, 8) - 0.5))
    plich = _lichen(c, 9, 0.02, 2.1, 0.25) * 0.6
    edge_w = sstep(0.045, 0.0, d)                                         # the exposed lower 4 cm weather first
    moss = np.clip(sstep(0.012, 0.0, gap) * sstep(0.6, 1.8, noise(c, 10, 0.03, 0.5) + 0.8 * cluster), 0, 1) * 0.6
    h = (0.014 * (1 - np.clip(pv, 0, 1.6)) - 0.010 * joint + 0.0015 * (1 - (2 * dx / w) ** 2)      # slight camber
         + 0.003 * tilt_u * (2 * dx / w) + 0.004 * tilt_v * (np.clip(pv, 0, 1) - 0.5)
         + 0.25e-3 * grain + 0.35e-3 * brush + 1.0e-3 * moss)
    lum = 1 + 0.16 * (t - 0.5) + 0.07 * cluster + 0.035 * grain + 0.03 * brush
    lum *= (1 - 0.24 * dark) * (1 + 0.20 * pale)
    lum *= (1 - 0.68 * shadow) * (1 - 0.55 * joint) * (1 - 0.14 * edge_w) * (1 - 0.10 * streak)
    lum *= (1 - 0.36 * lich) * (1 + 0.28 * plich) * (1 - 0.30 * moss)
    rough = 0.80 + 0.06 * edge_w + 0.08 * moss + 0.05 * lich

    def tint(alb):
        hue = hash01(tid, 11)
        out = _mix(alb, [1.06, 0.97, 0.88], 0.6 * sstep(0.55, 1.0, hue))
        out = _mix(out, [0.94, 1.00, 1.09], 0.6 * sstep(0.45, 0.0, hue))
        out = _mix(out, [0.88, 0.96, 1.05], np.clip(dark * 0.6 + edge_w * 0.35, 0, 1))
        out = _mix(out, [1.10, 1.00, 0.86], pale * 0.7)
        out = _mix(out, [0.80, 0.93, 1.04], lich * 0.8)
        out = _mix(out, [0.98, 1.14, 1.20], np.clip(plich, 0, 1) * 0.7)
        return _mix(out, [0.70, 1.12, 0.78], moss * 0.75)
    return _finish("roof_karpiowka", c, lum, h, rough, t, np.maximum(shadow, joint), extra=tint)


# ------------------------------------------------------------------------------------------------ zakladkowa
def roof_zakladkowa(n=1024):
    """Flat interlocking tile (zakladkowa: cement or engobed ceramic, the brown / grey roofs of Podlasie houses):
    cover width 0.233 m, gauge 0.35 m, courses half-offset; a tile is two flat pans with a narrow rib between
    them, a raised side roll over the interlock and a thick nose at the lower edge. Even factory tone (little per-tile variation), but
    dust in the flutes, dirt runs, pale round lichen and moss along the laps of a shaded slope.
    Tile 4.2 x 4.2 m (18 tiles x 12 courses). ADR 0316."""
    L, cols, rows = 4.2, 18, 12
    c = Ctx(n, n, L, L, seed=3162)
    w, course = L / cols, L / rows
    xx, vv = _warp(c, L, 0.004, 0.003, 40)

    def cell(r):
        xs = xx + 0.5 * w * (r % 2)
        k = np.floor(xs / w).astype(np.int64)
        return k % cols, (xs - k * w) / w          # column, 0..1 across the cover width

    def edge(r):
        k, _ = cell(r)
        return 0.003 * (hash01(r % rows, k, 21) - 0.5) * 2


    r, d, gap = _courses(vv, course, edge)
    row = r % rows
    k, pu = cell(r)
    tid = row * cols + k
    pv = d / course
    # cross-section: side roll over the interlock (pu 0..0.15), two flat pans with a narrow rib between them
    # (pu 0.54..0.61); dust lies along the foot of the roll and of the rib
    side = np.where(pu < 0.15, 0.5 - 0.5 * np.cos(2 * np.pi * pu / 0.15), 0.0)
    rib = sstep(0.035, 0.012, np.abs(pu - 0.575))
    flute = np.clip(sstep(0.05, 0.0, np.abs(pu - 0.20)) + sstep(0.06, 0.02, np.abs(np.abs(pu - 0.575) - 0.07)), 0, 1)
    lapline = sstep(0.006, 0.0015, np.minimum(pu, 1 - pu) * w)                       # joint beside the side roll
    nose = sstep(0.030, 0.0, d)                                                      # thickened lower edge
    shadow = np.clip(sstep(0.022, 0.003, gap) * 0.8 + sstep(0.006, 0.001, gap) * 0.4, 0, 1)
    t = hash01(tid, 1)
    tilt_v = hash01(tid, 3) - 0.5
    grain = noise(c, 1, c.px * 2, 0.012, beta=0.3)
    sand = noise(c, 2, 0.003, 0.02, beta=0.2)                                        # cement face: open sand grain
    cluster = noise(c, 3, 0.6, 2.8, beta=1.3)
    streak = sstep(0.2, 1.8, noise(c, 4, 0.03, 1.0, beta=1.0, aniso=1.0 / 8.0))
    plich = _lichen(c, 9, 0.045, 1.7, 0.3) * sstep(-0.5, 1.0, cluster)
    moss = np.clip(sstep(0.016, 0.0, gap) * sstep(0.5, 1.7, noise(c, 10, 0.03, 0.5) + 0.9 * cluster), 0, 1) * 0.7
    h = (0.012 * (1 - np.clip(pv, 0, 1.2)) + 0.011 * side + 0.006 * rib + 0.003 * nose - 0.004 * lapline
         + 0.003 * tilt_v * (np.clip(pv, 0, 1) - 0.5) + 0.3e-3 * grain + 0.3e-3 * sand + 1.2e-3 * moss)
    lum = 1 + 0.07 * (t - 0.5) + 0.06 * cluster + 0.03 * grain + 0.03 * sand
    lum *= (1 - 0.10 * flute) * (1 + 0.05 * side + 0.04 * rib) * (1 - 0.40 * lapline)
    lum *= (1 - 0.66 * shadow) * (1 - 0.13 * streak * (0.5 + 0.5 * flute)) * (1 + 0.06 * nose)
    lum *= (1 + 0.22 * plich) * (1 - 0.30 * moss)
    rough = 0.84 + 0.05 * flute + 0.07 * moss

    def tint(alb):
        out = _mix(alb, [1.04, 0.99, 0.93], 0.5 * sstep(0.6, 1.0, hash01(tid, 11)))
        out = _mix(out, [0.96, 1.00, 1.05], np.clip(0.5 * streak + 0.4 * flute, 0, 1) * 0.5)   # grey dust film
        out = _mix(out, [0.98, 1.12, 1.12], np.clip(plich, 0, 1) * 0.7)
        return _mix(out, [0.72, 1.12, 0.78], moss * 0.75)
    return _finish("roof_zakladkowa", c, lum, h, rough, t, np.maximum(shadow, lapline), extra=tint)


ROOF_SETS = {
    "roof_tiles": dict(fn=roof_tiles, tile_m=[4.2, 4.2], slots=["roof_tiles_red"],
        note="ADR 0316: ceramic S-tile (esowka), roll pitch 0.20 m, gauge 0.35 m, clustered tone, hollows under the "
             "lower edges, sparse lichen (u along the eave, v up the slope)."),
    "roof_tiles_old": dict(fn=roof_tiles_old, tile_m=[2.8, 2.8], slots=["roof_tiles_old"],
        note="ADR 0305 / 0316: old hand-laid ceramic S-tile, roll 0.20 m, gauge 0.35 m, uneven courses, per-tile tone "
             "and tilt, lichen crusts, moss in the pans."),
    "roof_karpiowka": dict(fn=roof_karpiowka, tile_m=[4.2, 4.2], slots=["roof_karp_*"],
        note="ADR 0316: plain tile (karpiowka) in the scale pattern, tiles 0.183 m, gauge 0.15 m, half-offset "
             "courses, segmental lower edges."),
    "roof_zakladkowa": dict(fn=roof_zakladkowa, tile_m=[4.2, 4.2], slots=["roof_tiles_brown", "roof_cement_*"],
        note="ADR 0316: flat interlocking tile (zakladkowa, cement / engobed), cover 0.233 m, gauge 0.35 m, "
             "half-offset courses, two flat pans, a middle rib and a side roll."),
}
