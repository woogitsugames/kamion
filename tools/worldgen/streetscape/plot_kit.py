"""Plot kit atlas (ADR 0114): ONE alpha-clip texture for everything that stands on a single-family plot - fences of
the Białystok typology (docs/refs/posesje-bialystok.md), gate infill, brick posts, steel / wood swatches, thuja and
spruce foliage, fruit-tree / shrub / perennial cards. One texture = one material (`plot_kit`) = one submesh of the
chunk's `furniture` mesh, so a chunk full of plots costs ONE draw (ADR 0107 drew every bay as an instance: one draw
per 64 m cell x prototype x submesh, +45 draws on the worst Low camera).

Drawn from primitives (numpy / PIL), no photos, no image generators; the reference frames (Mapillary CC BY-SA,
Commons) are looked at for pattern, proportion and colour only - no pixel of them is used. Colours are sRGB albedo
(material colour white), WORKING_VALUE read off the frames named per row.

Layout: 2048 x 2048, rows span the full width and TILE IN U (period KIT_M metres); v never tiles, rows are separated
by PAD px with replicated edges. v = 0 is the image bottom (generator convention, gltf.py flips to glTF).
    row(name) -> (v_bottom, v_top);  u = metres / KIT_M
    SWATCH[name] -> (u, v) of a flat colour (all vertices of a box pinned there)
    SPRITE[name] -> (u0, u1) inside the 'sprites' row
"""
from __future__ import annotations

import functools
import math

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

N = 2048
SS = 2                      # supersampling of the drawing canvas
KIT_M = 10.24               # metres across the atlas width (200 px / m)
PAD = 10
BAY_M = KIT_M / 4           # post pitch drawn into the framed rows (chain-link, bars, lamellae): 2.56 m
# (row, height px, height in metres the row stands for)
_ROWS = [("picket", 150, 1.30), ("boards_rust", 150, 1.80), ("boards_brown", 150, 1.80), ("chainlink", 150, 1.50),
         ("concrete", 150, 1.60), ("bars", 150, 1.40), ("lamella", 150, 1.70), ("wall", 56, 1.80), ("brick", 160, 2.00),
         ("swatch", 28, 0.0), ("thuja", 200, 1.20), ("spruce", 150, 0.90), ("sprites", 256, 0.0)]
ROW_Y = {}
ROW_H_M = {}
_y = PAD // 2
for _n, _h, _m in _ROWS:
    ROW_Y[_n] = (_y, _h)
    ROW_H_M[_n] = _m
    _y += _h + PAD
assert _y - PAD // 2 <= N, _y

_SW = ["steel_black", "steel_green", "steel_graphite", "wood_brown", "wood_rust", "concrete", "soil", "galv",
       "bin_dark", "lid_yellow", "lid_brown", "trunk"]
_SW_RGB = {"steel_black": (30, 30, 32), "steel_green": (28, 72, 52), "steel_graphite": (58, 60, 64),
           "wood_brown": (82, 56, 44), "wood_rust": (136, 64, 46), "concrete": (138, 135, 127), "soil": (60, 46, 36),
           "galv": (118, 122, 124), "bin_dark": (40, 44, 46), "lid_yellow": (186, 156, 44), "lid_brown": (96, 64, 44),
           "trunk": (66, 56, 48)}
# sprites of the 'sprites' row: name -> (x0 px, width px, width m, height m)
_SPR = [("apple_a", 400, 3.4, 2.6), ("apple_b", 400, 3.0, 2.6), ("shrub_a", 300, 1.7, 1.45), ("shrub_b", 300, 1.5, 1.3),
        ("flowers_a", 216, 0.9, 0.6), ("flowers_b", 216, 0.9, 0.6), ("flowers_c", 216, 0.9, 0.6)]
SPRITE = {}
SPRITE_M = {}
_x = 0
for _n, _w, _wm, _hm in _SPR:
    SPRITE[_n] = ((_x + 3) / N, (_x + _w - 3) / N)
    SPRITE_M[_n] = (_wm, _hm)
    _x += _w
THUJA_GREEN_U = 0.86         # u < this: live foliage; above: a browned (dead) stretch of the thuja row


