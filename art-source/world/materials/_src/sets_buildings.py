"""Building atlases of the Białystok typology work (ADR 0081): windows with what is behind the glass, doors, garage
doors, balcony balustrades, small facade equipment, LOD1 window rows and the prefabricated concrete fence.

`facade_atlas`    calibrated strip atlas 16 x 16 m (layout: tools/worldgen/streetscape/facade_atlas.py). Everything is
                  drawn by code from what the open references show (CC0 Commons photos of the blocks at Rondo Putry,
                  Mapillary frames of the Andersa plants; no pixels of them are used): PVC windows with net curtains,
                  drapes, roller and day-night blinds, cafe curtains, plants, dark and lit rooms; balcony doors;
                  entrances with an intercom panel; steel doors; garage doors (double-leaf sheet steel, up-and-over) with
                  rust, primer patches and content-free spray scribbles; balustrades (perforated sheet, trapezoid sheet,
                  frosted glass, bars with flower boxes, reed mat, old fibre-cement panels); balcony glazing-in; AC
                  units, louvres, meter cabinets.
`facade_far`      modulation set (wall = neutral 0.5): storey rows of 8 window bays composed from the same cells.
`fence_concrete`  calibrated strip atlas 16 x 4.5 m: bays of stacked plates and of framed panels, post strip; micro
                  relief / albedo ratio / roughness from the CC0 scan concrete_floor_worn_001 (Poly Haven) when fetched.

    uv run --project tools/worldgen python art-source/world/materials/_src/build_all.py --only facade_atlas,facade_far,fence_concrete
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[3] / "tools" / "worldgen"))
import pbrkit as K  # noqa: E402
from streetscape import facade_atlas as A  # noqa: E402

F32 = np.float32
GLASS_T = np.array([0.56, 0.60, 0.59], F32)      # what a room behind double glazing keeps of its albedo (WORKING_VALUE)
WHITE_PVC = (0.66, 0.66, 0.63)
BROWN_PVC = (0.12, 0.065, 0.04)
ANTHRACITE = (0.045, 0.048, 0.052)
ALU_GREY = (0.33, 0.34, 0.34)


def lin(*rgb255):
    a = np.array(rgb255, F32) / 255.0
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4).astype(F32)


class P:
    """Painter of one cell: coordinates in metres, x right, y up."""

    def __init__(self, w, h, px, seed):
        self.w, self.h, self.px = w, h, px
        self.nx, self.ny = int(round(w / px)), int(round(h / px))
        x = (np.arange(self.nx, dtype=F32) + 0.5) * px
        y = h - (np.arange(self.ny, dtype=F32) + 0.5) * px
        self.X, self.Y = np.meshgrid(x, y)
        self.alb = np.full((self.ny, self.nx, 3), 0.3, F32)
        self.hgt = np.zeros((self.ny, self.nx), F32)
        self.rgh = np.full((self.ny, self.nx), 0.8, F32)
        self.rng = np.random.default_rng(seed)
        self.seed = seed

    def rect(self, x0, x1, y0, y1, soft=None):
        s = soft or self.px
        d = np.minimum(np.minimum(self.X - x0, x1 - self.X), np.minimum(self.Y - y0, y1 - self.Y))
        return np.clip(d / s + 0.5, 0, 1)

    def ring(self, x0, x1, y0, y1, t):
        return self.rect(x0, x1, y0, y1) * (1 - self.rect(x0 + t, x1 - t, y0 + t, y1 - t))

    def disc(self, cx, cy, r, soft=None):
        s = soft or self.px
        return np.clip((r - np.hypot(self.X - cx, self.Y - cy)) / s + 0.5, 0, 1)

    def put(self, m, col=None, h=None, r=None):
        if col is not None:
            self.alb += (np.asarray(col, F32) - self.alb) * m[..., None]
        if h is not None:
            self.hgt += (h - self.hgt) * m
        if r is not None:
            self.rgh += (r - self.rgh) * m

    def mul(self, m, k):
        self.alb *= 1 - m[..., None] * (1 - np.asarray(k, F32))

    def noise(self, wl, k=0, aniso=(1.0, 1.0)):
        r = np.random.default_rng(self.seed * 131 + k).standard_normal((self.ny, self.nx)).astype(F32)
        s = max(0.5, wl / self.px / 2.5)
        r = ndimage.gaussian_filter(r, (s * aniso[1], s * aniso[0]), mode="reflect")
        return (r - r.mean()) / (r.std() + 1e-6)


def _folds(p, u, n, k, depth=1.0):
    """Curtain folds along u (0..1 across the cloth): 0..1, irregular pitch."""
    ph = p.rng.random(3) * 6.28
    w = u * n + 0.35 * np.sin(u * n * 0.37 * 6.28 + ph[0]) + 0.2 * np.sin(u * n * 0.11 * 6.28 + ph[1])
    f = 0.5 + 0.5 * np.sin(6.2832 * w + ph[2])
    return 1 - depth * (1 - f ** 0.7)


def _plants(p, R, n, k=0):
    x0, x1, y0, y1 = R
    rng = np.random.default_rng(p.seed * 7 + k)
    for i in range(n):
        cx = x0 + (x1 - x0) * (0.15 + 0.7 * rng.random())
        pw, ph = 0.07 + 0.03 * rng.random(), 0.09 + 0.04 * rng.random()
        pot = [lin(150, 82, 55), lin(215, 212, 205), lin(60, 60, 62), lin(120, 95, 70)][rng.integers(4)]
        lh = 0.16 + 0.22 * rng.random()
        leaf = p.disc(cx, y0 + ph + lh * 0.55, lh * 0.55, soft=0.02) * (p.noise(0.03, 40 + i) > -0.5 - 0.6 * rng.random())
        g = np.array([0.045, 0.085, 0.03], F32) * (0.7 + 0.8 * rng.random())
        p.put(leaf * (p.Y > y0 + ph * 0.6), g * (1 + 0.25 * p.noise(0.02, 60 + i))[..., None])
        if rng.random() < 0.35:        # orchid / geranium flowers
            fl = p.disc(cx + 0.03, y0 + ph + lh * 0.9, 0.035, soft=0.01) * (p.noise(0.012, 80 + i) > 0.2)
            p.put(fl, [lin(225, 225, 230), lin(190, 40, 90), lin(200, 45, 40)][rng.integers(3)])
        p.put(p.rect(cx - pw / 2, cx + pw / 2, y0, y0 + ph), pot)


def interior(p, R, kind, col=None, frac=1.0, plants=0, k=0):
    """What is seen through the glass in rectangle R = (x0, x1, y0, y1)."""
    x0, x1, y0, y1 = R
    m = p.rect(x0, x1, y0, y1)
    u = np.clip((p.X - x0) / (x1 - x0), 0, 1)
    v = np.clip((p.Y - y0) / (y1 - y0), 0, 1)
    room = np.array([0.030, 0.029, 0.028], F32) * (1 + 0.5 * v + 0.25 * p.noise(0.5, 3 + k))[..., None]
    if kind == "lit":
        glow = np.exp(-(((u - 0.55) / 0.5) ** 2 + ((v - 0.85) / 0.45) ** 2))
        room = np.array([0.42, 0.30, 0.17], F32) * (0.35 + 0.9 * glow)[..., None]
        room = np.where(((v < 0.38) & (np.abs(u - 0.3) < 0.22))[..., None], room * 0.25, room)      # furniture silhouette
    p.put(m, room, r=0.07)
    net = np.array([0.60, 0.60, 0.57], F32)

    def sheer(mask, dens=0.80, n=None, lace=True):
        f = _folds(p, u, n or max(5, int((x1 - x0) / 0.085)), 1, 0.55)
        cov = mask * (dens * (0.80 + 0.2 * f))
        c = net * (0.72 + 0.28 * f)[..., None]
        if lace:
            hem = np.clip(1 - np.abs(v - 0.07) / 0.05, 0, 1) * (0.5 + 0.5 * np.sin(u * (x1 - x0) / 0.06 * 6.28))
            c = c * (1 - 0.25 * hem)[..., None]
        p.put(cov * m, c)

    if kind in ("net", "lit"):
        sheer(np.ones_like(u), 0.82 if kind == "net" else 0.55)
    elif kind == "net_gap":
        gap = 0.03 + 0.22 * (1 - v) ** 1.8
        sheer((np.abs(u - 0.5) > gap).astype(F32) * np.clip((np.abs(u - 0.5) - gap) / 0.01, 0, 1))
    elif kind == "cafe":                 # zazdrostka: lower part only, on a rod
        top = 0.50 + 0.06 * frac
        sheer((v < top).astype(F32), 0.9, lace=False)
        p.put(p.rect(x0, x1, y0 + top * (y1 - y0) - 0.006, y0 + top * (y1 - y0) + 0.006) * m, [0.5, 0.45, 0.35])
    elif kind == "drapes":
        col = np.asarray(col if col is not None else lin(196, 176, 140), F32)
        a = 0.20 + 0.10 * frac + 0.03 * np.sin(v * 5 + 1.0)
        b = 0.17 + 0.08 * frac + 0.03 * np.sin(v * 4 + 2.0)
        sheer(((u > a) & (u < 1 - b)).astype(F32), 0.8)
        f = _folds(p, u, max(8, int((x1 - x0) / 0.05)), 2, 0.75)
        dm = np.clip((a - u) / 0.01, 0, 1) + np.clip((u - (1 - b)) / 0.01, 0, 1)
        p.put(np.clip(dm, 0, 1) * m, col * (0.45 + 0.55 * f)[..., None])
    elif kind in ("roller", "daynight", "venetian", "vertical"):
        col = np.asarray(col if col is not None else lin(225, 222, 212), F32)
        vb = 1 - frac
        bm = np.clip((v - vb) / 0.004, 0, 1)
        if kind == "roller":
            c = col * (0.92 + 0.08 * v + 0.03 * p.noise(0.3, 9 + k))[..., None]
            p.put(bm * m, c)
            p.put(p.rect(x0, x1, y0 + vb * (y1 - y0), y0 + vb * (y1 - y0) + 0.022) * m, col * 0.6)
        elif kind == "daynight":
            st = 0.5 + 0.5 * np.sin(6.2832 * p.Y / 0.15)
            op = np.clip((st - 0.5) / 0.08 + 0.5, 0, 1)
            p.put(bm * m * (0.45 + 0.55 * op), col * (0.9 + 0.1 * op)[..., None])
        elif kind == "venetian":
            st = np.abs(((p.Y / 0.05) % 1.0) - 0.5) * 2
            p.put(bm * m, col * (0.55 + 0.45 * st)[..., None])
        else:                               # vertical lamellae (offices)
            st = np.abs((((p.X - x0) / 0.09) % 1.0) - 0.5) * 2
            p.put(bm * m, col * (0.6 + 0.4 * st ** 0.6)[..., None])
    elif kind == "frosted":
        p.put(m, np.array([0.34, 0.36, 0.36], F32) * (1 + 0.05 * p.noise(0.01, 5))[..., None], r=0.45)
    elif kind == "office":                 # ceiling light panels in a dim room
        for i in range(3):
            p.put(p.rect(x0 + (0.12 + 0.3 * i) * (x1 - x0), x0 + (0.30 + 0.3 * i) * (x1 - x0), y0 + 0.86 * (y1 - y0),
                         y0 + 0.92 * (y1 - y0)) * m, [0.55, 0.56, 0.52])
        p.put(p.rect(x0, x1, y0, y0 + 0.3 * (y1 - y0)) * m, [0.07, 0.07, 0.07])
    if plants:
        _plants(p, (x0 + 0.03, x1 - 0.03, y0 + 0.005, y1), plants, k)


def window(p, R, sashes=2, frame=WHITE_PVC, fw=0.062, sw=0.052, handle=True, transom=None, muntins=None, dirt=0.25,
           bottom=None):
    """Frame, sashes and glass state over an interior already painted in R. sashes: number or list of relative widths.
    transom: relative height of a horizontal bar; muntins: (nx, ny) glazing bars per sash; bottom: height of a solid
    lower panel (doors)."""
    x0, x1, y0, y1 = R
    frame = np.asarray(frame, F32)
    m = p.rect(x0, x1, y0, y1)
    # glass: tint, dust towards the bottom edge, depth
    p.alb *= 1 - m[..., None] * (1 - GLASS_T)
    v = np.clip((p.Y - y0) / (y1 - y0), 0, 1)
    dust = dirt * (0.25 + 0.75 * np.clip(1 - v / 0.25, 0, 1) ** 2) * (0.7 + 0.3 * p.noise(0.08, 11))
    p.put(m * np.clip(dust, 0, 0.6) * 0.35, [0.20, 0.19, 0.17])
    p.rgh += m * (0.10 * np.clip(dust, 0, 1))
    p.hgt = np.where(m > 0.5, -0.040, p.hgt)
    wts = np.asarray(sashes if isinstance(sashes, (list, tuple)) else [1.0] * sashes, float)
    xs = x0 + fw + (x1 - x0 - 2 * fw) * np.concatenate([[0], np.cumsum(wts) / wts.sum()])
    fm = p.ring(x0, x1, y0, y1, fw)
    sm = np.zeros_like(fm)
    gk = np.zeros_like(fm)
    for a, b in zip(xs, xs[1:]):
        sm = np.maximum(sm, p.ring(a, b, y0 + fw, y1 - fw, sw))
        gk = np.maximum(gk, p.ring(a - 0.004, b + 0.004, y0 + fw - 0.004, y1 - fw + 0.004, 0.008))
        gk = np.maximum(gk, p.ring(a + sw - 0.006, b - sw + 0.006, y0 + fw + sw - 0.006, y1 - fw - sw + 0.006, 0.007))
        if muntins:
            for i in range(1, muntins[0]):
                xm = a + (b - a) * i / muntins[0]
                sm = np.maximum(sm, p.rect(xm - 0.012, xm + 0.012, y0 + fw, y1 - fw))
            for j in range(1, muntins[1]):
                ym = y0 + fw + (y1 - y0 - 2 * fw) * j / muntins[1]
                sm = np.maximum(sm, p.rect(a, b, ym - 0.012, ym + 0.012))
        if transom:
            yt = y0 + (y1 - y0) * transom
            sm = np.maximum(sm, p.rect(a, b, yt - 0.035, yt + 0.035))
        if bottom:
            sm = np.maximum(sm, p.rect(a, b, y0 + fw, y0 + bottom))
    tone = 1 + 0.03 * p.noise(0.2, 12)
    grime = 1 - 0.18 * np.clip(1 - v / 0.12, 0, 1)                 # the bottom rail collects dirt
    p.put(sm, frame * (tone * grime)[..., None], h=-0.012, r=0.42)
    p.put(fm, frame * (tone * grime)[..., None] * 1.0, h=0.0, r=0.42)
    p.put(gk * np.maximum(fm, sm), frame * 0.25 + 0.01)
    if handle:
        for a, b in zip(xs[1:-1], xs[2:]):        # handle on the meeting stile of every sash but the first
            hx = a + sw * 0.5
            p.put(p.rect(hx - 0.011, hx + 0.011, (y0 + y1) / 2 - 0.07, (y0 + y1) / 2 + 0.06), frame * 0.8 + 0.05, h=0.012)
        if len(xs) == 2:
            hx = xs[1] - sw * 0.5
            p.put(p.rect(hx - 0.011, hx + 0.011, (y0 + y1) / 2 - 0.07, (y0 + y1) / 2 + 0.06), frame * 0.8 + 0.05, h=0.012)


DRAPE = [lin(196, 176, 140), lin(110, 40, 38), lin(92, 98, 80), lin(150, 150, 152), lin(70, 62, 90), lin(170, 120, 70)]
BLIND = [lin(228, 226, 218), lin(210, 200, 176), lin(150, 152, 155), lin(196, 170, 150), lin(120, 135, 150)]


def _resid(p, i, kind):
    """Residential window variants: interior + frame."""
    R = (0, p.w, 0, p.h)
    G = (0.11, p.w - 0.11, 0.11, p.h - 0.11)
    if kind == "w2":
        v = [("net", {}), ("drapes", dict(col=DRAPE[0], frac=0.4)), ("roller", dict(col=BLIND[0], frac=0.6)),
             ("dark", dict(plants=3)), ("net_gap", dict(plants=2)), ("daynight", dict(col=BLIND[2], frac=0.85)),
             ("drapes", dict(col=DRAPE[1], frac=0.9)), ("venetian", dict(col=BLIND[0], frac=1.0)),
             ("cafe", dict(plants=1)), ("lit", {})][i]
        interior(p, G, v[0], k=i, **v[1])
        window(p, R, 2, frame=WHITE_PVC if i != 6 else BROWN_PVC)
    elif kind == "w1":
        v = [("net", {}), ("roller", dict(col=BLIND[1], frac=1.0)), ("dark", dict(plants=1)), ("cafe", {}),
             ("frosted", {}), ("daynight", dict(col=BLIND[0], frac=0.7))][i]
        interior(p, G, v[0], k=i, **v[1])
        window(p, R, 1)
    elif kind == "w3":
        v = [("drapes", dict(col=DRAPE[3], frac=0.6)), ("net_gap", dict(plants=3)),
             ("roller", dict(col=BLIND[3], frac=0.45))][i]
        interior(p, G, v[0], k=i, **v[1])
        window(p, R, [1, 1.25, 1])
    elif kind in ("bdoor", "bwin"):
        v = [("net", {}), ("drapes", dict(col=DRAPE[2], frac=0.5)), ("dark", {}), ("roller", dict(col=BLIND[0], frac=0.75)),
             ("daynight", dict(col=BLIND[1], frac=0.9))][i]
        interior(p, G, v[0], k=i + (7 if kind == "bwin" else 0), **v[1])
        if kind == "bdoor":
            window(p, R, 1, fw=0.065, sw=0.075, bottom=0.16)
        else:
            window(p, R, 1)
    elif kind == "stair":
        interior(p, G, ["dark", "dark", "lit"][i], k=i)
        window(p, R, 2, frame=[WHITE_PVC, ALU_GREY, WHITE_PVC][i], transom=0.5, handle=False, dirt=0.5)
    elif kind == "base":
        interior(p, (0.05, p.w - 0.05, 0.05, p.h - 0.05), ["dark", "frosted", "dark"][i], k=i)
        window(p, R, 1, frame=[(0.3, 0.3, 0.29), WHITE_PVC, (0.12, 0.12, 0.12)][i], fw=0.04, sw=0.03, handle=False, dirt=0.8)
        if i != 1:                                                                    # bars
            for xb in np.arange(0.12, p.w - 0.08, 0.11):
                p.put(p.rect(xb - 0.007, xb + 0.007, 0.03, p.h - 0.03), [0.035, 0.03, 0.028], h=0.01, r=0.6)
    elif kind == "house":
        v = [("net", {}), ("drapes", dict(col=DRAPE[5], frac=0.5)), ("roller", dict(col=lin(205, 205, 200), frac=1.0)),
             ("cafe", dict(plants=2))][i]
        interior(p, G, v[0], k=i, **v[1])
        if i == 2:                       # external roller shutter, closed: slats 40 mm in guide rails
            st = np.abs(((p.Y / 0.04) % 1.0) - 0.5) * 2
            m = p.rect(0.07, p.w - 0.07, 0.07, p.h - 0.07)
            p.put(m, lin(205, 205, 200) * (0.8 + 0.2 * st)[..., None], h=-0.01, r=0.5)
            p.put(p.ring(0, p.w, 0, p.h, 0.07), WHITE_PVC, h=0.0, r=0.45)
            p.put(p.rect(0, p.w, p.h - 0.16, p.h), WHITE_PVC, h=0.02)
        else:
            window(p, R, 2, frame=[WHITE_PVC, BROWN_PVC, WHITE_PVC, lin(52, 84, 62)][i], muntins=(1, 2) if i in (0, 3) else None)


def _office(p, i, kind):
    R = (0, p.w, 0, p.h)
    G = (0.09, p.w - 0.09, 0.09, p.h - 0.09)
    if kind == "off":
        v = [("vertical", dict(col=BLIND[1], frac=1.0)), ("office", {}), ("roller", dict(col=BLIND[2], frac=0.5)),
             ("dark", {}), ("vertical", dict(col=BLIND[0], frac=0.7))][i]
        interior(p, G, v[0], k=i, **v[1])
        window(p, R, [1.3, 1], frame=[ALU_GREY, ANTHRACITE, WHITE_PVC, ANTHRACITE, ALU_GREY][i], fw=0.05, sw=0.045)
    elif kind == "hallw":
        interior(p, G, ["office", "dark", "frosted"][i], k=i)
        window(p, R, 2, frame=ANTHRACITE, fw=0.05, sw=0.04, handle=False, dirt=0.5)
    elif kind == "indw":                 # steel sashes, small panes, a few painted over or replaced
        interior(p, (0.04, p.w - 0.04, 0.04, p.h - 0.04), "dark", k=i)
        rng = np.random.default_rng(900 + i)
        nxp, nyp = 8, 4
        for a in range(nxp):
            for b in range(nyp):
                r_ = rng.random()
                m = p.rect(p.w * a / nxp, p.w * (a + 1) / nxp, p.h * b / nyp, p.h * (b + 1) / nyp)
                if r_ < 0.12:
                    p.put(m, [0.36, 0.38, 0.38], r=0.5)                 # frosted replacement pane
                elif r_ < 0.2:
                    p.put(m, [0.20, 0.23, 0.22], r=0.6)                 # painted over
        window(p, R, 1, frame=[lin(70, 84, 76), lin(96, 70, 58)][i], fw=0.045, sw=0.03, muntins=(nxp, nyp), handle=False,
               dirt=0.9)
        p.mul(p.rect(0, p.w, 0, p.h), 1 - 0.12 * np.clip(p.noise(0.4, 21), 0, 2).mean())


def _door(p, i, kind):
    R = (0, p.w, 0, p.h)
    if kind == "door_block":
        fr = [lin(120, 46, 42), ALU_GREY, BROWN_PVC][i]
        interior(p, (0.06, p.w - 0.06, 0.06, p.h - 0.06), "dark", k=i)
        # side light 0.45 m with the intercom, door leaf 1.0 m, transom above 2.0 m
        window(p, (0, p.w, 2.0, p.h), 1, frame=fr, fw=0.05, sw=0.03, handle=False)
        window(p, (0, 0.5, 0, 2.02), 1, frame=fr, fw=0.05, sw=0.03, handle=False, bottom=0.9)
        window(p, (0.48, p.w, 0, 2.02), 1, frame=fr, fw=0.05, sw=0.07, handle=False, bottom=0.42, transom=0.52)
        p.put(p.rect(0.60, 0.63, 0.85, 1.35), [0.45, 0.45, 0.44], h=0.03, r=0.3)          # pull handle
        p.put(p.rect(0.56, p.w - 0.07, 0.07, 0.30), np.asarray(fr) * 0.8, h=-0.005)       # kick panel
        ip = p.rect(0.15, 0.36, 1.12, 1.50)
        p.put(ip, [0.36, 0.37, 0.37], h=0.01, r=0.35)                                      # intercom: steel panel,
        for r_ in range(4):                                                                 # buttons, speaker grille
            for c_ in range(3):
                p.put(p.disc(0.195 + 0.06 * c_, 1.16 + 0.045 * r_, 0.012), [0.10, 0.10, 0.10])
        p.put(p.rect(0.18, 0.33, 1.38, 1.46) * (np.sin(p.Y / 0.008 * 6.28) > 0), [0.05, 0.05, 0.05])
    elif kind == "door_steel":
        c = [lin(120, 124, 126), lin(64, 86, 74), lin(96, 100, 104)][i]
        p.put(p.rect(0, p.w, 0, p.h), np.asarray(c) * 0.75, h=0.0, r=0.5)
        leaf = p.rect(0.06, p.w - 0.06, 0.015, p.h - 0.06)
        p.put(leaf, np.asarray(c, F32) * (1 + 0.04 * p.noise(0.25, 2))[..., None], h=-0.02, r=0.45)
        p.put(p.ring(0.06, p.w - 0.06, 0.015, p.h - 0.06, 0.006), np.asarray(c) * 0.3)
        p.put(p.rect(p.w - 0.20, p.w - 0.10, 0.98, 1.06), [0.30, 0.30, 0.30], h=0.01, r=0.3)      # lever + rose
        p.put(p.rect(p.w - 0.19, p.w - 0.13, 0.86, 1.14) * 0.6, [0.25, 0.25, 0.25])
        if i == 0:                                                                          # door closer arm
            p.put(p.rect(0.12, 0.55, p.h - 0.14, p.h - 0.10), [0.2, 0.2, 0.2], h=0.02)
        if i == 2:                                                                          # louvre in the lower panel
            lv = p.rect(0.25, p.w - 0.25, 0.25, 0.60)
            p.put(lv, np.asarray(c, F32) * (0.45 + 0.55 * (np.abs(((p.Y / 0.035) % 1) - 0.5) * 2))[..., None], h=-0.025)
        scuff = np.clip(1 - p.Y / 0.35, 0, 1) ** 1.5 * (0.6 + 0.4 * p.noise(0.05, 5, (3, 1)))
        p.put(leaf * np.clip(scuff, 0, 1) * 0.55, [0.12, 0.11, 0.10])
        hand = np.exp(-(((p.X - (p.w - 0.2)) / 0.12) ** 2 + ((p.Y - 1.1) / 0.2) ** 2))
        p.put(leaf * hand * 0.3, np.asarray(c) * 0.55)
    else:                                   # house doors
        c = [lin(98, 60, 36), WHITE_PVC, ANTHRACITE][i]
        interior(p, (0.2, p.w - 0.2, 1.25, p.h - 0.25), ["frosted", "frosted", "dark"][i], k=i)
        p.put(p.rect(0, p.w, 0, p.h) * (1 - p.rect(0.25, p.w - 0.25, 1.3, p.h - 0.3)), np.asarray(c, F32), h=-0.01, r=0.5)
        p.put(p.ring(0, p.w, 0, p.h, 0.06), np.asarray(c) * 0.9, h=0.0)
        if i == 0:                                                                          # panelled wood
            for (a, b) in ((0.12, 0.55), (0.65, 1.15)):
                p.put(p.ring(0.16, p.w - 0.16, a, b, 0.02), np.asarray(c) * 0.6, h=-0.016)
            p.alb *= (1 + 0.10 * p.noise(0.02, 3, (0.2, 6)))[..., None]
        if i == 2:
            for yb in (0.5, 0.8, 1.1):
                p.put(p.rect(0.16, p.w - 0.16, yb - 0.008, yb + 0.008), [0.4, 0.4, 0.4])
        p.put(p.rect(p.w - 0.17, p.w - 0.14, 0.9, 1.2), [0.42, 0.42, 0.40], h=0.02, r=0.3)


def scribble(p, R, col, seed, width=0.022, n=None):
    """Content-free spray scribble (no letters, signs or marks of anyone): a few looping strokes with overspray."""
    x0, x1, y0, y1 = R
    rng = np.random.default_rng(seed)
    pts = []
    for s in range(n or rng.integers(2, 5)):
        k = rng.integers(5, 9)
        cx = x0 + (x1 - x0) * (0.15 + 0.7 * rng.random())
        cy = y0 + (y1 - y0) * (0.3 + 0.4 * rng.random())
        ctrl = np.column_stack([cx + (x1 - x0) * 0.22 * rng.standard_normal(k), cy + (y1 - y0) * 0.30 * rng.standard_normal(k)])
        ctrl[:, 0] = np.clip(ctrl[:, 0], x0 + 0.05, x1 - 0.05)
        ctrl[:, 1] = np.clip(ctrl[:, 1], y0 + 0.05, y1 - 0.05)
        t = np.linspace(0, k - 1, k * 60)
        sm = np.column_stack([ndimage.gaussian_filter1d(np.interp(t, np.arange(k), ctrl[:, j]), 22) for j in range(2)])
        pts.append(sm)
    pts = np.concatenate(pts)
    d, _ = cKDTree(pts).query(np.column_stack([p.X.ravel(), p.Y.ravel()]), workers=-1)
    d = d.reshape(p.X.shape)
    line = np.clip((width - d) / (width * 0.5), 0, 1)
    halo = np.exp(-(d / (width * 2.2)) ** 2) * 0.35 * (0.6 + 0.4 * p.noise(0.01, seed % 97))
    a = np.clip(line + halo, 0, 1) * p.rect(x0, x1, y0, y1) * (0.75 + 0.25 * p.noise(0.06, seed % 89 + 1))
    p.put(np.clip(a, 0, 1), col, r=0.55)


def _garage(p, i, kind):
    base = [lin(58, 92, 70), lin(96, 62, 44), lin(150, 153, 155), lin(205, 205, 200), lin(62, 86, 128), lin(120, 60, 46)][i]
    base = np.asarray(base, F32)
    full = p.rect(0, p.w, 0, p.h)
    n1, n2 = p.noise(0.5, 1), p.noise(0.06, 2)
    c = base * (1 + 0.06 * n1 + 0.03 * n2)[..., None]
    p.put(full, c, h=-0.01, r=0.55 if i != 2 else 0.4)
    if i in (2,):                         # trapezoid sheet leaves (blaszak): vertical ribs 0.2 m
        rib = 0.5 + 0.5 * np.cos(6.2832 * p.X / 0.2)
        p.alb *= (0.86 + 0.14 * rib)[..., None]
        p.hgt += -0.012 * (1 - rib)
    if i == 3:                            # up-and-over door: horizontal ribs 0.1 m
        rib = 0.5 + 0.5 * np.cos(6.2832 * p.Y / 0.1)
        p.alb *= (0.9 + 0.1 * rib)[..., None]
        p.hgt += -0.006 * (1 - rib)
        p.put(p.rect(p.w / 2 - 0.08, p.w / 2 + 0.08, 0.95, 1.0), [0.1, 0.1, 0.1], h=0.01)
    else:                                 # two leaves: centre gap, frame angle, hinges, hasp
        p.put(p.rect(p.w / 2 - 0.006, p.w / 2 + 0.006, 0, p.h), base * 0.15, h=-0.03)
        for (a, b) in ((0.04, p.w / 2 - 0.02), (p.w / 2 + 0.02, p.w - 0.04)):
            p.put(p.ring(a, b, 0.03, p.h - 0.04, 0.035), c * 0.88, h=0.0)
            if i in (0, 1, 4, 5):         # X / Z bracing of the leaf on some
                dgn = np.abs((p.Y - 0.03) / (p.h - 0.07) - (p.X - a) / (b - a))
                p.put((dgn < 0.012 / 1.0) * p.rect(a, b, 0.03, p.h - 0.04) * (i in (0, 5)), c * 0.9, h=0.0)
        for xh in (0.03, p.w - 0.03):
            for yh in (0.35, 1.75):
                p.put(p.rect(xh - 0.03, xh + 0.03, yh - 0.05, yh + 0.05), base * 0.5, h=0.01)
        p.put(p.rect(p.w / 2 - 0.07, p.w / 2 + 0.07, 1.0, 1.06), [0.16, 0.15, 0.14], h=0.012, r=0.4)
    p.put(p.ring(0, p.w, -0.1, p.h, 0.04), base * 0.6, h=0.004)
    # rust creeping up from the bottom edge and along the leaf frames, splash dirt, faded paint
    v = p.Y
    rust = np.clip(1 - v / (0.22 + 0.25 * (i in (0, 1, 5))), 0, 1) ** 1.3 * np.clip(0.55 + 0.6 * p.noise(0.09, 4) + 0.4 * n2, 0, 1)
    rust += 0.5 * np.clip(p.noise(0.15, 6) - 1.5, 0, 1) * (i in (0, 1, 2, 5))
    rcol = np.array([0.16, 0.065, 0.03], F32) * (0.8 + 0.4 * p.noise(0.02, 7))[..., None]
    p.put(np.clip(rust, 0, 0.9) * full, rcol, r=0.85)
    p.put(full * np.clip(1 - v / 0.5, 0, 1) ** 2 * 0.35, [0.14, 0.13, 0.11])
    if i == 5:                            # primer patches
        pm = (p.noise(0.5, 8) > 0.8) * full
        p.put(pm * 0.8, lin(128, 128, 126))
    if i == 4:
        scribble(p, (0.2, p.w - 0.2, 0.5, 1.8), [0.03, 0.03, 0.03], 4101)
    if i == 2:
        scribble(p, (0.3, 1.3, 0.7, 1.5), [0.42, 0.43, 0.45], 4102, width=0.018, n=2)


def _balf(p, i, kind):
    """Balcony balustrade front 2.6 x 1.05 m (top rail at 1.0 m, slab edge below)."""
    full = p.rect(0, p.w, 0, p.h)
    # ADR 0094 (review s9 P1-5: balustrade front 37-40 sRGB next to a wall of 155): what shows between bars / around
    # panels is the lit wall and door behind seen through the balustrade, not a black hole (0.045 -> 0.13); frames are
    # painted light grey steel (was dark 92-98 sRGB); the infill colours sit at >= 0.5 of a light wall tone
    shade = np.array([0.13, 0.13, 0.125], F32)
    p.put(full, shade, h=-0.03, r=0.85)                   # the balcony behind, seen through the balustrade
    steel = np.array(lin(150, 153, 154), F32)
    panel = p.rect(0.05, p.w - 0.05, 0.10, 0.93)
    n1 = p.noise(0.4, 1)
    if i == 0:                                            # perforated steel-blue sheet in a grey frame
        c = np.array(lin(150, 160, 166), F32)              # ADR 0097: blue desaturated (was 140, 162, 180)
        hole = (np.hypot((p.X / 0.03) % 1 - 0.5, (p.Y / 0.03) % 1 - 0.5) < 0.2)
        p.put(panel, c * (1 + 0.04 * n1)[..., None] * np.where(hole, 0.5, 1.0)[..., None], h=-0.004, r=0.5)
        for xb in (0.87, 1.73):
            p.put(p.rect(xb - 0.02, xb + 0.02, 0.0, 1.0), steel, h=0.0)
    elif i in (1, 2):                                     # trapezoid sheet, white / brown
        c = np.array([lin(214, 214, 208), lin(160, 134, 114)][i - 1], F32)   # ADR 0097: brown 172, 128, 98 -> less orange
        rib = 0.5 + 0.5 * np.cos(6.2832 * p.X / 0.137)
        p.put(panel, c * (0.82 + 0.18 * rib)[..., None] * (1 + 0.03 * n1)[..., None], r=0.5)
        p.hgt = np.where(panel > 0.5, -0.012 * (1 - rib), p.hgt)
    elif i == 3:                                          # frosted glass panels in a steel frame
        for k in range(3):
            g = p.rect(0.07 + k * 0.85, 0.07 + k * 0.85 + 0.78, 0.14, 0.9)
            p.put(g, np.array([0.40, 0.44, 0.44], F32) * (1 + 0.03 * n1)[..., None], h=-0.01, r=0.25)
    elif i == 4:                                          # vertical bars + flower boxes on the rail
        bars = (np.abs(((p.X / 0.11) % 1) - 0.5) < 0.09) & (p.Y > 0.1) & (p.Y < 0.97)
        p.put(bars * full, steel * 0.85, h=0.0, r=0.5)
        for k in range(3):
            xb = 0.2 + k * 0.8
            p.put(p.rect(xb, xb + 0.6, 0.86, 1.0), lin(120, 70, 50), h=0.02, r=0.7)
            fl = (p.noise(0.03, 20 + k) > 0.1) * p.rect(xb - 0.02, xb + 0.62, 0.95, 1.05, soft=0.02)
            p.put(fl, np.array([0.05, 0.10, 0.03], F32))
            p.put(fl * (p.noise(0.015, 30 + k) > 0.6), [lin(196, 40, 44), lin(214, 70, 120), lin(230, 228, 220)][k])
    elif i == 5:                                          # reed mat tied to the bars
        st = 0.5 + 0.5 * np.sin(6.2832 * p.X / 0.012 + 3 * p.noise(0.05, 5))
        c = np.array(lin(176, 150, 100), F32) * (0.7 + 0.3 * st)[..., None] * (1 + 0.08 * n1)[..., None]
        p.put(panel, c, h=-0.002, r=0.85)
        for yb in (0.25, 0.55, 0.85):
            p.put(p.rect(0.05, p.w - 0.05, yb - 0.004, yb + 0.004) * panel, [0.08, 0.07, 0.05])
    elif i == 6:                                          # flat fibre-cement panels, stained (PRL)
        for k in range(2):
            g = p.rect(0.06 + k * 1.25, 0.06 + k * 1.25 + 1.2, 0.12, 0.92)
            p.put(g, np.array(lin(168, 166, 158), F32) * (1 + 0.06 * n1 + 0.04 * p.noise(0.04, 6, (0.3, 4)))[..., None], h=-0.004)
        run = np.clip(p.noise(0.05, 7, (0.25, 8)) - 0.6, 0, 1) * np.clip((0.95 - p.Y) / 0.5, 0, 1)
        p.put(panel * np.clip(run, 0, 0.6), [0.10, 0.10, 0.09])
    else:                                                 # corrugated green plastic, faded
        rib = 0.5 + 0.5 * np.cos(6.2832 * p.X / 0.076)
        c = np.array(lin(150, 164, 150), F32) * (0.8 + 0.2 * rib)[..., None] * (1 + 0.10 * n1)[..., None]
        p.put(panel, c, r=0.6)
        p.hgt = np.where(panel > 0.5, -0.008 * (1 - rib), p.hgt)
    # frame: top rail, bottom rail, end posts; slab edge with a drip stain at the very bottom
    for (a, b, c_, d) in ((0, p.w, 0.96, 1.02), (0, p.w, 0.08, 0.12), (0, 0.045, 0.0, 1.0), (p.w - 0.045, p.w, 0.0, 1.0)):
        p.put(p.rect(a, b, c_, d), steel * (1 + 0.05 * n1)[..., None], h=0.004, r=0.5)
    rust = np.clip(p.noise(0.07, 9) - 1.7, 0, 1) * p.rect(0, p.w, 0.07, 0.13)      # few rust blooms on the bottom rail
    p.put(np.clip(rust * 2, 0, 0.6), [0.20, 0.10, 0.05])


def _balg(p, i, kind):
    """Balcony glazing-in (zabudowa balkonu): frames between the balustrade rail and the slab above."""
    R = (0, p.w, 0, p.h)
    G = (0.06, p.w - 0.06, 0.06, p.h - 0.06)
    v = [("net", {}), ("roller", dict(col=BLIND[0], frac=0.35)), ("dark", dict(plants=2))][i]
    interior(p, G, v[0], k=i, **v[1])
    if i == 2:                                            # shelves / stored things behind the glass
        for k in range(3):
            p.put(p.rect(1.5 + 0.3 * k, 1.75 + 0.3 * k, 0.06, 0.45 + 0.2 * (k % 2)), [lin(120, 96, 70), lin(70, 90, 120), lin(150, 150, 146)][k])
    window(p, R, [1, 1, 1, 1] if i == 0 else 3, frame=[ALU_GREY, WHITE_PVC, lin(196, 194, 186)][i], fw=0.045, sw=0.035,
           handle=False, dirt=0.4)


def _small(p, i, kind):
    full = p.rect(0, p.w, 0, p.h)
    if kind == "ac":
        c = np.array([lin(214, 214, 208), lin(176, 178, 176)][i], F32)
        p.put(full, c * (1 + 0.03 * p.noise(0.2, 1))[..., None], h=0.0, r=0.5)
        cx, cy, r = p.w * 0.36, p.h * 0.5, p.h * 0.40
        d = np.hypot(p.X - cx, p.Y - cy)
        grille = p.disc(cx, cy, r)
        rings = 0.5 + 0.5 * np.cos(6.2832 * d / 0.022)
        p.put(grille, c * 0.25 + 0.01, h=-0.02)
        p.put(grille * (rings > 0.55), c * 0.8, h=-0.006)
        ang = np.arctan2(p.Y - cy, p.X - cx)
        p.put(grille * (np.abs(np.sin(ang * 4)) < 0.06), c * 0.8, h=-0.004)
        p.put(p.disc(cx, cy, 0.05), c * 0.9, h=0.0)
        lv = p.rect(p.w * 0.74, p.w - 0.04, 0.08, p.h - 0.08)
        p.put(lv * (np.abs(((p.Y / 0.03) % 1) - 0.5) < 0.2), c * 0.45, h=-0.004)
        p.put(full * np.clip(1 - p.Y / 0.1, 0, 1) * 0.4, [0.2, 0.19, 0.17])
    elif kind == "vent":
        c = np.array([lin(150, 152, 152), lin(220, 220, 214)][i], F32)
        p.put(full, c, h=0.0, r=0.45)
        if i == 0:
            sl = np.abs(((p.Y / 0.05) % 1) - 0.5) * 2
            p.put(p.rect(0.04, p.w - 0.04, 0.04, p.h - 0.04), c * (0.3 + 0.7 * sl)[..., None], h=-0.01)
        else:
            d = np.hypot(p.X - p.w / 2, p.Y - p.h / 2)
            p.put(p.disc(p.w / 2, p.h / 2, 0.19) * (np.cos(6.2832 * d / 0.035) > 0), c * 0.35, h=-0.01)
        p.put(full * np.clip((p.h * 0.3 - p.Y) / 0.2, 0, 1) * 0.3, [0.1, 0.1, 0.09])       # soot under the grille
    elif kind == "elbox":
        c = np.array([lin(150, 152, 150), lin(206, 172, 40)][i], F32)
        p.put(full, c * (1 + 0.04 * p.noise(0.2, 1))[..., None], h=0.0, r=0.5)
        p.put(p.ring(0.03, p.w - 0.03, 0.03, p.h - 0.03, 0.006), c * 0.3, h=-0.01)
        p.put(p.disc(p.w - 0.09, p.h / 2, 0.016), [0.08, 0.08, 0.08])
        if i == 0:
            for yv in (0.12, 0.16, 0.20):
                p.put(p.rect(0.12, p.w - 0.12, yv - 0.008, yv + 0.008), c * 0.4)
        p.put(full * np.clip(p.noise(0.06, 3) - 1.4, 0, 1), [0.17, 0.07, 0.03])
    else:                                   # plate: 0 intercom panel, 1 blank enamel number plate
        if i == 0:
            p.put(full, [0.36, 0.37, 0.37], r=0.35)
            for r_ in range(5):
                for c_ in range(3):
                    p.put(p.disc(0.08 + 0.07 * c_, 0.05 + 0.045 * r_, 0.014), [0.09, 0.09, 0.09])
            p.put(p.rect(0.06, p.w - 0.06, 0.30, 0.36) * (np.sin(p.Y / 0.008 * 6.28) > 0), [0.05, 0.05, 0.05])
        else:
            p.put(full, lin(30, 52, 110), r=0.3)
            p.put(p.ring(0.012, p.w - 0.012, 0.012, p.h - 0.012, 0.01), lin(225, 225, 220))


SWATCH_COL = {
    "pvc_white": (WHITE_PVC, 0.42), "alu_sill": ((0.40, 0.40, 0.39), 0.4), "concrete": ((0.30, 0.30, 0.28), 0.9),
    "steel_grey": (tuple(lin(92, 96, 98)), 0.5), "steel_dark": ((0.05, 0.052, 0.055), 0.5), "galv": ((0.40, 0.41, 0.41), 0.45),
    "wood": (tuple(lin(120, 84, 52)), 0.8), "pvc_brown": (BROWN_PVC, 0.42), "cloth_white": (tuple(lin(225, 224, 218)), 0.9),
    "cloth_red": (tuple(lin(170, 44, 48)), 0.9), "cloth_blue": (tuple(lin(60, 90, 150)), 0.9),
    "cloth_dark": (tuple(lin(40, 44, 54)), 0.9), "cloth_yellow": (tuple(lin(214, 180, 70)), 0.9),
    "cloth_green": (tuple(lin(84, 130, 92)), 0.9), "dish": (tuple(lin(176, 177, 174)), 0.45),
    "rubber": ((0.02, 0.02, 0.02), 0.85), "glass_dark": ((0.025, 0.03, 0.032), 0.07), "roof_felt": ((0.06, 0.06, 0.06), 0.9),
    "terracotta": (tuple(lin(150, 82, 55)), 0.85), "leaf": ((0.045, 0.09, 0.03), 0.8),
}


def _swatch(p, name):
    c, r = SWATCH_COL[name]
    n = p.noise(0.04, 1)
    p.put(p.rect(-1, p.w + 1, -1, p.h + 1), np.asarray(c, F32) * (1 + 0.05 * n)[..., None], h=0.0, r=r)
    if name.startswith("cloth"):
        p.alb *= (0.85 + 0.15 * _folds(p, p.X / p.w, 3, 1, 0.6))[..., None]


PAINT = {"w2": _resid, "w1": _resid, "w3": _resid, "bdoor": _resid, "bwin": _resid, "stair": _resid, "base": _resid,
         "house": _resid, "off": _office, "hallw": _office, "indw": _office, "door_block": _door, "door_steel": _door,
         "door_house": _door, "garage": _garage, "balf": _balf, "balg": _balg, "ac": _small, "vent": _small,
         "elbox": _small, "plate": _small}
_CACHE = {}


def paint_cell(kind, i, px):
    if kind in A.KINDS:
        i = i % A.KINDS[kind][2]
    key = (kind, i, round(px, 6))
    if key not in _CACHE:
        if kind.startswith("sw_"):
            p = P(A.SWATCH_M, A.SWATCH_M, px, A.hint(kind) % 100000)
            _swatch(p, kind[3:])
        else:
            w, h, _ = A.KINDS[kind]
            p = P(w, h, px, A.hint(kind, i) % 100000)
            PAINT[kind](p, i, kind)
        p.alb = np.clip(p.alb, 0.008, 0.9)
        _CACHE[key] = p
    return _CACHE[key]


def facade_atlas(nx=4096):
    c = K.Ctx(nx, nx, A.ATLAS_M[0], A.ATLAS_M[1], seed=811)
    alb = np.full((c.ny, c.nx, 3), 0.25, F32)
    h = np.zeros((c.ny, c.nx), F32)
    rough = np.full((c.ny, c.nx), 0.8, F32)
    g = int(round(A.GUTTER / c.px))
    for (kind, i), (u0, v0, w, hh) in A.CELLS.items():
        p = paint_cell(kind, i, c.px)
        col = int(round(u0 / c.px))
        row = c.ny - int(round((v0 + hh) / c.px))
        a = np.pad(p.alb, ((g, g), (g, g), (0, 0)), mode="edge")
        r0, c0 = row - g, col - g
        alb[r0:r0 + a.shape[0], c0:c0 + a.shape[1]] = a
        h[r0:r0 + a.shape[0], c0:c0 + a.shape[1]] = np.pad(p.hgt, g, mode="edge")
        rough[r0:r0 + a.shape[0], c0:c0 + a.shape[1]] = np.pad(p.rgh, g, mode="edge")
    z = np.zeros((c.ny, c.nx), F32)
    s = K.SurfaceSet("facade_atlas", c, alb, h, np.clip(rough, 0.04, 1), z, z, ao_k=0.35, ao_scales=(0.02, 0.06))
    s.aux_div = 2          # texture budget (ADR 0081): relief / mask / var at half the albedo size
    return s


# ------------------------------------------------------------------------------------------- LOD1 rows
def _far_paste(dst_a, dst_r, px, x, y, p):
    """Paste a painted cell with its lower-left corner at (x, y) metres of the row canvas (y up)."""
    ny = dst_a.shape[0]
    c0 = int(round(x / px))
    r0 = ny - int(round(y / px)) - p.ny
    r1, c1 = r0 + p.ny, c0 + p.nx
    if r0 < 0 or c0 < 0 or r1 > ny or c1 > dst_a.shape[1]:
        return
    dst_a[r0:r1, c0:c1] = p.alb
    dst_r[r0:r1, c0:c1] = p.rgh


def facade_far(nx=2048):
    """Storey rows for LOD1 walls. Modulation set: wall = 0.5; window content at ~true albedo for a mid-tone wall
    (engine albedo = 2 x wall colour x map), so frames take a little of the wall colour - invisible at LOD1 range."""
    Lx, Ly = A.FAR_M
    ny = int(round(nx * Ly / Lx)) // 4 * 4
    c = K.Ctx(nx, ny, Lx, Ly, seed=812)
    px = Lx / nx
    alb = np.full((ny, nx, 3), 0.5, F32)
    rough = np.full((ny, nx), 0.9, F32)
    h = np.zeros((ny, nx), F32)
    k_alb = 1.0 / (2 * 0.45)
    for group, row in A.FAR_ORDER:
        vf = A.far_row_v(group, row)
        sill = A.FAR_SILL[group]
        for bay in range(A.FAR_BAYS):
            kind, var = A.FAR_ROWS[group][row][bay]
            xc = (bay + 0.5) * A.FAR_PITCH
            if kind == "bal":
                d, w_ = paint_cell("bdoor", var, px), paint_cell("bwin", var, px)
                x0 = xc - 1.05
                _far_paste(alb, rough, px, x0, vf + 0.05, d)
                _far_paste(alb, rough, px, x0 + 0.9, vf + 0.05 + 0.85, w_)
                f = paint_cell("balf", A.bal_type(group), px)     # ADR 0097: one balustrade type per row group
                _far_paste(alb, rough, px, xc - 1.3, vf + 0.02, f)
                # slab edge + its shadow line
                r0 = ny - int(round((vf + 0.02) / px))
                ca, cb = int(round((xc - 1.35) / px)), int(round((xc + 1.35) / px))
                alb[r0:r0 + max(2, int(0.16 / px)), ca:cb] = 0.30 * k_alb
            elif kind == "rib":
                p = paint_cell("off", var, px)
                # ribbon: office panes side by side across the whole bay
                for j in range(2):
                    _far_paste(alb, rough, px, bay * A.FAR_PITCH + j * 1.5, vf + sill, p)
            else:
                p = paint_cell(kind, var, px)
                _far_paste(alb, rough, px, xc - p.w / 2, vf + sill, p)
                # sill flashing + a faint dirt run under it
                r0 = ny - int(round((vf + sill) / px))
                ca, cb = int(round((xc - p.w / 2 - 0.04) / px)), int(round((xc + p.w / 2 + 0.04) / px))
                alb[r0:r0 + max(1, int(0.04 / px)), ca:cb] = 0.36
                alb[r0 + max(1, int(0.04 / px)):r0 + int(0.5 / px), ca:cb] *= 0.965
    wall = (rough > 0.85) & (np.abs(alb[..., 0] - 0.5) < 0.02)
    alb = np.where(wall[..., None], alb, np.clip(alb * k_alb, 0.01, 0.95))
    n1 = K.noise(c, 1, 0.3, 4.0, beta=1.0)
    alb = np.where(wall[..., None], alb * (1 + 0.025 * n1)[..., None], alb).astype(F32)
    z = np.zeros((ny, nx), F32)
    s = K.SurfaceSet("facade_far", c, alb, h, np.clip(rough, 0.04, 1).astype(F32), z, z, ao_k=0.0)
    s.aa_tiers = True
    s.aux_div = 4          # flat set (no relief): normal / mask / var at a quarter of the albedo size (ADR 0081 budget)
    return s


# ------------------------------------------------------------------------------------------- concrete fence
def fence_concrete(nx=2048):
    Lx, Ly = A.FENCE_M
    ny = int(round(nx * Ly / Lx)) // 4 * 4
    c = K.Ctx(nx, ny, Lx, Ly, seed=813)
    X, Yd = c.xy()
    V = Ly - Yd
    sstep, noise = K.sstep, K.noise
    n_fine = noise(c, 1, c.px * 2, 0.03, beta=0.4)
    n_mid = noise(c, 2, 0.1, 1.0, beta=1.0)
    n_big = noise(c, 3, 0.8, 6.0, beta=1.2)
    n_run = noise(c, 4, 0.03, 0.8, beta=0.9, aniso=1.0 / 8.0)        # vertical run-off
    n_agg = noise(c, 5, 0.006, 0.02, beta=0.2)
    g = A.GUTTER
    bw, bh = A.FENCE_BAY
    tone = np.ones_like(X)
    h = 0.2e-3 * n_fine
    dirt = np.zeros_like(X)
    moss = np.zeros_like(X)
    rust = np.zeros_like(X)
    joint = np.zeros_like(X)
    crack = np.zeros_like(X)
    paint = np.zeros((*X.shape, 4), F32)                   # rgb + alpha of spray
    # ---- row 0: bays of four 0.5 m plates between posts
    y0 = g
    v = V - y0
    in0 = (v > -g) & (v < bh + g) & (X < A.FENCE_VARIANTS["plate"] * bw + g)
    bay = np.floor(np.clip(X, 0, None) / bw).astype(np.int64)
    ub = X - bay * bw
    plate = np.clip(np.floor(v / 0.5), 0, 3).astype(np.int64)
    pv = v - plate * 0.5
    dj = np.minimum(pv, 0.5 - pv)
    jm = sstep(0.016, 0.004, dj) * (v > 0.02) * (v < bh - 0.02) * in0
    joint = np.maximum(joint, jm)
    h -= 6e-3 * jm
    pt = K.hash01(bay * 17 + plate, 31)
    tone = np.where(in0, tone * (0.90 + 0.20 * pt), tone)             # every plate is its own cast
    # per-plate out-of-plane step (plates never sit flush in the post slots)
    h += np.where(in0, (K.hash01(bay * 17 + plate, 32) - 0.5) * 6e-3, 0)
    # plate face styles per bay: 0-2 plain float finish, 3 board-marked, 4 plain new (repair), 5 split-stone relief,
    # 6 plain mossy, 7 plain with a crack
    style = bay % 8
    boards = (style == 3) & in0
    bd = np.abs(((pv / 0.125) % 1.0) - 0.5)
    h -= 1.5e-3 * sstep(0.46, 0.5, bd) * boards
    tone = np.where(boards, tone * (1 + 0.04 * np.sin(X * 40 + 6 * K.hash01(np.floor(pv / 0.125).astype(np.int64) + plate * 5, 33))), tone)
    stone = (style == 5) & in0
    if stone.any():
        d1, d2, i1, _, _ = K.voronoi(c, 6, 0.16, jitter=0.9, cell_y=0.10)
        ed = K.edge_dist(d1, d2)
        relief = sstep(0.0, 0.03, ed) * (0.6 + 0.4 * K.hash01(i1, 34))
        h += np.where(stone, 9e-3 * relief - 5e-3, 0)
        tone = np.where(stone, tone * (0.86 + 0.2 * K.hash01(i1, 35)) * (0.8 + 0.2 * sstep(0.0, 0.02, ed)), tone)
    tone = np.where((style == 4) & in0 & (plate == 2), tone * 1.22, tone)          # one replaced plate, lighter
    # weathering: run-off below every joint and from the top, splash + green algae at the foot, exposed aggregate
    under = sstep(0.35, 0.0, 0.5 - pv)
    dirt += in0 * 0.22 * sstep(0.3, 1.6, n_run) * under
    dirt += in0 * 0.30 * sstep(0.5, 2.0, n_run + 0.6 * n_big) * sstep(bh, bh - 0.9, v)
    splash = sstep(0.55 + 0.15 * n_mid, 0.05, v) ** 1.4
    dirt += in0 * 0.35 * splash
    wet = sstep(0.2, 1.4, n_big + 0.5 * n_mid)
    moss += in0 * sstep(0.45 + 0.25 * wet, 0.0, v) * wet * np.where(style == 6, 1.0, 0.45)
    moss += in0 * 0.5 * sstep(0.03, 0.0, dj) * wet * (v > 0.3)                       # algae lines in damp joints
    tone *= 1 - 0.10 * sstep(1.2, 2.6, n_agg) * in0                                 # pin holes
    h -= 0.8e-3 * sstep(1.2, 2.6, n_agg) * in0
    # crack through two plates of bay 7, rust bleeding at a spalled corner of bay 2
    cx = 7 * bw + 1.1 + 0.08 * np.sin(v * 9) + 0.05 * n_mid
    cm = sstep(0.006, 0.0015, np.abs(X - cx)) * (v > 0.5) * (v < 1.5) * in0
    crack = np.maximum(crack, cm)
    sp = np.exp(-(((X - (2 * bw + 1.75)) / 0.09) ** 2 + ((v - 1.02) / 0.05) ** 2))
    h -= 8e-3 * sstep(0.4, 0.8, sp)
    rust += in0 * 0.8 * sstep(0.5, 0.9, sp)
    rust += in0 * 0.5 * np.exp(-((X - (2 * bw + 1.75)) / 0.03) ** 2) * sstep(1.0, 0.95, v) * sstep(0.35, 1.0, v) * (0.5 + 0.5 * n_run)
    # ---- row 1: framed monolithic panels (older type): raised 0.11 m frame, recessed exposed-aggregate field
    y1 = g + bh + 2 * g
    v1 = V - y1
    in1 = (v1 > -g) & (v1 < bh + g) & (X < A.FENCE_VARIANTS["frame"] * bw + g)
    bay1 = np.floor(np.clip(X, 0, None) / bw).astype(np.int64)
    u1 = X - bay1 * bw
    fd = np.minimum(np.minimum(u1 - 0.06, bw - 0.06 - u1), np.minimum(v1 - 0.02, bh - 0.02 - v1))
    field = sstep(0.11, 0.135, fd)
    h += np.where(in1, -9e-3 * field + 1.6e-3 * n_agg * field, 0)
    tone = np.where(in1, tone * (0.80 + 0.12 * K.hash01(bay1, 41)) * (1 - 0.10 * field * sstep(0.0, 1.5, n_agg)), tone)
    dirt += in1 * 0.38 * sstep(0.2, 1.8, n_run + 0.5 * n_big) * sstep(bh, bh - 1.3, v1)
    dirt += in1 * 0.30 * sstep(0.6, 0.05, v1) ** 1.3
    dirt += in1 * 0.25 * sstep(0.03, 0.0, np.abs(fd - 0.12))                         # dust on the frame ledge
    moss += in1 * sstep(0.5, 0.0, v1) * wet * 0.8
    rb = np.exp(-(((u1 - 0.5) / 0.02) ** 2)) * sstep(1.2, 1.15, v1) * sstep(0.5, 1.1, v1) * (bay1 == 1)
    rust += in1 * 0.6 * rb * (0.5 + 0.5 * n_run)
    joint = np.maximum(joint, in1 * sstep(0.012, 0.004, np.minimum(u1, bw - u1)))
    # ---- post strip (unrolled 0.30 m) right of the framed panels
    pu0, pv0, pw_, ph_ = A.fence_post_uv()
    inp = (X > pu0 - g) & (X < pu0 + pw_ + g) & (V > pv0 - g) & (V < pv0 + ph_ + g)
    tone = np.where(inp, 0.98 + 0.05 * n_mid, tone)
    dirt = np.where(inp, 0.25 * sstep(0.2, 1.6, n_run) + 0.3 * sstep(0.5, 0.0, V - pv0), dirt)
    moss = np.where(inp, 0.4 * sstep(0.35, 0.0, V - pv0) * wet, moss)

    # ---- compose
    CONC = 0.30
    conc = CONC * tone * (1 + 0.03 * n_mid + 0.04 * n_big)
    chroma = np.array([1.03, 1.0, 0.93], F32)
    alb = conc[..., None] * chroma
    dirt = np.clip(dirt, 0, 0.8)
    alb = alb * (1 - dirt[..., None]) + np.array([0.075, 0.068, 0.058], F32) * dirt[..., None]
    moss = np.clip(moss, 0, 0.75) * (0.6 + 0.4 * sstep(-0.5, 1.0, n_fine))
    alb = alb * (1 - moss[..., None]) + np.array([0.055, 0.085, 0.035], F32) * moss[..., None]
    rust = np.clip(rust, 0, 0.8)
    alb = alb * (1 - rust[..., None]) + np.array([0.20, 0.085, 0.035], F32) * rust[..., None]
    alb *= (1 - 0.6 * joint - 0.75 * crack)[..., None]
    h -= 2.5e-3 * crack
    rough = 0.88 + 0.06 * dirt - 0.05 * moss

    s = K.SurfaceSet("fence_concrete", c, np.clip(alb, 0.01, 0.9).astype(F32), h.astype(F32),
                     np.clip(rough, 0.3, 1).astype(F32), (K.hash01(bay * 17 + plate, 36)).astype(F32),
                     np.clip(joint, 0, 1).astype(F32), ao_k=0.6)
    try:
        import sets_scan as SC
        if SC.available("concrete_floor_worn_001"):
            s = SC.hybrid(s, "concrete_floor_worn_001", 6381, alb_k=1.3, h_k=0.7)
    except Exception as e:      # noqa: BLE001 - the set must build offline too
        print("  fence_concrete: scan detail skipped:", e)
    # calibrated set: the scan detail shifts the mean, bring it back to the 0.30 target (test_cc0_scans)
    s.albedo = (s.albedo * (0.30 / float((s.albedo @ K.LUM).mean()))).astype(F32)
    # content-free spray scribbles (after the scan detail: paint covers the concrete tone), on 3 bays
    canvas = P(Lx, Ly, c.px, 4200)
    canvas.alb, canvas.rgh = s.albedo, s.rough
    scribble(canvas, (1 * bw + 0.25, 1 * bw + 1.75, g + 0.5, g + 1.7), [0.025, 0.025, 0.028], 4201, width=0.03)
    scribble(canvas, (5 * bw + 0.2, 5 * bw + 1.3, g + 0.7, g + 1.6), [0.42, 0.44, 0.47], 4202, width=0.024, n=2)
    scribble(canvas, (3 * bw + 0.3, 3 * bw + 1.7, y1 + 0.5, y1 + 1.6), [0.10, 0.16, 0.36], 4203, width=0.028)
    # grey rectangle where a scribble was painted over (bay 6): the commonest "clean-up" on such fences
    over = canvas.rect(6 * bw + 0.35, 6 * bw + 1.55, g + 0.75, g + 1.6, soft=0.02) * (0.85 + 0.15 * canvas.noise(0.1, 3))
    canvas.put(np.clip(over, 0, 1) * 0.9, [0.34, 0.345, 0.33])
    s.albedo, s.rough = np.clip(canvas.alb, 0.01, 0.9).astype(F32), np.clip(canvas.rgh, 0.3, 1).astype(F32)
    return s


BUILDING_SETS = {
    "facade_atlas": dict(fn=facade_atlas, tile_m=list(A.ATLAS_M), target=None, kind="tiling_set",
        uv="mesh_uv0_metres (atlas cells, layout tools/worldgen/streetscape/facade_atlas.py)",
        slots=["facade_atlas (windows, doors, garage doors, balustrades, facade equipment; ADR 0081)"],
        note="Cell atlas 16 x 16 m. Calibrated: every cell carries its real albedo (tint 1)."),
    "facade_far": dict(fn=facade_far, tile_m=list(A.FAR_M), target=0.5, kind="modulation_set",
        uv="mesh_uv0_metres (u = bay x 3 m, v = row; layout facade_atlas.FAR_*)",
        slots=["<wall>__far_block / __far_office / __far_ribbon (LOD1 window zone; ADR 0081)"],
        note="Storey rows of 8 bays composed from the facade_atlas cells; wall = neutral 0.5 tinted by the wall colour."),
    "fence_concrete": dict(fn=fence_concrete, tile_m=list(A.FENCE_M), target=0.30, kind="tiling_set",
        uv="mesh_uv0_metres (bay cells, layout facade_atlas.fence_uv)",
        slots=["concrete_fence, concrete_fence_post (prefabricated fence; ADR 0081)"],
        note="Strip atlas 16 x 4.5 m: 8 bays of stacked 0.5 m plates, 5 framed panels, post strip. Micro detail from the "
             "CC0 scan concrete_floor_worn_001 (Poly Haven) when fetched."),
}
