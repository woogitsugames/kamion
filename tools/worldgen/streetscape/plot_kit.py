"""Plot kit atlas (ADR 0114 -> ADR 0124): ONE alpha-clip texture for everything that stands on a single-family plot -
fences of the Białystok typology (docs/refs/posesje-bialystok.md), gate infill, brick posts, steel / wood swatches,
thuja foliage, a leafy hedge, and plant cards (thujas, spruces, a big garden tree, fruit trees, shrubs, perennials).
One texture = one material (`plot_kit`) = one submesh of the chunk's `furniture` mesh, so a chunk full of plots costs
ONE draw.

Sources. Fences / brick / walls: drawn from primitives (numpy / PIL), no photos; the reference frames (Mapillary
CC BY-SA, Commons) are looked at for pattern, proportion and colour only - no pixel of them is used. Conifer foliage
(ADR 0124, review 0114 P1-r8-d/e "tekstura z fotograficznej bazy CC0"): photographed twigs of Poly Haven `fir_tree_01`
(CC0, `art-source/world/cc0/_raw/fir_tree_01/twig_{diff,alpha}.png`, outside git; docs/LICENSES.md) cut out by
connected component, recoloured to the thuja / blue-spruce palette and stamped back to front. When the raw files are
absent (clean checkout) the conifers fall back to drawn fronds - `SOURCE['conifer']` says which one was used.
Broadleaf leaves are drawn (lens-shaped leaves with a midrib, stamped in clusters): no CC0 leaf photo is in the repo.
Colours are sRGB albedo (material colour white), WORKING_VALUE read off the frames named per row.

Layout: 2048 x 2048. v never tiles; rows are separated by PAD px with replicated edges; v = 0 is the image bottom
(generator convention, gltf.py flips to glTF).
  * fence rows share a band in pairs (ADR 0124: the freed 450 px carry the plant cards): each is HALF the width and
    stands for HALF_M = 5.12 m - exactly one fence panel (plots.SEG_M), so a panel never wraps. `uspan(row, m0, m1)`;
  * `wall`, `brick`, `thuja`, `hedge` span the full width and tile in u (period KIT_M);
  * `sprites` / `tall` hold the plant cards: `sprite(name) -> (u0, u1, v0, v1)`, `SPRITE_M[name] -> (w m, h m)`.
    row(name) -> (v_bottom, v_top);  SWATCH[name] -> (u, v) of a flat colour (all vertices of a box pinned there)
"""
from __future__ import annotations

import functools
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

N = 2048
SS = 2                      # supersampling of the drawing canvas
KIT_M = 10.24               # metres across the atlas width (200 px / m)
HALF_M = KIT_M / 2          # metres a half-width fence row stands for = one fence panel
PAD = 10
BAY_M = KIT_M / 4           # post pitch drawn into the framed rows (chain-link, bars, lamellae, concrete): 2.56 m
# bands top to bottom: (names sharing the band, height px); ROW_H_M: metres a row stands for
_BANDS = [(("picket", "boards_rust"), 150), (("boards_brown", "chainlink"), 150), (("concrete", "bars"), 150),
          (("lamella", "boards_grey"), 150), (("wall",), 56), (("brick",), 160), (("swatch",), 28), (("thuja",), 180),
          (("hedge",), 170), (("sprites",), 256), (("tall",), 420)]
ROW_H_M = {"picket": 1.30, "boards_rust": 1.80, "boards_brown": 1.80, "chainlink": 1.50, "concrete": 1.60, "bars": 1.40,
           "lamella": 1.70, "boards_grey": 1.80, "wall": 1.80, "brick": 2.00, "swatch": 0.0, "thuja": 1.00, "hedge": 1.50,
           "sprites": 0.0, "tall": 0.0}