def row(name, inset_px=1.0):
    y0, h = ROW_Y[name]
    return (1.0 - (y0 + h - inset_px) / N, 1.0 - (y0 + inset_px) / N)


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


def _grid(h, w, hm):
    """x (m), y (m, 0 = ground, up) of every canvas texel of a row standing for hm metres."""
    x = (np.arange(w) + 0.5) / w * KIT_M
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


def _picket(rng, h, w):
    hm = ROW_H_M["picket"]
    X, Y = _grid(h, w, hm)
    n = 76
    pitch = KIT_M / n
    k = np.floor(X / pitch).astype(int)
    xc = (k + 0.5) * pitch
    half = 0.335 * pitch
    top = hm - 0.03 - 0.035 * rng.random(n)[k]            # hand-nailed: tops within 3.5 cm
    tip = top - np.abs(X - xc) * 0.9                      # pointed tops (Commons C04)
    on = (np.abs(X - xc) < half) & (Y < tip) & (Y > 0.03)
    base = np.array([118, 50, 38], np.float32) * (0.82 + 0.36 * rng.random(n))[k][..., None]
    peel = rng.random(n) < 0.10                           # paint gone: grey wood
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


def _boards(rng, h, w, name, col):
    hm = ROW_H_M[name]
    X, Y = _grid(h, w, hm)
    n = 80
    pitch = KIT_M / n
    k = np.floor(X / pitch).astype(int)
    xin = X - k * pitch
    top = hm - 0.02 - 0.09 * rng.random(n)[k] ** 2        # uneven tops (Mapillary P09)
    gap = xin < (0.004 + 0.008 * (rng.random(n)[k] < 0.25))
    on = (~gap) & (Y < top)
    base = np.array(col, np.float32) * (0.80 + 0.38 * rng.random(n))[k][..., None]
    fade = rng.random(n) < 0.12
    base[fade[k]] = base[fade[k]] * 0.55 + np.array([120, 108, 96], np.float32) * 0.45
    rgb = _weather(base, rng, h, w, bottom=0.22)
    im = _rgba(h, w)
    im[on, :3] = rgb[on]
    im[on, 3] = 1.0
    for yr in (0.22 * hm, 0.80 * hm):                     # nail rows
        nail = (np.abs(xin - pitch / 2) < 0.005) & (np.abs(Y - yr) < 0.006) & on
        im[nail, :3] *= 0.5
    return im


def _chainlink(rng, h, w):
    hm = ROW_H_M["chainlink"]
    X, Y = _grid(h, w, hm)
    p = KIT_M / 170                                       # 60 mm diamond
    wire = 0.0042                                         # half width: drawn ~8 mm so one texel survives (real 3 mm)
    d1 = np.abs(((X + Y) / p + 0.5) % 1.0 - 0.5) * p * 0.7071
    d2 = np.abs(((X - Y) / p + 0.5) % 1.0 - 0.5) * p * 0.7071
    mesh = ((d1 < wire) | (d2 < wire)) & (Y > 0.05) & (Y < hm - 0.03)
    im = _rgba(h, w)
    tone = 0.85 + 0.3 * _noise(rng, h, w, 20, 20)
    im[mesh, :3] = np.array([40, 88, 64], np.float32) * tone[mesh][:, None]
    im[mesh, 3] = 1.0
    xb = np.abs((X / BAY_M + 0.5) % 1.0 - 0.5) * BAY_M
    frame = (xb < 0.025) | (np.abs(Y - (hm - 0.025)) < 0.022) | (np.abs(Y - 0.06) < 0.012)
    im[frame, :3] = np.array([28, 72, 52], np.float32) * tone[frame][:, None]
    im[frame, 3] = 1.0
    rust = (_noise(rng, h, w, 3, 3) > 0.78) & frame & (Y < 0.3)
    im[rust, :3] = (92, 58, 40)
    return im


def _concrete(rng, h, w):
    hm = ROW_H_M["concrete"]
    X, Y = _grid(h, w, hm)
    bay = KIT_M / 5
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
    post = (np.abs(xb - 0.5) > 0.47)
    rgb[post] = (rgb[post] * 0.9 + 6)
    edge = (np.abs(np.abs(xb - 0.5) - 0.47) < 0.004)
    rgb[edge] *= 0.6
    run = np.clip(_noise(rng, h, w, 50, 1.5) - 0.62, 0, 1) * 2.2 * np.clip((Y - 0.3) / 1.2, 0, 1)    # run-off from the cap
    rgb *= (1 - 0.35 * run)[..., None]
    im = _rgba(h, w, a=1.0)
    im[..., :3] = rgb
    return im


def _bars(rng, h, w):
    hm = ROW_H_M["bars"]
    X, Y = _grid(h, w, hm)
    n = 80
    pitch = KIT_M / n
    xc = (np.floor(X / pitch) + 0.5) * pitch
    dx = np.abs(X - xc)
    bar = (dx < 0.011) & (Y > 0.08) & (Y < hm - 0.07)
    tip = (dx < np.clip(0.028 - np.abs(Y - (hm - 0.06)) * 0.5, 0, 0.028)) & (Y > hm - 0.12)      # spear heads
    flat = (np.abs(Y - 0.16) < 0.02) | (np.abs(Y - (hm - 0.20)) < 0.02)
    xb = np.abs((X / BAY_M + 0.5) % 1.0 - 0.5) * BAY_M
    post = (xb < 0.03) & (Y < hm - 0.03)
    on = bar | tip | flat | post
    im = _rgba(h, w)
    tone = 0.8 + 0.5 * _noise(rng, h, w, 12, 12)
    im[on, :3] = np.array([30, 30, 32], np.float32) * tone[on][:, None]
    im[on, 3] = 1.0
    rust = (_noise(rng, h, w, 2.5, 2.5) > 0.80) & on & ((np.abs(Y - 0.16) < 0.05) | (Y < 0.14))
    im[rust, :3] = (78, 48, 34)
    return im


def _lamella(rng, h, w):
    hm = ROW_H_M["lamella"]
    X, Y = _grid(h, w, hm)
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
    run = np.clip(_noise(rng, h, w, 30, 1.2) - 0.6, 0, 1) * 2.0
    rgb *= (1 - 0.3 * run)[..., None]
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
    col = np.array([150, 72, 52], np.float32) * (0.8 + 0.4 * tone[c, b])[..., None]
    burnt = tone[c, b] > 0.9
    col[burnt] = np.array([98, 54, 46], np.float32)
    col = col * (0.92 + 0.16 * _noise(rng, h, w, 1.5, 1.5))[..., None]
    mortar = (yin < 0.011) | (xin < 0.011)
    col[mortar] = np.array([146, 140, 130], np.float32) * (0.9 + 0.2 * rng.random())
    y = np.clip((0.3 - Y) / 0.3, 0, 1)[..., None]
    col = col * (1 - 0.22 * y)                                                   # damp foot
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


def _wrap_ellipse(d, w, x, y, rx, ry, fill):
    for dx in (-w, 0, w):
        d.ellipse([x + dx - rx, y - ry, x + dx + rx, y + ry], fill=fill)


def _wrap_poly(d, w, pts, fill):
    for dx in (-w, 0, w):
        d.polygon([(px + dx, py) for px, py in pts], fill=fill)


def _thuja(rng, h, w):
    """Scale-leaf sprays of a thuja: flat fronds hanging up and out - a stem with short side shoots - drawn back to
    front, dark inside, yellow-green at the tips; ~7 % holes onto the dark interior of the shell."""
    im = _pil(h, w)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, h], fill=(22, 36, 22, 255))
    live = [(30, 46, 26), (42, 64, 34), (54, 80, 40), (72, 98, 46)]
    dead = [(64, 48, 32), (98, 74, 44), (124, 94, 54), (142, 112, 68)]
    n = 3600
    ppm_x, ppm_y = w / KIT_M, h / ROW_H_M["thuja"]
    for i in range(n):
        x, y = rng.uniform(0, w), rng.uniform(-0.05 * h, 1.05 * h)
        pal = dead if x / w > THUJA_GREEN_U + 0.01 else live
        lvl = min(3, int(i / n * 4))
        L = rng.uniform(0.07, 0.13)                       # frond length, m
        a = rng.normal(0, 0.30)                           # off vertical
        col = _jit(pal[lvl], rng, 0.14)
        tip = (x + math.sin(a) * L * ppm_x, y - math.cos(a) * L * ppm_y)
        wd = max(2, int(0.006 * ppm_x))
        for dx in (-w, 0, w):
            d.line([(x + dx, y), (tip[0] + dx, tip[1])], fill=col, width=wd + 1)
        for k in range(1, 6):                             # side shoots, shorter towards the tip
            f = k / 6
            bx, by = x + (tip[0] - x) * f, y + (tip[1] - y) * f
            sl = L * (0.42 - 0.25 * f)
            for sg in (-1, 1):
                aa = a + sg * 0.9
                ex, ey = bx + math.sin(aa) * sl * ppm_x, by - math.cos(aa) * sl * ppm_y
                for dx in (-w, 0, w):
                    d.line([(bx + dx, by), (ex + dx, ey)], fill=col, width=wd)
    a = np.asarray(im, np.float32).copy()
    hole = _noise(rng, h, w, 1.6 * SS, 1.6 * SS) > 0.74
    a[hole & (a[..., :3].sum(-1) < 110), 3] = 0.0         # holes only where the dark interior shows
    a[..., 3] /= 255.0
    return a