ROW_Y = {}                  # name -> (y0 px from the top, height px)
ROW_X = {}                  # name -> (x0 px, width px)
_y = PAD // 2
for _names, _h in _BANDS:
    for _k, _n in enumerate(_names):
        ROW_Y[_n] = (_y, _h)
        ROW_X[_n] = (_k * N // len(_names), N // len(_names))
    _y += _h + PAD
assert _y - PAD // 2 <= N, _y
HALF_ROWS = {n for names, _ in _BANDS if len(names) == 2 for n in names}

_SW = ["steel_black", "steel_green", "steel_graphite", "wood_brown", "wood_rust", "concrete", "soil", "galv",
       "bin_dark", "lid_yellow", "lid_brown", "trunk", "wood_grey", "rust"]
_SW_RGB = {"steel_black": (30, 30, 32), "steel_green": (28, 72, 52), "steel_graphite": (58, 60, 64),
           "wood_brown": (82, 56, 44), "wood_rust": (136, 64, 46), "concrete": (138, 135, 127), "soil": (60, 46, 36),
           "galv": (118, 122, 124), "bin_dark": (40, 44, 46), "lid_yellow": (186, 156, 44), "lid_brown": (96, 64, 44),
           "trunk": (66, 56, 48), "wood_grey": (112, 104, 94), "rust": (96, 60, 42)}
# plant cards: (row, name, width px, width m, height m)
_SPR = [("sprites", "apple_a", 400, 3.4, 2.6), ("sprites", "apple_b", 400, 3.0, 2.6), ("sprites", "shrub_a", 300, 1.7, 1.45),
        ("sprites", "shrub_b", 300, 1.5, 1.3), ("sprites", "flowers_a", 216, 0.9, 0.6), ("sprites", "flowers_b", 216, 0.9, 0.6),
        ("sprites", "flowers_c", 216, 0.9, 0.6),
        ("tall", "thuja_a", 200, 1.0, 2.1), ("tall", "thuja_b", 200, 1.0, 2.1), ("tall", "thuja_c", 180, 0.9, 2.1),
        ("tall", "spruce_a", 380, 3.4, 3.76), ("tall", "spruce_b", 340, 3.04, 3.76),
        # ADR 0163 (G7 #13 / #14, Ebben habit): whole crowns of the garden trees instead of the one umbrella `tree_a`
        # (10.5 x 5.9 m, W / H 1.78 - no Podlasie garden tree looks like that). Width / height of the card = the
        # habit: linden ovate dense 0.63, maple / chestnut / fruit round dense 0.71, birch narrow open 0.44.
        ("tall", "crown_ovoid", 264, 4.0, 6.36), ("tall", "crown_round", 300, 5.0, 7.0), ("tall", "crown_birch", 184, 3.2, 7.3)]
SPRITE = {}                 # name -> (u0, u1) (kept for callers that only need u)
SPRITE_ROW = {}
SPRITE_M = {}
_SPR_X = {}
_xs = {"sprites": 0, "tall": 0}
for _r, _n, _w, _wm, _hm in _SPR:
    _x = _xs[_r]
    SPRITE[_n] = ((_x + 3) / N, (_x + _w - 3) / N)
    SPRITE_ROW[_n] = _r
    SPRITE_M[_n] = (_wm, _hm)
    _SPR_X[_n] = (_x, _w)
    _xs[_r] = _x + _w
assert max(_xs.values()) <= N
# `tree_a` (plots.big_tree, the rule path of regions without an orthophoto canopy) now shows the round crown
SPRITE["tree_a"], SPRITE_ROW["tree_a"], SPRITE_M["tree_a"], _SPR_X["tree_a"] =     SPRITE["crown_round"], "tall", SPRITE_M["crown_round"], _SPR_X["crown_round"]
THUJA_GREEN_U = 0.86         # u < this: live foliage; above: a browned (dead) stretch of the thuja row
SOURCE = {"conifer": "unset"}
_RAW = Path(__file__).resolve().parents[3] / "art-source" / "world" / "cc0" / "_raw" / "fir_tree_01"


def row(name, inset_px=1.0):
    y0, h = ROW_Y[name]
    return (1.0 - (y0 + h - inset_px) / N, 1.0 - (y0 + inset_px) / N)


def uspan(name, m0, m1, mirror=False):
    """u of the stretch m0..m1 (metres along the fence) of a row. Half rows hold HALF_M metres and do not tile: the
    stretch is clamped into the row (a longer one is squeezed); full rows tile with period KIT_M."""
    x0, wpx = ROW_X[name]
    if name not in HALF_ROWS:
        return (m0 / KIT_M, m1 / KIT_M) if not mirror else (m1 / KIT_M, m0 / KIT_M)
    L = m1 - m0
    if L > HALF_M:
        m0, m1 = 0.0, HALF_M
    elif m1 > HALF_M:
        m0, m1 = HALF_M - L, HALF_M
    px = wpx / HALF_M
    u0 = (x0 + min(max(m0 * px, 1.5), wpx - 1.5)) / N
    u1 = (x0 + min(max(m1 * px, 1.5), wpx - 1.5)) / N
    return (u1, u0) if mirror else (u0, u1)


def sprite(name):
    """(u0, u1, v0, v1) of a plant card."""
    v0, v1 = row(SPRITE_ROW[name], 2.0)
    return SPRITE[name] + (v0, v1)


def _swatch_uv(name):
    k = _SW.index(name)
    y0, h = ROW_Y["swatch"]
    return ((k + 0.5) / len(_SW), 1.0 - (y0 + h / 2) / N)


SWATCH = {n: _swatch_uv(n) for n in _SW}


# ------------------------------------------------------------------------------------------------- painting helpers
def _noise(rng, h, w, sy, sx):
    """0..1 field, tileable in x."""
    a = ndimage.gaussian_filter(rng.random((h, w)), (sy, sx), mode=("nearest", "wrap"))
    lo, hi = a.min(), a.max()
    return (a - lo) / max(hi - lo, 1e-9)


def _rgba(h, w, rgb=(0, 0, 0), a=0.0):
    im = np.zeros((h, w, 4), np.float32)
    im[..., :3] = rgb
    im[..., 3] = a
    return im


def _grid(h, w, hm, per=KIT_M):
    """x (m), y (m, 0 = ground, up) of every canvas texel of a row standing for hm metres and per metres across."""
    x = (np.arange(w) + 0.5) / w * per
    y = (1.0 - (np.arange(h) + 0.5) / h) * hm
    return np.meshgrid(x, y)


def _weather(rgb, rng, h, w, bottom=0.25, grey=0.12):
    """Vertical grain / rain streaks, a darker and greener foot, a little overall dirt."""
    streak = _noise(rng, h, w, 40 * SS, 0.6 * SS)
    blot = _noise(rng, h, w, 14 * SS, 18 * SS)
    y = (np.arange(h) + 0.5)[:, None] / h
    foot = np.clip((y - (1 - bottom)) / bottom, 0, 1) ** 1.5
    k = (0.88 + 0.2 * streak) * (0.92 + 0.14 * blot) * (1 - 0.28 * foot)
    out = rgb * k[..., None]
    g = out.mean(-1, keepdims=True)
    out = out * (1 - grey * blot[..., None]) + g * grey * blot[..., None]
    out[..., 1] += 9.0 * foot * blot                      # algae at the foot
    return out


def _picket(rng, h, w, per=HALF_M):
    hm = ROW_H_M["picket"]
    X, Y = _grid(h, w, hm, per)
    n = 38
    pitch = per / n
    k = np.floor(X / pitch).astype(int)
    xc = (k + 0.5) * pitch
    half = 0.335 * pitch
    top = hm - 0.03 - 0.035 * rng.random(n)[k]            # hand-nailed: tops within 3.5 cm
    tip = top - np.abs(X - xc) * 0.9                      # pointed tops (Commons C04)
    on = (np.abs(X - xc) < half) & (Y < tip) & (Y > 0.03)
    base = np.array([118, 50, 38], np.float32) * (0.82 + 0.36 * rng.random(n))[k][..., None]
    peel = rng.random(n) < 0.16                           # paint gone: grey wood
    base[peel[k]] = np.array([112, 102, 92], np.float32) * (0.85 + 0.3 * rng.random())
    rgb = _weather(base, rng, h, w, bottom=0.2)
    sun = np.clip((Y - (top - 0.12)) / 0.12, 0, 1)        # bleached tips
    rgb = rgb * (1 + 0.16 * sun[..., None])
    im = _rgba(h, w)
    for yr in (0.24 * hm, 0.78 * hm):                     # rails behind the pickets
        rail = np.abs(Y - yr) < 0.035
        im[rail, :3] = np.array([62, 34, 28], np.float32) * (0.8 + 0.3 * _noise(rng, h, w, 2, 30)[rail][:, None])
        im[rail, 3] = 1.0
    im[on, :3] = rgb[on]
    im[on, 3] = 1.0
    nail = (np.abs(X - xc) < 0.006) & ((np.abs(Y - 0.24 * hm) < 0.006) | (np.abs(Y - 0.78 * hm) < 0.006))
    im[nail & on, :3] *= 0.45
    return im


def _boards(rng, h, w, name, col, per=HALF_M, grey=False):
    hm = ROW_H_M[name]
    X, Y = _grid(h, w, hm, per)
    n = 40
    pitch = per / n
    k = np.floor(X / pitch).astype(int)
    xin = X - k * pitch
    top = hm - 0.02 - (0.16 if grey else 0.09) * rng.random(n)[k] ** 2        # uneven tops (Mapillary P09)
    gap = xin < (0.004 + (0.014 if grey else 0.008) * (rng.random(n)[k] < (0.4 if grey else 0.25)))
    on = (~gap) & (Y < top)
    base = np.array(col, np.float32) * (0.80 + 0.38 * rng.random(n))[k][..., None]
    fade = rng.random(n) < (0.3 if grey else 0.16)
    base[fade[k]] = base[fade[k]] * 0.55 + np.array([120, 108, 96], np.float32) * 0.45
    rgb = _weather(base, rng, h, w, bottom=0.22, grey=0.3 if grey else 0.12)
    if grey:                                              # unpainted, silvered boards: knots, a dark damp foot, lichen
        knots = _noise(rng, h, w, 1.2 * SS, 0.8 * SS) > 0.83
        rgb[knots] *= 0.72
        lichen = (_noise(rng, h, w, 5 * SS, 5 * SS) > 0.7) & (Y < 0.7)
        rgb[lichen] = rgb[lichen] * 0.7 + np.array([70, 84, 52], np.float32) * 0.3
        miss = rng.random(n) < 0.05                       # a board gone
        on &= ~miss[k]
    im = _rgba(h, w)
    for yr in ((0.22 * hm, 0.80 * hm) if grey else ()):   # rails show through the missing boards
        rail = np.abs(Y - yr) < 0.04
        im[rail, :3] = np.array([72, 64, 56], np.float32)
        im[rail, 3] = 1.0
    im[on, :3] = rgb[on]
    im[on, 3] = 1.0
    for yr in (0.22 * hm, 0.80 * hm):                     # nail rows (rusty on the grey boards)
        nail = (np.abs(xin - pitch / 2) < 0.005) & (np.abs(Y - yr) < 0.006) & on
        im[nail, :3] *= 0.5
        if grey:
            run = (np.abs(xin - pitch / 2) < 0.004) & (Y < yr) & (Y > yr - 0.10) & on
            im[run, :3] = im[run, :3] * 0.75 + np.array([96, 58, 40], np.float32) * 0.25
    return im


def _chainlink(rng, h, w, per=HALF_M):
    hm = ROW_H_M["chainlink"]
    X, Y = _grid(h, w, hm, per)
    p = KIT_M / 170                                       # 60 mm diamond
    wire = 0.0042                                         # half width: drawn ~8 mm so one texel survives (real 3 mm)
    sagx = 0.012 * np.sin(Y / hm * math.pi) * np.sin(X / BAY_M * math.pi) ** 2      # the mesh bellies between the posts (P10)
    d1 = np.abs(((X + sagx + Y) / p + 0.5) % 1.0 - 0.5) * p * 0.7071
    d2 = np.abs(((X + sagx - Y) / p + 0.5) % 1.0 - 0.5) * p * 0.7071
    mesh = ((d1 < wire) | (d2 < wire)) & (Y > 0.05) & (Y < hm - 0.03)
    im = _rgba(h, w)
    tone = 0.85 + 0.3 * _noise(rng, h, w, 20, 20)
    im[mesh, :3] = np.array([40, 88, 64], np.float32) * tone[mesh][:, None]
    im[mesh, 3] = 1.0
    xb = np.abs((X / BAY_M + 0.5) % 1.0 - 0.5) * BAY_M
    frame = (xb < 0.025) | (np.abs(Y - (hm - 0.025)) < 0.022) | (np.abs(Y - 0.06) < 0.012)
    im[frame, :3] = np.array([28, 72, 52], np.float32) * tone[frame][:, None]
    im[frame, 3] = 1.0
    rust = (_noise(rng, h, w, 3, 3) > 0.72) & frame & ((Y < 0.4) | (np.abs(Y - (hm - 0.025)) < 0.022))
    im[rust, :3] = (92, 58, 40)
    return im


def _concrete(rng, h, w, per=HALF_M):
    hm = ROW_H_M["concrete"]
    X, Y = _grid(h, w, hm, per)
    bay = BAY_M
    xb = (X / bay) % 1.0
    plate = np.minimum(np.floor(Y / 0.5), 2)
    yin = Y - plate * 0.5
    base = np.array([122, 119, 112], np.float32) * (0.9 + 0.2 * _noise(rng, h, w, 30, 60))[..., None]
    base *= (0.94 + 0.1 * ((np.floor(X / bay) * 7 + plate * 3) % 5) / 4)[..., None]      # plate to plate
    rgb = _weather(base, rng, h, w, bottom=0.2, grey=0.05)
    relief = (np.sin(X / 0.32 * 2 * math.pi + plate * 1.7) > 0.86) | ((yin % 0.167) < 0.012)    # split-face emboss
    rgb[relief & (Y < 1.5)] *= 0.86
    joint = (yin < 0.012) | (Y > 1.5) & (Y < 1.512)
    rgb[joint] *= 0.55
    post = (np.abs(xb - 0.5) > 0.46)
    rgb[post] = (rgb[post] * 0.9 + 6)
    edge = (np.abs(np.abs(xb - 0.5) - 0.46) < 0.004)
    rgb[edge] *= 0.6
    run = np.clip(_noise(rng, h, w, 50, 1.5) - 0.55, 0, 1) * 2.2 * np.clip((Y - 0.3) / 1.2, 0, 1)    # run-off from the cap
    rgb *= (1 - 0.4 * run)[..., None]
    moss = np.clip(_noise(rng, h, w, 6 * SS, 9 * SS) - 0.45, 0, 1) * 2.0 * np.clip((0.45 - Y) / 0.45, 0, 1)
    rgb = rgb * (1 - 0.5 * moss[..., None]) + np.array([66, 78, 50], np.float32) * 0.5 * moss[..., None]
    im = _rgba(h, w, a=1.0)
    im[..., :3] = rgb
    return im


def _bars(rng, h, w, per=HALF_M):
    """Wrought bars with spear heads between flat rails. One card, both faces lit by the shader (ADR 0124: the two
    offset cards of ADR 0114 showed a grey 'ghost' of every spear head). Bars 22 mm, edges anti-aliased by the
    supersampled canvas; the inner corners stay square (PIL had rounded them)."""
    hm = ROW_H_M["bars"]
    X, Y = _grid(h, w, hm, per)
    n = 40
    pitch = per / n
    xc = (np.floor(X / pitch) + 0.5) * pitch
    dx = np.abs(X - xc)
    bar = (dx < 0.011) & (Y > 0.08) & (Y < hm - 0.085)
    yt = Y - (hm - 0.085)                                  # spear head: a leaf 85 mm tall, 44 mm wide, point up
    tip = (yt >= 0) & (yt < 0.085) & (dx < 0.022 * np.clip(1 - yt / 0.085, 0, 1) ** 0.8)
    collar = (np.abs(Y - (hm - 0.095)) < 0.008) & (dx < 0.016)
    flat = (np.abs(Y - 0.16) < 0.02) | (np.abs(Y - (hm - 0.22)) < 0.02)
    xb = np.abs((X / BAY_M + 0.5) % 1.0 - 0.5) * BAY_M
    post = (xb < 0.03) & (Y < hm - 0.03)
    on = bar | tip | flat | post | collar
    im = _rgba(h, w)
    tone = 0.8 + 0.5 * _noise(rng, h, w, 12, 12)
    im[on, :3] = np.array([30, 30, 32], np.float32) * tone[on][:, None]
    im[on, 3] = 1.0
    rust = (_noise(rng, h, w, 2.5, 2.5) > 0.74) & on & ((np.abs(Y - 0.16) < 0.05) | (Y < 0.14) | (np.abs(Y - (hm - 0.22)) < 0.03))
    im[rust, :3] = (78, 48, 34)
    return im


def _lamella(rng, h, w, per=HALF_M):
    hm = ROW_H_M["lamella"]
    X, Y = _grid(h, w, hm, per)
    pitch = hm / 14
    yin = Y % pitch
    slat = yin > 0.022
    xb = np.abs((X / BAY_M + 0.5) % 1.0 - 0.5) * BAY_M
    post = xb < 0.03
    base = np.array([60, 62, 66], np.float32) * (0.9 + 0.2 * _noise(rng, h, w, 3, 80))[..., None]
    base *= (0.86 + 0.2 * np.clip(yin / pitch, 0, 1))[..., None]                 # each slat lighter at its top edge
    dust = np.clip((0.35 - Y) / 0.35, 0, 1)[..., None]
    base = base * (1 - 0.3 * dust) + np.array([120, 110, 95], np.float32) * 0.3 * dust
    im = _rgba(h, w)
    on = slat | post
    im[on, :3] = base[on]
    im[post, :3] *= 0.8
    im[on, 3] = 1.0
    return im


def _wall(rng, h, w):
    hm = ROW_H_M["wall"]
    X, Y = _grid(h, w, hm)
    base = np.array([98, 99, 101], np.float32) * (0.9 + 0.2 * _noise(rng, h, w, 6, 40))[..., None]
    rgb = _weather(base, rng, h, w, bottom=0.18, grey=0.03)
    run = np.clip(_noise(rng, h, w, 30, 1.2) - 0.5, 0, 1) * 2.0
    rgb *= (1 - 0.36 * run)[..., None]
    rgb[Y > hm - 0.10] = np.array([70, 70, 72], np.float32)                      # coping
    im = _rgba(h, w, a=1.0)
    im[..., :3] = rgb
    return im


def _brick(rng, h, w):
    hm = ROW_H_M["brick"]
    X, Y = _grid(h, w, hm)
    nc, nb = 27, 39
    ch, bl = hm / nc, KIT_M / nb
    c = np.floor(Y / ch).astype(int)
    xs = X + (c % 2) * bl / 2
    b = np.floor(xs / bl).astype(int) % nb
    yin, xin = Y - c * ch, xs % bl
    tone = rng.random((nc, nb))
    col = np.array([138, 70, 52], np.float32) * (0.74 + 0.44 * tone[c, b])[..., None]
    burnt = tone[c, b] > 0.86
    col[burnt] = np.array([92, 54, 46], np.float32)
    pale = tone[c, b] < 0.08                                                     # efflorescence / a patched brick
    col[pale] = col[pale] * 0.6 + np.array([168, 150, 136], np.float32) * 0.4
    col = col * (0.90 + 0.2 * _noise(rng, h, w, 1.5, 1.5))[..., None]
    mortar = (yin < 0.011) | (xin < 0.011)
    col[mortar] = np.array([138, 132, 122], np.float32) * (0.9 + 0.2 * rng.random())
    grime = np.clip(_noise(rng, h, w, 40 * SS, 2.0 * SS) - 0.5, 0, 1) * 1.6      # rain streaks under the cap
    col *= (1 - 0.3 * grime * np.clip((Y - 0.2) / 1.2, 0, 1))[..., None]
    y = np.clip((0.4 - Y) / 0.4, 0, 1)[..., None]
    moss = np.clip(_noise(rng, h, w, 5 * SS, 8 * SS) - 0.4, 0, 1)[..., None] * 1.6 * y
    col = col * (1 - 0.26 * y)                                                   # damp foot
    col = col * (1 - 0.45 * moss) + np.array([64, 76, 48], np.float32) * 0.45 * moss
    im = _rgba(h, w, a=1.0)
    im[..., :3] = col
    return im


def _swatches(rng, h, w):
    im = _rgba(h, w, a=1.0)
    sw = w // len(_SW)
    tone = 0.94 + 0.12 * _noise(rng, h, w, 4, 4)
    for k, n in enumerate(_SW):
        im[:, k * sw:(k + 1) * sw if k < len(_SW) - 1 else w, :3] = np.array(_SW_RGB[n], np.float32)
    im[..., :3] *= tone[..., None]
    return im


def _pil(h, w):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def _jit(c, rng, k=0.16):
    f = 1 + rng.uniform(-k, k)
    return tuple(int(min(255, max(0, v * f))) for v in c) + (255,)


# ------------------------------------------------------------------------------------------------- foliage stamps
@functools.lru_cache(maxsize=1)
def _twigs():
    """Photographed fir twigs (Poly Haven fir_tree_01, CC0) cut out as RGBA stamps, tip up, colour normalised to a
    mean of 1 (the caller tints). None when the raw files are not there."""
    d, a = _RAW / "twig_diff.png", _RAW / "twig_alpha.png"
    if not (d.exists() and a.exists()):
        return None
    rgb = np.asarray(Image.open(d).convert("RGB"), np.float32)
    al = np.asarray(Image.open(a).convert("L"), np.float32) / 255.0
    H, W = al.shape
    m = al > 0.5
    m[:, : int(W * 0.14)] = False                         # the trunk strip of the source atlas
    m[int(H * 0.86):, :] = False                          # branch / bark strips
    lab, n = ndimage.label(ndimage.binary_dilation(m, iterations=2))
    out = []
    for k, sl in enumerate(ndimage.find_objects(lab)):
        mm = (lab[sl] == k + 1) & m[sl]
        if mm.sum() < 0.0012 * H * W:
            continue
        c = rgb[sl].copy()
        lum = c @ np.array([0.30, 0.59, 0.11], np.float32)
        g = np.clip(lum / max(float(lum[mm].mean()), 1.0), 0.35, 1.7)      # luminance detail only, mean 1: the caller's
        st = np.zeros(mm.shape + (4,), np.float32)                         # tint carries the hue (thuja / blue spruce)
        st[..., :3] = g[..., None]
        st[..., 3] = al[sl] * mm
        out.append(st)
    return out or None


def _leaf_stamps(rng, n=10):
    """Drawn broadleaf leaves: a lens-shaped blade with a lighter midrib and a darker lower half, tip up, mean ~1."""
    out = []
    for k in range(n):
        h, w = 64, 30 + int(rng.integers(0, 14))
        im = Image.new("L", (w, h), 0)
        d = ImageDraw.Draw(im)
        bulge = 0.36 + 0.2 * rng.random()
        pts = [(w / 2 + s * (w / 2 - 1) * math.sin(math.pi * t) ** (0.8 + 0.5 * bulge) * (1 - 0.25 * t), h - 2 - t * (h - 4))
               for s in (-1, 1) for t in (np.linspace(0, 1, 14) if s < 0 else np.linspace(1, 0, 14))]
        d.polygon(pts, fill=255)
        a = np.asarray(im, np.float32) / 255.0
        x = (np.arange(w) + 0.5)[None, :] / w - 0.5
        y = (np.arange(h) + 0.5)[:, None] / h
        tone = 0.92 + 0.18 * (x > 0) + 0.10 * (1 - y)      # one half catches the light, the tip is paler
        tone = np.where(np.abs(x) < 0.035, tone + 0.22, tone)                    # midrib
        tone = tone * (1 - 0.10 * np.abs(np.sin(y * 16 + x * 9)))               # side veins
        st = np.zeros((h, w, 4), np.float32)
        st[..., :3] = tone[..., None] * np.array([1.0, 1.0, 1.0], np.float32)
        st[..., 3] = a
        out.append(st)
    return out


class _Stamper:
    """Pastes rotated / scaled / tinted stamps onto a float RGBA canvas (alpha-over), optionally wrapping in x."""

    def __init__(self, canvas, stamps, wrap=False):
        self.c = canvas
        self.h, self.w = canvas.shape[:2]
        self.stamps = stamps
        self.wrap = wrap
        self._cache = {}

    def _get(self, k, length, ang):
        qa, ql = int(round(ang / 0.2618)) % 24, max(4, int(round(length / 3.0)) * 3)       # 15 deg / 3 px bins
        key = (k, ql, qa)
        s = self._cache.get(key)
        if s is None:
            st = self.stamps[k]
            sc = ql / st.shape[0]
            im = Image.fromarray(np.clip(np.concatenate([st[..., :3] * 127.5, st[..., 3:] * 255.0], -1), 0, 255).astype(np.uint8), "RGBA")
            # Pillow resizes RGBA through premultiplied alpha itself; the stamp is premultiplied after the transforms
            im = im.resize((max(2, int(round(st.shape[1] * sc))), ql), Image.BILINEAR).rotate(-math.degrees(qa * 0.2618), Image.BILINEAR, expand=True)
            s = np.asarray(im, np.float32) / 255.0
            s[..., :3] *= 2.0 * s[..., 3:]                 # back to mean ~1, premultiplied
            self._cache[key] = s
        return s

    def put(self, k, x, y, length, ang, tint):
        """Stamp k with its base at (x, y) px, pointing at angle ang (0 = up, + = clockwise), length px, RGB tint 0..255."""
        s = self._get(k, length, ang)
        sh, sw = s.shape[:2]
        # centre of the stamp = base + half the length along the direction
        cx = x + math.sin(ang) * length / 2
        cy = y - math.cos(ang) * length / 2
        x0, y0 = int(round(cx - sw / 2)), int(round(cy - sh / 2))
        for dx in ((-self.w, 0, self.w) if self.wrap else (0,)):
            xa, ya = x0 + dx, y0
            xs0, ys0 = max(0, -xa), max(0, -ya)
            xs1, ys1 = min(sw, self.w - xa), min(sh, self.h - ya)
            if xs1 <= xs0 or ys1 <= ys0:
                continue
            src = s[ys0:ys1, xs0:xs1]
            dst = self.c[ya + ys0:ya + ys1, xa + xs0:xa + xs1]
            a = src[..., 3:4]
            dst[..., :3] = src[..., :3] * np.asarray(tint, np.float32) + dst[..., :3] * (1 - a)
            dst[..., 3:4] = a + dst[..., 3:4] * (1 - a)


def _conifer_stamps(rng):
    tw = _twigs()
    if tw is not None:
        SOURCE["conifer"] = "polyhaven fir_tree_01 twig (CC0)"
        return tw
    SOURCE["conifer"] = "drawn fronds (raw CC0 twig not found)"
    out = []
    for k in range(6):                                    # drawn frond: a stem with side shoots
        h, w = 96, 64
        im = Image.new("L", (w, h), 0)
        d = ImageDraw.Draw(im)
        d.line([(w / 2, h - 1), (w / 2, 2)], fill=255, width=3)
        for j in range(1, 12):
            f = j / 12
            L = (0.46 - 0.3 * f) * w * rng.uniform(0.8, 1.2)
            y = h - f * h
            for sg in (-1, 1):
                d.line([(w / 2, y), (w / 2 + sg * L, y - L * 0.8)], fill=255, width=2)
        st = np.zeros((h, w, 4), np.float32)
        st[..., :3] = 1.0
        st[..., 3] = np.asarray(im, np.float32) / 255.0
        out.append(st)
    return out


def _thuja(rng, h, w):
    """Tileable thuja foliage (the core shell of a plant): twigs pointing up and out, stamped back to front over a
    dark interior; ~5 % holes onto that interior. u > THUJA_GREEN_U: browned."""
    st = _conifer_stamps(rng)
    c = _rgba(h, w, (22, 36, 22), 1.0)
    S = _Stamper(c, st, wrap=True)
    ppm = w / KIT_M
    live = [(30, 48, 28), (40, 62, 34), (50, 76, 40), (64, 90, 46)]
    dead = [(60, 46, 30), (96, 72, 44), (122, 92, 54), (140, 110, 66)]
    n = 5200
    for i in range(n):
        x, y = rng.uniform(0, w), rng.uniform(0.0, 1.12 * h)
        pal = dead if x / w > THUJA_GREEN_U + 0.01 else live
        lvl = min(3, int(i / n * 4))
        col = np.array(pal[lvl], np.float32) * rng.uniform(0.86, 1.14)
        S.put(int(rng.integers(len(st))), x, y, rng.uniform(0.11, 0.2) * ppm, rng.normal(0, 0.42), col)
    hole = (_noise(rng, h, w, 1.6 * SS, 1.6 * SS) > 0.78) & (c[..., :3].sum(-1) < 100)
    c[hole, 3] = 0.0
    return c


def _body_mask(h, w, prof, rng, ragged=0.0):
    """Mask of a plant silhouette: prof(f) -> half width (0..1 of w / 2) at height fraction f (0 = bottom)."""
    y = (np.arange(h) + 0.5)[:, None] / h
    f = 1.0 - y
    x = np.abs((np.arange(w) + 0.5)[None, :] / w - 0.5) * 2.0
    hw = np.vectorize(prof)(f)
    if ragged:
        hw = hw * (1 + ragged * (_noise(rng, h, w, 3 * SS, 0.01)[:, :1] - 0.5) * 2)
    return x < hw


def _thuja_card(rng, h, w, variant):
    """Silhouette card of a columnar thuja: a ragged outline of twig tips around a solid dark body, blunt rounded top."""
    st = _conifer_stamps(rng)
    c = _rgba(h, w)
    bulge = {0: 0.0, 1: 0.10, 2: 0.05}[variant]
    ph = rng.uniform(0, 6.28)

    def prof(f):
        f = f / 0.90                                       # the tip twigs need the last tenth of the card
        base = (0.74 + 0.20 * (f / 0.16)) if f < 0.16 else 0.94 * math.sqrt(max(1.0 - ((f - 0.16) / 0.84) ** 2.3, 0.0))
        return max(base * (1 + bulge * math.sin(f * 9.0 + ph)) * 0.72, 0.0)
    body = _body_mask(h, w, lambda f: prof(f) * 0.80, rng)
    c[body, :3] = (24, 38, 24)
    c[body, 3] = 1.0
    S = _Stamper(c, st)
    live = [(28, 46, 27), (38, 60, 33), (50, 76, 40), (66, 92, 48)]
    dead = [(64, 48, 32), (100, 76, 46), (126, 96, 56), (144, 114, 70)]
    n = 900
    brown = (rng.uniform(0.2, 0.8), rng.uniform(0.25, 0.6)) if variant == 2 else None
    tl = 0.2 * w / 1.0 * 1.0                              # twig length px (card stands for ~1 m across)
    for i in range(n):
        f = rng.uniform(0.0, 0.885)
        hwf = prof(f)
        xo = rng.uniform(-1, 1) * hwf
        lvl = min(3, int(i / n * 4))
        edge = abs(xo) / max(hwf, 1e-3)
        pal = live
        if brown is not None and abs(f - brown[1]) < 0.16 and (xo > 0) == (brown[0] > 0.5) and edge > 0.2:
            pal = dead
        col = np.array(pal[lvl], np.float32) * rng.uniform(0.86, 1.14) * (0.86 + 0.2 * f) * (0.9 + 0.16 * edge)
        ang = xo / max(hwf, 1e-3) * 0.75 + rng.normal(0, 0.28)
        S.put(int(rng.integers(len(st))), w / 2 + xo * w / 2, h - f * h, tl * rng.uniform(0.6, 1.0), ang, col)
    return c


def _spruce_card(rng, h, w):
    """Silhouette card of a blue spruce (świerk kłujący): whorls of boughs reaching out and slightly down, tips turned
    up, a scalloped outline with gaps between the whorls, a pointed leader."""
    st = _conifer_stamps(rng)
    c = _rgba(h, w)
    tiers = 9
    ph = rng.uniform(0, 3.1)

    def prof(f):
        return max((1 - f) ** 0.92 * 0.90 * (0.70 + 0.30 * abs(math.sin(f * tiers * math.pi + ph))) * (1 + 0.08 * math.sin(f * 23 + ph)) + 0.012, 0.0)
    # ADR 0170: opaque body out to 0.74 of the outline (was 0.62: the thin scalloped rim lost its alpha coverage in the
    # mips and the cone read half-transparent from 40 m on)
    body = _body_mask(h, w, lambda f: prof(f) * 0.74 + 0.01, rng)
    # ADR 0159 (REVIEW s16-world-int P1, SBS 1801374 / 182011: "turkusowe polprzezroczyste stozki"): with G = B the
    # cards read turquoise in sun on Low (palette up to 72 / 96 / 94). Grey-green with a slight blue cast, darker
    # (a blue spruce among garden trees is a dark cone, not a cyan one). WORKING_VALUE
    # ADR 0170 (review s17 0163 P2 "blady, sinawy swierk"): G7-P11 / P12 spruces are dark, saturated blue-green
    # (shade ~ 25 / 40 / 38, lit ~ 55 / 80 / 70 on the photos, WORKING_VALUE); the 0159 palette was greyer and lighter
    c[body, :3] = (13, 24, 19)
    c[body, 3] = 1.0
    S = _Stamper(c, st)
    pal = [(15, 28, 22), (22, 40, 31), (32, 54, 43), (46, 70, 58)]
    n = 2600
    tl = 0.42 * w / 3.4
    for i in range(n):
        f = rng.uniform(0.02, 0.97) ** 1.15
        hwf = prof(f)
        xo = rng.uniform(-1, 1) * hwf
        lvl = min(3, int(i / n * 4))
        edge = abs(xo) / max(hwf, 1e-3)
        col = np.array(pal[lvl], np.float32) * rng.uniform(0.85, 1.15) * (0.84 + 0.24 * f) * (0.86 + 0.2 * edge)
        ang = math.copysign(1.0, xo) * (0.5 + 1.5 * edge - 0.5 * f) + rng.normal(0, 0.45)     # boughs reach out and droop
        S.put(int(rng.integers(len(st))), w / 2 + xo * w / 2, h - f * h, tl * rng.uniform(0.6, 1.1) * (1 - 0.4 * f), ang, col)
    S.put(0, w / 2, h * 0.07, tl * 0.9, 0.0, np.array(pal[3], np.float32))       # leader
    return c


def _leafy(c, rng, x0, wpx, h, leaf_rgb, blobs, leaf_px, n_per=46, frame=None, stems=False, dots=None, shade=0.55):
    """A broadleaf crown inside [x0, x0 + wpx] x [0, h] of canvas c: branch frame, then clusters of drawn leaves back
    to front (lower / inner clusters darker). blobs: [(cx, cy, r) px]; dots: (rgb, count, r px) flowers / fruit."""
    stamps = _leaf_stamps(rng)
    S = _Stamper(c, stamps)
    if frame:
        im = Image.fromarray(np.clip(c * np.array([1, 1, 1, 255], np.float32), 0, 255).astype(np.uint8), "RGBA")
        d = ImageDraw.Draw(im)
        for (xa, ya, xb, yb, wd) in frame:
            d.line([(xa, ya), (xb, yb)], fill=(58, 48, 40, 255), width=max(2, int(wd)))
        c[...] = np.asarray(im, np.float32) / np.array([1, 1, 1, 255], np.float32)
    order = sorted(range(len(blobs)), key=lambda i: -blobs[i][1])                # low clusters first
    ymin = min(b[1] - b[2] for b in blobs)
    ymax = max(b[1] + b[2] for b in blobs)
    for rank, i in enumerate(order):
        bx, by, br = blobs[i]
        lvl = rank / max(len(blobs) - 1, 1)
        for j in range(n_per):
            a, r = rng.uniform(0, 6.2832), br * math.sqrt(rng.random())
            lx, ly = bx + math.cos(a) * r, by + math.sin(a) * r * 0.85
            if not (x0 + leaf_px < lx < x0 + wpx - leaf_px and leaf_px < ly < h - 2):
                continue
            up = 1 - (ly - ymin) / max(ymax - ymin, 1)     # 1 at the top of the crown
            k = (shade + (1 - shade) * (0.55 * lvl + 0.45 * up)) * rng.uniform(0.82, 1.16) * (0.8 + 0.2 * j / n_per)
            hue = rng.uniform(-1, 1)
            col = np.array(leaf_rgb, np.float32) * k + np.array([10, 4, -8], np.float32) * hue
            S.put(int(rng.integers(len(stamps))), lx, ly, leaf_px * rng.uniform(0.75, 1.25), rng.uniform(0, 6.2832), col)
    if dots is not None:
        rgb, cnt, rr = dots
        im = Image.fromarray(np.clip(c * np.array([1, 1, 1, 255], np.float32), 0, 255).astype(np.uint8), "RGBA")
        d = ImageDraw.Draw(im)
        for _ in range(cnt):
            bx, by, br = blobs[int(rng.integers(len(blobs)))]
            a, r = rng.uniform(0, 6.2832), br * math.sqrt(rng.random()) * 0.8
            fx, fy = bx + math.cos(a) * r, by + math.sin(a) * r * 0.8
            if x0 + rr + 2 < fx < x0 + wpx - rr - 2 and rr + 2 < fy < h - rr - 2:
                d.ellipse([fx - rr, fy - rr, fx + rr, fy + rr], fill=_jit(rgb, rng, 0.15))
        c[...] = np.asarray(im, np.float32) / np.array([1, 1, 1, 255], np.float32)


def _crown_blobs(rng, x0, wpx, h, n, top=0.04, bottom=0.70, dome=False, rr=(0.10, 0.17)):
    cx = x0 + wpx / 2
    out = []
    for i in range(n):
        a, r = rng.uniform(0, 6.2832), math.sqrt(rng.random())
        br = rng.uniform(*rr) * wpx
        if dome:
            bx = cx + (rng.random() * 2 - 1) * (wpx / 2 - br - 3)
            lim = 1 - ((bx - cx) / (wpx * 0.5)) ** 2
            by = h * (1.0 - (0.12 + 0.80 * rng.random() ** 0.8) * max(lim, 0.1))
        else:
            bx = cx + math.cos(a) * r * (wpx / 2 - br - 3)
            cy = h * (top + bottom) / 2
            by = cy + math.sin(a) * r * (h * (bottom - top) / 2 - br * 0.6)
        out.append((bx, max(by, br * 0.8 + 3), br))
    return out


def _sprites(rng, h, w):
    c = _rgba(h, w)
    s = w / N
    for name in ("apple_a", "apple_b", "shrub_a", "shrub_b", "flowers_a", "flowers_b", "flowers_c"):
        x0, wpx = _SPR_X[name][0] * s, _SPR_X[name][1] * s
        cx = x0 + wpx / 2
        if name.startswith("apple"):
            frame = []
            for k in range(7):
                a = -math.pi / 2 + (k - 3) * 0.33 + rng.normal(0, 0.06)
                L = h * rng.uniform(0.45, 0.72)
                frame.append((cx, h, cx + math.cos(a) * L * 0.8, h + math.sin(a) * L, h * 0.02))
            blobs = _crown_blobs(rng, x0, wpx, h, 34, top=0.03, bottom=0.80, rr=(0.085, 0.14))
            leaf = (70, 100, 46) if name == "apple_a" else (82, 106, 54)
            _leafy(c, rng, x0, wpx, h, leaf, blobs, 0.085 * wpx / SPRITE_M[name][0] * 1.5, n_per=52, frame=frame,
                   dots=((150, 64, 46), 7, 0.007 * wpx) if name == "apple_a" else None)
        elif name.startswith("shrub"):
            blobs = _crown_blobs(rng, x0, wpx, h, 34, dome=True, rr=(0.10, 0.16))
            leaf = (58, 92, 42) if name == "shrub_a" else (96, 58, 52)          # b: berberis, red-brown leaves
            _leafy(c, rng, x0, wpx, h, leaf, blobs, 0.07 * wpx / SPRITE_M[name][0] * 1.5, n_per=60, shade=0.5)
        else:
            col = {"flowers_a": (214, 124, 34), "flowers_b": (220, 190, 56), "flowers_c": (196, 108, 146)}[name]
            blobs = _crown_blobs(rng, x0, wpx, h, 16, dome=True, rr=(0.08, 0.13))
            _leafy(c, rng, x0, wpx, h, (58, 96, 42), blobs, 0.10 * wpx / 0.9, n_per=30, shade=0.6,
                   dots=(col, 34, 0.028 * wpx))
    return c


# ADR 0163: silhouettes of whole crowns, bottom -> top (t 0..1) -> half width (0..1). Sources: G7 #14 (Ebben habit:
# linden ovate and dense, maple / horse chestnut round-oval and dense, birch narrow-ovate and open) and the Bialystok
# measurements G7-T01..T04 (crown starts low: no umbrella on a bare stem).
def _crown_hw(kind, t):
    t = min(max(float(t), 0.0), 1.0)
    if kind == "ovoid":                                   # widest at 0.34 of the crown height, a rounded point on top
        return 0.30 + 0.70 * (t / 0.34) ** 0.7 if t < 0.34 else max(1.0 - ((t - 0.34) / 0.66) ** 1.9, 0.0) ** 0.62
    if kind == "round":                                   # widest at 0.46, a flatter underside, a broad dome
        return 0.34 + 0.66 * (t / 0.46) ** 0.6 if t < 0.46 else max(1.0 - ((t - 0.46) / 0.54) ** 2.2, 0.0) ** 0.5
    if t < 0.45:                                          # birch: slim foot, widest in the middle, a spire
        return 0.22 + 0.78 * (t / 0.45) ** 0.8
    return max(1.0 - ((t - 0.45) / 0.55) ** 1.6, 0.0) ** 0.75


_CROWN = {  # leaf rgb, clusters, leaves per cluster, cluster radius (share of width), darkest shade, opaque interior
    "ovoid": dict(leaf=(60, 92, 42), n=260, per=34, rr=(0.07, 0.115), shade=0.36, fill=0.66, stem=(58, 48, 40), lm=0.075, lobes=0.13),
    "round": dict(leaf=(66, 98, 46), n=290, per=34, rr=(0.065, 0.105), shade=0.38, fill=0.66, stem=(60, 50, 42), lm=0.085, lobes=0.15),
    "birch": dict(leaf=(98, 126, 58), n=210, per=26, rr=(0.075, 0.125), shade=0.58, fill=0.0, stem=(204, 200, 188), lm=0.06, lobes=0.20),
}


def _crown_card(rng, h, w, kind):
    """One whole crown (ADR 0163), foot of the crown at the bottom edge: the stem and the limbs that carry it, a dark
    interior for the dense habits (no sky through a linden) and leaf clusters filling the habit's silhouette. Every
    cluster is a lobe of its own depth (nearer = lighter, lit from above and from one side), the outline belongs to
    clusters that stand proud of it, and each side wanders by `lobes` (no ball on a stick). Birch: open tiers, the
    white stem shows, twigs droop."""
    P = _CROWN[kind]
    c = _rgba(h, w)
    cx = w / 2
    hw = w / 2 - 5
    top, bot = 0.035 * h, 0.985 * h                        # crown spans top..bot px (y down)
    ph = rng.uniform(0, 6.2832, 4)

    def half(y, side=1):
        t = (bot - y) / (bot - top)
        wob = 1.0 + P["lobes"] * (0.6 * math.sin(t * 9.0 + ph[0 if side > 0 else 1]) + 0.4 * math.sin(t * 21.0 + ph[2 if side > 0 else 3]))
        return min(hw * _crown_hw(kind, t) * wob * (1.0 - 0.5 * P["lobes"]), hw)
    im = Image.fromarray(np.zeros((h, w, 4), np.uint8), "RGBA")
    d = ImageDraw.Draw(im)
    if P["fill"] > 0:                                      # the crown's own shade behind the leaves
        ys = np.linspace(top + 0.06 * h, bot - 0.05 * h, 60)
        pts = [(cx - half(y, -1) * P["fill"], y) for y in ys] + [(cx + half(y, 1) * P["fill"], y) for y in ys[::-1]]
        d.polygon(pts, fill=(22, 34, 20, 255))
    lean = rng.normal(0, 0.012) * w
    d.line([(cx, h), (cx + lean, h * (0.16 if kind == "birch" else 0.5))], fill=P["stem"] + (255,),
           width=max(3, int(w * (0.024 if kind == "birch" else 0.036))))
    for k in range(8 if kind != "birch" else 12):          # limbs: steep forks (linden / maple), thin drooping twigs (birch)
        f0 = rng.uniform(0.0, 0.45 if kind != "birch" else 0.8)
        y0 = h - f0 * h
        sg = -1 if k % 2 else 1
        a = sg * (rng.uniform(0.35, 0.85) if kind != "birch" else rng.uniform(0.75, 1.3))
        L = half(y0 - 0.15 * h, sg) * rng.uniform(0.6, 0.95)
        d.line([(cx, y0), (cx + math.sin(a) * L, y0 - math.cos(a) * L)],
               fill=(tuple(int(v * 0.8) for v in P["stem"]) if kind != "birch" else (74, 62, 54)) + (255,), width=max(2, int(w * 0.014)))
    c[...] = np.asarray(im, np.float32) / np.array([1, 1, 1, 255], np.float32)
    stamps = _leaf_stamps(rng)
    S = _Stamper(c, stamps)
    leaf_px = max(P["lm"] * (w / SPRITE_M["crown_" + kind][0]) * 1.5, 5.0 * SS / 2 + 2.5)
    blobs = []
    for i in range(P["n"]):
        t = rng.uniform(0.0, 1.0)
        y = bot - t * (bot - top)
        br = rng.uniform(*P["rr"]) * w
        sg = 1 if rng.random() < 0.5 else -1
        proud = rng.random() < 0.34                         # skin clusters: the outline is theirs
        x = cx + sg * half(y, sg) * (rng.uniform(0.78, 1.0) if proud else rng.uniform(0.0, 0.86))
        x = min(max(x, br * 0.7 + 3), w - br * 0.7 - 3)
        if kind == "birch" and (math.sin(t * 13.0 + ph[0] + sg * 1.3) > 0.78 or rng.random() < 0.08):   # bays between the tiers
            continue
        depth = rng.random() if not proud else rng.uniform(0.0, 0.6)       # 0 = far side of the crown
        blobs.append((depth, x, min(max(y, br * 0.6 + 3), h - 3), br, t))
    blobs.sort()
    for depth, bx, by, br, t in blobs:
        side = (bx - cx) / hw                               # light from the upper left
        k0 = P["shade"] + (1 - P["shade"]) * (0.42 * depth + 0.38 * t + 0.20 * (0.5 - 0.5 * side))
        for j in range(P["per"]):
            a, r = rng.uniform(0, 6.2832), br * math.sqrt(rng.random())
            lx, ly = bx + math.cos(a) * r, by + math.sin(a) * r * (0.8 if kind != "birch" else 1.5)
            if not (leaf_px * 0.6 < lx < w - leaf_px * 0.6 and leaf_px * 0.6 < ly < h - 2):
                continue
            k = k0 * rng.uniform(0.8, 1.18) * (0.78 + 0.3 * (1 - (ly - by) / max(br, 1)) * 0.5 + 0.22 * j / P["per"])
            col = np.array(P["leaf"], np.float32) * k + np.array([10, 4, -8], np.float32) * rng.uniform(-1, 1)
            ang = rng.uniform(0, 6.2832) if kind != "birch" else math.pi + rng.normal(0, 0.5)     # birch leaves hang
            S.put(int(rng.integers(len(stamps))), lx, ly, leaf_px * rng.uniform(0.75, 1.25), ang, col)
    return c


def _tall(rng, h, w):
    c = _rgba(h, w)
    s = w / N
    for name in ("thuja_a", "thuja_b", "thuja_c", "spruce_a", "spruce_b", "crown_ovoid", "crown_round", "crown_birch"):
        x0, wpx = int(round(_SPR_X[name][0] * s)), int(round(_SPR_X[name][1] * s))
        sub = c[:, x0:x0 + wpx]
        if name.startswith("thuja"):
            sub[...] = _thuja_card(rng, h, wpx, "abc".index(name[-1]))
        elif name.startswith("spruce"):
            sub[...] = _spruce_card(rng, h, wpx)
        else:
            sub[...] = _crown_card(rng, h, wpx, name[6:])
    return c


def _hedge(rng, h, w):
    """Tileable side of a clipped broadleaf hedge (hornbeam / privet, refs P08 / P12): dense leaves, a ragged top
    edge, thin and twiggy at the foot."""
    c = _rgba(h, w)
    stamps = _leaf_stamps(rng)
    y = (np.arange(h) + 0.5)[:, None] / h
    top = 0.10 + 0.06 * _noise(rng, 1, w, 0.01, 30 * SS)                        # ragged top line (fraction from the top)
    body = (y > top + 0.05) & (y < 0.97)
    c[np.broadcast_to(body, (h, w)), :3] = (26, 40, 24)
    c[np.broadcast_to(body, (h, w)), 3] = 1.0
    S = _Stamper(c, stamps, wrap=True)
    # s12 (ADR 0124 r2): the row is 1.5 m of hedge in 170 px but a hedge quad stands up to ~2.1 m, so a 7.5 cm stamp
    # read as a ~18 cm leaf from 5 m (r1 / r2b `r15_front_brick_bars`). 3.6 cm in the atlas = 5-8 cm on the hedge
    # (privet / hornbeam blade, WORKING_VALUE); count scaled with the area so the cover stays the same.
    n = 36000
    lp = 0.036 * w / KIT_M
    for i in range(n):
        x = rng.uniform(0, w)
        t0 = float(top[0, int(x) % w])
        yy = rng.uniform(t0, 1.0)
        lvl = i / n
        if yy > 0.9 and rng.random() < 0.6:               # sparse foot
            continue
        k = (0.45 + 0.55 * lvl) * rng.uniform(0.84, 1.16) * (1.08 - 0.3 * yy)
        col = np.array([62, 94, 44], np.float32) * k + np.array([8, 3, -6], np.float32) * rng.uniform(-1, 1)
        S.put(int(rng.integers(len(stamps))), x, yy * h, lp * rng.uniform(0.75, 1.25), rng.uniform(0, 6.2832), col)
    return c


def _bleed(im):
    """Transparent texels take the blurred colour of their neighbours (no dark fringe in the mips)."""
    a = im[..., 3:4]
    if a.min() > 0.999:
        return im
    num = ndimage.gaussian_filter(im[..., :3] * a, (4, 4, 0), mode=("nearest", "wrap", "nearest"))
    den = ndimage.gaussian_filter(a, (4, 4, 0), mode=("nearest", "wrap", "nearest"))
    far = np.broadcast_to((im[..., :3] * a).sum((0, 1)) / max(float(a.sum()), 1.0), num.shape)
    fill = np.where(den > 1e-3, num / np.maximum(den, 1e-3), far)
    out = im.copy()
    out[..., :3] = np.where(a > 0.5, im[..., :3], fill)
    return out


@functools.lru_cache(maxsize=1)
def atlas():
    """The atlas as a PIL RGBA image (deterministic)."""
    W = N * SS
    canvas = np.zeros((N * SS, W, 4), np.float32)
    paint = {"picket": _picket, "boards_rust": lambda r, h, w: _boards(r, h, w, "boards_rust", (160, 82, 52)),
             "boards_brown": lambda r, h, w: _boards(r, h, w, "boards_brown", (80, 54, 42)),
             "boards_grey": lambda r, h, w: _boards(r, h, w, "boards_grey", (118, 110, 100), grey=True),
             "chainlink": _chainlink, "concrete": _concrete, "bars": _bars, "lamella": _lamella, "wall": _wall,
             "brick": _brick, "swatch": _swatches, "thuja": _thuja, "hedge": _hedge, "sprites": _sprites, "tall": _tall}
    k = 0
    for names, hpx in _BANDS:
        for name in names:
            rng = np.random.default_rng(12400 + k)
            k += 1
            x0, wpx = ROW_X[name][0] * SS, ROW_X[name][1] * SS
            im = paint[name](rng, hpx * SS, wpx)
            if name in ("thuja", "hedge", "sprites", "tall"):          # stamped rows: values 0..255 rgb, alpha 0..1
                im = im.copy()
            im = _bleed(im)
            y0 = ROW_Y[name][0] * SS
            canvas[y0:y0 + hpx * SS, x0:x0 + wpx] = im
            p = PAD * SS // 2                                 # replicate the row edges into half the padding
            canvas[y0 - p:y0, x0:x0 + wpx] = im[:1]
            canvas[y0 + hpx * SS:y0 + hpx * SS + p, x0:x0 + wpx] = im[-1:]
    canvas[..., 3] *= 255.0
    big = Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8), "RGBA")
    return big.resize((N, N), Image.LANCZOS)


def textures():
    return {"plot_kit": atlas()}


def coverage():
    """{row: share of texels with alpha >= 0.5} (QA)."""
    a = np.asarray(atlas())[..., 3] >= 128
    return {n: round(float(a[y0:y0 + h, ROW_X[n][0]:ROW_X[n][0] + ROW_X[n][1]].mean()), 3) for n, (y0, h) in ROW_Y.items()}


if __name__ == "__main__":
    import sys
    atlas().save(sys.argv[1] if len(sys.argv) > 1 else "plot_kit.png")
    print(coverage(), SOURCE)