def _spruce(rng, h, w):
    """One tier of drooping branches of a blue spruce: twigs with short needles hanging down and out, dense at the top
    (the trunk side), ragged tips below."""
    im = _pil(h, w)
    d = ImageDraw.Draw(im)
    pal = [(18, 28, 27), (30, 46, 45), (44, 64, 62), (62, 84, 80)]
    d.rectangle([0, 0, w, int(h * 0.34)], fill=pal[0] + (255,))
    n = 3000
    ppm_x, ppm_y = w / KIT_M, h / ROW_H_M["spruce"]
    for i in range(n):
        lvl = min(3, int(i / n * 4))
        x = rng.uniform(0, w)
        y = rng.uniform(0, 0.62 * h)
        L = rng.uniform(0.16, 0.32) * (1.25 if rng.random() < 0.2 else 1.0)       # twig length, m
        a = math.pi + rng.normal(0, 0.28)                                       # hanging
        col = _jit(pal[lvl], rng, 0.12)
        tip = (x + math.sin(a) * L * ppm_x, min(y - math.cos(a) * L * ppm_y, h - 2))
        wd = max(2, int(0.008 * ppm_x))
        for dx in (-w, 0, w):
            d.line([(x + dx, y), (tip[0] + dx, tip[1])], fill=col, width=wd + 1)
        for k in range(1, 9):                                                   # needles all along the twig
            f = k / 9
            bx, by = x + (tip[0] - x) * f, y + (tip[1] - y) * f
            for sg in (-1, 1):
                aa = a + sg * 1.05
                ex, ey = bx + math.sin(aa) * 0.022 * ppm_x, by - math.cos(aa) * 0.022 * ppm_y
                for dx in (-w, 0, w):
                    d.line([(bx + dx, by), (ex + dx, min(ey, h - 1))], fill=col, width=wd)
    a = np.asarray(im, np.float32).copy()
    a[..., 3] /= 255.0
    return a


def _crown(d, rng, x0, wpx, h, leaf, n_blobs, fruit=None, trunk=True, dome=False):
    """Leaf clusters around a branch frame inside [x0, x0 + wpx] x [0, h]."""
    cx = x0 + wpx / 2
    if trunk:
        for k in range(7):                                # branch frame
            a = -math.pi / 2 + (k - 3) * 0.33 + rng.normal(0, 0.06)
            L = h * rng.uniform(0.45, 0.72)
            d.line([(cx, h), (cx + math.cos(a) * L * 0.8, h + math.sin(a) * L)], fill=(60, 48, 40, 255), width=max(2, int(h * 0.018)))
    blobs = []
    for i in range(n_blobs):
        a, r = rng.uniform(0, 2 * math.pi), math.sqrt(rng.random())
        bx = cx + math.cos(a) * r * wpx * 0.40
        by = (h * 0.50 + math.sin(a) * r * h * 0.40) if not dome else h * (1.0 - 0.9 * rng.random() ** 0.8 * (1 - (abs(bx - cx) / (wpx * 0.46)) ** 2))
        blobs.append((by, bx))
    order = sorted(range(n_blobs), key=lambda i: -blobs[i][0])        # lower clusters first (darker), top last
    for rank, i in enumerate(order):
        by, bx = blobs[i]
        lvl = rank / max(n_blobs - 1, 1)
        base = tuple(int(c * (0.55 + 0.6 * lvl)) for c in leaf)
        for _ in range(26):
            lx, ly = bx + rng.normal(0, wpx * 0.045), by + rng.normal(0, h * 0.05)
            rr = rng.uniform(0.012, 0.022) * wpx
            if x0 + rr + 2 < lx < x0 + wpx - rr - 2 and rr + 2 < ly < h - 2:
                d.ellipse([lx - rr, ly - rr * 0.7, lx + rr, ly + rr * 0.7], fill=_jit(base, rng, 0.2))
        if fruit is not None and rng.random() < fruit[1]:
            fx, fy = bx + rng.normal(0, wpx * 0.03), by + rng.normal(0, h * 0.03)
            rr = fruit[2] * wpx
            if x0 + 4 < fx < x0 + wpx - 4 and 4 < fy < h - 4:
                d.ellipse([fx - rr, fy - rr, fx + rr, fy + rr], fill=_jit(fruit[0], rng, 0.15))


def _sprites(rng, h, w):
    im = _pil(h, w)
    d = ImageDraw.Draw(im)
    s = w / N
    x = 0
    spec = {"apple_a": dict(leaf=(74, 104, 48), n=120, fruit=((176, 60, 44), 0.25, 0.010)),
            "apple_b": dict(leaf=(84, 110, 52), n=105, fruit=((196, 170, 70), 0.18, 0.010)),
            "shrub_a": dict(leaf=(62, 96, 44), n=80, dome=True, trunk=False),
            "shrub_b": dict(leaf=(70, 92, 50), n=70, dome=True, trunk=False, fruit=((214, 196, 206), 0.9, 0.035)),
            "flowers_a": dict(leaf=(60, 100, 40), n=34, dome=True, trunk=False, fruit=((222, 128, 30), 1.0, 0.045)),
            "flowers_b": dict(leaf=(66, 104, 46), n=34, dome=True, trunk=False, fruit=((226, 196, 52), 1.0, 0.040)),
            "flowers_c": dict(leaf=(58, 92, 44), n=34, dome=True, trunk=False, fruit=((204, 110, 150), 0.9, 0.040))}
    for name, wpx, _, _ in _SPR:
        sp = spec[name]
        _crown(d, rng, x * s, wpx * s, h, sp["leaf"], sp["n"], sp.get("fruit"), sp.get("trunk", True), sp.get("dome", False))
        x += wpx
    a = np.asarray(im, np.float32).copy()
    a[..., 3] /= 255.0
    return a


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
             "boards_brown": lambda r, h, w: _boards(r, h, w, "boards_brown", (80, 54, 42)), "chainlink": _chainlink,
             "concrete": _concrete, "bars": _bars, "lamella": _lamella, "wall": _wall, "brick": _brick,
             "swatch": _swatches, "thuja": _thuja, "spruce": _spruce, "sprites": _sprites}
    for k, (name, hpx, _) in enumerate(_ROWS):
        rng = np.random.default_rng(11400 + k)
        im = _bleed(paint[name](rng, hpx * SS, W))
        y0 = ROW_Y[name][0] * SS
        canvas[y0:y0 + hpx * SS] = im
        p = PAD * SS // 2                                 # replicate the row edges into half the padding
        canvas[y0 - p:y0] = im[:1]
        canvas[y0 + hpx * SS:y0 + hpx * SS + p] = im[-1:]
    canvas[..., 3] *= 255.0
    big = Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8), "RGBA")
    return big.resize((N, N), Image.LANCZOS)


def textures():
    return {"plot_kit": atlas()}


def coverage():
    """{row: share of texels with alpha >= 0.5} (QA)."""
    a = np.asarray(atlas())[..., 3] >= 128
    return {n: round(float(a[y0:y0 + h].mean()), 3) for n, (y0, h) in ROW_Y.items()}


if __name__ == "__main__":
    import sys
    atlas().save(sys.argv[1] if len(sys.argv) > 1 else "plot_kit.png")
    print(coverage())
