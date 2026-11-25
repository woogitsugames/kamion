"""Atlas of the roadside / field-margin plants and the maize rows (ADR 0324 r5, ADR 0334 r3; material `verge_tufts`).

Critic s24 wave10-pre 1 / #7: the r4 atlas had 16 tufts, but all 16 were the same growth form - a symmetric fan of
grass blades on a straight foot line - so the verge read as "one sprite at an even rhythm". This atlas holds plants
of DIFFERENT growth forms (what stands on a Podlasie verge and baulk in August): grass tussocks, bleached stalks with
panicles, dock with rust-brown seed spikes, tansy (yellow button heads), yarrow / wild carrot (white flat umbels),
mugwort (grey-green bush), chicory (wiry stems, blue flowers), broad-leaf rosettes, clover mats, flattened dead grass.

Layout (2048 x 1024, v from the image bottom):
  v 0.00 .. 0.25   SHORT row, 8 cells of 0.5 m: plants of the shoulder edge (to ~0.4 m)
  v 0.25 .. 0.50   TALL row, 8 cells of 0.5 m: plants of slopes, ditch bottoms and baulks (to ~1.1 m)
  v 0.50 .. 1.00   MAIZE row, 4 cells of 1.6 m x 2.4 m: a run of fodder maize plants seen from the side (tassels,
                   cobs, drying lower leaves), two depth layers so a card is a dense wall
Every cell is painted on its own canvas (no bleed into the neighbour, transparent margins), so a card that maps one
cell shows one whole plant. Colours sRGB around the calibrated terrain grass (linear 0.08 / 0.105 / 0.038).
All shapes WORKING_VALUE (no botanical survey; Wikimedia Commons CC BY-SA photos of Polish verges viewed only).
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

TEX_W, TEX_H = 2048, 1024
NT = 8                            # cells per plant row
N_MAIZE = 4                       # cells of the maize row
MAIZE_CELL_M = 1.6                # metres of row one maize cell stands for
MAIZE_H_M = 2.4                   # metres the maize row height stands for (plants 2.0-2.35 m, WORKING_VALUE)
V_SHORT = (0.0, 0.25)
V_TALL = (0.25, 0.5)
V_MAIZE = (0.5, 1.0)
# growth forms per cell (the generator picks cells by form, see verge_flora.FORMS_*)
SHORT_FORMS = ("tuft", "tuft_dry", "rosette", "clover", "flat_dead", "wisp", "hawkbit", "yarrow_low")
TALL_FORMS = ("tussock", "tussock_dry", "stalks", "dock", "tansy", "yarrow", "mugwort", "chicory")

GREENS = [np.array(c, float) for c in ((84, 98, 52), (72, 90, 50), (98, 106, 58), (66, 84, 46))]
DRY = np.array([142, 130, 86], float)
DARK = np.array([42, 52, 30], float)
HEAD = np.array([150, 138, 96], float)
S = 2                             # supersampling


class _Cell:
    """One cell canvas (supersampled RGBA); x in 0..w, y from the foot upward (0 = ground line)."""

    def __init__(self, w, h, rng):
        self.w, self.h, self.rng = w, h, rng
        self.im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    def col(self, c, k=None, lo=0.82, span=0.34):
        k = self.rng.random() if k is None else k
        return tuple(int(v) for v in np.clip(np.asarray(c, float) * (lo + span * k), 0, 255)) + (255,)

    def _xy(self, pts):
        return [(float(x), float(self.h - 2 - y)) for x, y in pts]

    def stroke(self, pts, w0, w1, c):
        q = self._xy(pts)
        for i in range(len(q) - 1):
            w = w0 + (w1 - w0) * i / max(len(q) - 2, 1)
            self.d.line([q[i], q[i + 1]], fill=c, width=max(1, int(round(w))))

    def blade(self, x, h, lean, bend, w0, c, n=7):
        pts = [(x + (lean * t + bend * t * t) * h, h * t) for t in np.linspace(0, 1, n)]
        self.stroke(pts, w0, 0.9 * S, c)
        return pts[-1]

    def leaf(self, base, ang, length, width, c, droop=0.0, rib=None, n=9):
        """A lanceolate leaf from `base`, initial direction `ang` (rad from +x), bending down by `droop` rad."""
        mid, a = [np.array(base, float)], ang
        for i in range(n):
            a2 = ang - droop * ((i + 1) / n) ** 1.5 * np.sign(math.cos(ang) if abs(math.cos(ang)) > 1e-3 else 1.0) \
                if droop else ang
            mid.append(mid[-1] + np.array([math.cos(a2), math.sin(a2)]) * length / n)
            a = a2
        left, right = [], []
        for i, p in enumerate(mid):
            t = i / n
            hw = 0.5 * width * math.sin(math.pi * min(0.08 + 0.92 * t, 1.0) ** 0.75) * (1.0 - 0.35 * t)
            j = min(i + 1, n)
            dv = mid[j] - mid[max(j - 1, 0)]
            dv = dv / max(float(np.hypot(*dv)), 1e-6)
            nrm = np.array([-dv[1], dv[0]])
            left.append(p + nrm * hw)
            right.append(p - nrm * hw)
        self.d.polygon(self._xy(left + right[::-1]), fill=c)
        if rib is not None:
            self.stroke([tuple(p) for p in mid], 1.4 * S, 0.8 * S, rib)
        return mid[-1]

    def dot(self, x, y, r, c):
        (px, py), = self._xy([(x, y)])
        self.d.ellipse([px - r, py - r, px + r, py + r], fill=c)


def _fan(cell, n, hmin, hmax, w0, dry_share, base_share, heads, lean0=0.0, spread=1.0, tone=1.0, cx=0.5):
    rng, cw, rh = cell.rng, cell.w, cell.h
    for _ in range(n):
        off = float(np.clip(rng.normal(0, 0.13 * spread), -0.30, 0.30))
        x = (cx + off) * cw
        env = max(0.25, 1.0 - (abs(off) / 0.32) ** 2 * 0.55)
        h = (hmin + (hmax - hmin) * rng.random() ** 1.6) * rh * env
        lean = off * 1.6 + rng.normal(0, 0.10) + lean0
        bend = rng.normal(0, 0.16)
        reach = abs(lean) * h + abs(bend) * h
        if abs(off) * cw + reach > 0.46 * cw:
            sc = max(0.25, (0.46 * cw - abs(off) * cw) / max(reach, 1e-6))
            lean, bend = lean * sc, bend * sc
        c = DRY if rng.random() < dry_share else GREENS[int(rng.integers(0, len(GREENS)))]
        if rng.random() < base_share:
            c = DARK * rng.uniform(0.9, 1.6)
        tip = cell.blade(x, h, lean, bend, w0 * S, cell.col(c * tone))
        if heads and h > 0.6 * rh and rng.random() < heads:
            L = rng.uniform(0.06, 0.12) * rh
            for q in range(14):
                t = q / 13.0
                sx, sy = tip[0] - (lean + 2 * bend) * L * t * 0.3, tip[1] - L * t
                a = rng.uniform(-1.0, 1.0)
                cell.stroke([(sx, sy), (sx + math.sin(a) * L * 0.22, sy + abs(math.cos(a)) * L * 0.10)],
                            2.2 * S, 1.0 * S, cell.col(HEAD))


def _stems(cell, n, hmin, hmax, w0, c, spread=0.16, lean_sd=0.10, bend_sd=0.10):
    """Upright stems; returns [(tip, base x, height, lean, bend)]."""
    rng, cw, rh = cell.rng, cell.w, cell.h
    out = []
    for _ in range(n):
        x = (0.5 + float(np.clip(rng.normal(0, spread), -0.26, 0.26))) * cw
        h = (hmin + (hmax - hmin) * rng.random()) * rh
        lean, bend = rng.normal(0, lean_sd), rng.normal(0, bend_sd)
        mx = 0.46 * cw - abs(x - 0.5 * cw)
        if (abs(lean) + abs(bend)) * h > mx:
            k = mx / max((abs(lean) + abs(bend)) * h, 1e-6)
            lean, bend = lean * k, bend * k
        tip = cell.blade(x, h, lean, bend, w0 * S, cell.col(c), n=9)
        out.append((tip, x, h, lean, bend))
    return out


def _at(x, h, lean, bend, t):
    return x + (lean * t + bend * t * t) * h, h * t


def _paint_tall(form, cell):
    rng, cw, rh = cell.rng, cell.w, cell.h
    if form == "tussock":
        _fan(cell, 60, 0.06, 0.26, 4.5, 0.06, 0.55, 0.0)
        _fan(cell, 120, 0.22, 0.72, 3.6, 0.07, 0.12, 0.0)
        _fan(cell, 50, 0.50, 0.97, 3.0, 0.08, 0.03, 0.30)
    elif form == "tussock_dry":
        _fan(cell, 40, 0.06, 0.24, 4.5, 0.35, 0.45, 0.0, spread=1.25)
        _fan(cell, 70, 0.20, 0.60, 3.4, 0.55, 0.08, 0.0, lean0=0.22, spread=1.25, tone=1.08)
        _fan(cell, 22, 0.45, 0.80, 2.8, 0.70, 0.02, 0.20, lean0=0.25, tone=1.1)
    elif form == "stalks":
        _fan(cell, 45, 0.05, 0.22, 4.2, 0.20, 0.50, 0.0, spread=0.9)
        for tip, x, h, lean, bend in _stems(cell, 9, 0.62, 0.98, 2.4, DRY * 0.95, spread=0.12, lean_sd=0.07, bend_sd=0.09):
            L = rng.uniform(0.10, 0.16) * rh                 # loose bleached panicle (reed grass)
            for q in range(26):
                t = q / 25.0
                sx, sy = _at(x, h, lean, bend, 1.0 - t * L / h)
                a = rng.uniform(-1.2, 1.2)
                cell.stroke([(sx, sy), (sx + math.sin(a) * L * 0.30, sy + abs(math.cos(a)) * L * 0.14)],
                            2.0 * S, 0.9 * S, cell.col(HEAD * rng.uniform(0.9, 1.12)))
    elif form == "dock":
        # broad wavy basal leaves, 2-3 stiff stems with dense rust-brown seed spikes (Rumex, August)
        for i in range(9):
            sg = -1.0 if i % 2 else 1.0
            ang = math.pi / 2 - sg * rng.uniform(0.35, 1.25)
            c = cell.col(np.array([58, 86, 42]) * rng.uniform(0.85, 1.15))
            cell.leaf((0.5 * cw + rng.normal(0, 0.03) * cw, 0.0), ang, rng.uniform(0.26, 0.44) * rh,
                      rng.uniform(0.07, 0.11) * cw * 1.8, c, droop=rng.uniform(0.3, 0.9), rib=cell.col((96, 118, 66)))
        rust = np.array([112, 58, 34])
        for tip, x, h, lean, bend in _stems(cell, 3, 0.70, 0.98, 3.4, np.array([104, 72, 44]), spread=0.07, lean_sd=0.06, bend_sd=0.04):
            for q in range(170):
                t = rng.uniform(0.42, 1.0)
                sx, sy = _at(x, h, lean, bend, t)
                r = (1.0 - 0.6 * (t - 0.42) / 0.58) * 0.045 * cw
                cell.dot(sx + rng.normal(0, r * 0.55), sy + rng.normal(0, 3.0), rng.uniform(1.6, 3.0) * S,
                         cell.col(rust * rng.uniform(0.75, 1.3)))
    elif form == "tansy":
        # stiff leafy stems, flat-topped corymbs of yellow buttons (Tanacetum vulgare)
        for tip, x, h, lean, bend in _stems(cell, 6, 0.55, 0.92, 3.0, np.array([70, 92, 46]), spread=0.10, lean_sd=0.10, bend_sd=0.05):
            for t in np.linspace(0.12, 0.82, 13):            # pinnate leaves: short feathery side strokes
                sx, sy = _at(x, h, lean, bend, t)
                for sg in (-1.0, 1.0):
                    L = rng.uniform(0.05, 0.085) * cw * (1.15 - 0.5 * t)
                    cell.leaf((sx, sy), math.pi / 2 - sg * rng.uniform(0.8, 1.3), L * 2.2, L * 0.75,
                              cell.col(np.array([62, 92, 44]) * rng.uniform(0.85, 1.15)), droop=0.5)
            for q in range(15):                              # the corymb: a flat plate of buttons
                bx = tip[0] + rng.normal(0, 0.050) * cw
                by = tip[1] + rng.uniform(-0.012, 0.022) * rh
                cell.stroke([_at(x, h, lean, bend, 0.9), (bx, by)], 1.3 * S, 1.0 * S, cell.col((84, 100, 50)))
                cell.dot(bx, by, rng.uniform(3.0, 4.2) * S, cell.col(np.array([190, 160, 40]) * rng.uniform(0.88, 1.08), 1.0))
    elif form == "yarrow":
        # thin stems, feathery leaves, white flat umbels (Achillea / Daucus)
        _fan(cell, 25, 0.05, 0.20, 3.6, 0.10, 0.4, 0.0, spread=0.8)
        for tip, x, h, lean, bend in _stems(cell, 5, 0.50, 0.90, 2.4, np.array([86, 104, 60]), spread=0.12, lean_sd=0.12, bend_sd=0.06):
            for t in np.linspace(0.10, 0.70, 9):
                sx, sy = _at(x, h, lean, bend, t)
                sg = 1.0 if rng.random() < 0.5 else -1.0
                cell.leaf((sx, sy), math.pi / 2 - sg * rng.uniform(0.7, 1.2), rng.uniform(0.07, 0.12) * cw * 1.6,
                          0.022 * cw, cell.col(np.array([78, 100, 58]) * rng.uniform(0.9, 1.1)), droop=0.6)
            rw = rng.uniform(0.07, 0.11) * cw
            for q in range(70):
                a = rng.uniform(0, 2 * math.pi)
                r = rw * math.sqrt(rng.random())
                cell.dot(tip[0] + math.cos(a) * r, tip[1] + math.sin(a) * r * 0.22 + 0.006 * rh, rng.uniform(1.8, 2.8) * S,
                         cell.col(np.array([214, 212, 196]) * rng.uniform(0.86, 1.04), 1.0))
            for q in range(7):
                a = rng.uniform(-1.0, 1.0)
                cell.stroke([_at(x, h, lean, bend, 0.88), (tip[0] + math.sin(a) * rw * 0.9, tip[1])], 1.2 * S, 1.0 * S,
                            cell.col((92, 108, 64)))
    elif form == "mugwort":
        # bushy, branching, dark grey-green with pale undersides and greyish panicle tips (Artemisia vulgaris)
        for tip, x, h, lean, bend in _stems(cell, 6, 0.60, 0.98, 3.2, np.array([78, 70, 52]), spread=0.09, lean_sd=0.12, bend_sd=0.07):
            for t in np.linspace(0.15, 0.95, 18):
                sx, sy = _at(x, h, lean, bend, t)
                sg = 1.0 if rng.random() < 0.5 else -1.0
                L = rng.uniform(0.07, 0.13) * cw * (1.25 - 0.7 * t) * 2.0
                c = np.array([56, 76, 48]) if rng.random() < 0.7 else np.array([118, 128, 104])
                end = cell.leaf((sx, sy), math.pi / 2 - sg * rng.uniform(0.45, 1.0), L, L * 0.28,
                                cell.col(c * rng.uniform(0.85, 1.15)), droop=0.35)
                if t > 0.55:
                    for q in range(5):
                        cell.dot(end[0] + rng.normal(0, 3.0 * S), end[1] + rng.normal(0, 3.0 * S), 1.7 * S,
                                 cell.col(np.array([128, 124, 96]) * rng.uniform(0.85, 1.1)))
    elif form == "chicory":
        # wiry, sparsely branched bare stems with a few sky-blue flowers (Cichorium intybus) over a low rosette
        for i in range(6):
            sg = -1.0 if i % 2 else 1.0
            cell.leaf((0.5 * cw, 0.0), math.pi / 2 - sg * rng.uniform(0.7, 1.35), rng.uniform(0.14, 0.24) * rh,
                      0.06 * cw, cell.col(np.array([64, 90, 46]) * rng.uniform(0.9, 1.1)), droop=0.8)
        for tip, x, h, lean, bend in _stems(cell, 4, 0.60, 0.97, 2.6, np.array([86, 96, 62]), spread=0.06, lean_sd=0.16, bend_sd=0.10):
            for t in rng.uniform(0.35, 0.92, 4):
                sx, sy = _at(x, h, lean, bend, t)
                sg = 1.0 if rng.random() < 0.5 else -1.0
                L = rng.uniform(0.10, 0.22) * rh
                ex, ey = sx + sg * L * 0.55, sy + L * 0.75
                ex = float(np.clip(ex, 0.06 * cw, 0.94 * cw))
                cell.stroke([(sx, sy), (ex, ey)], 2.0 * S, 1.3 * S, cell.col((86, 96, 62)))
                for fx, fy in ((ex, ey), (sx + (ex - sx) * 0.55, sy + (ey - sy) * 0.55)):
                    if rng.random() < 0.6:
                        for a in np.linspace(0, 2 * math.pi, 9)[:-1]:
                            cell.dot(fx + math.cos(a) * 3.2 * S, fy + math.sin(a) * 3.2 * S, 2.3 * S,
                                     cell.col(np.array([112, 142, 206]) * rng.uniform(0.9, 1.08), 1.0))


def _paint_short(form, cell):
    rng, cw, rh = cell.rng, cell.w, cell.h
    if form == "tuft":
        _fan(cell, 70, 0.08, 0.34, 4.5, 0.06, 0.45, 0.0)
        _fan(cell, 100, 0.25, 0.75, 3.8, 0.08, 0.10, 0.0)
        _fan(cell, 28, 0.55, 0.97, 3.0, 0.08, 0.03, 0.06)
    elif form == "tuft_dry":
        _fan(cell, 50, 0.08, 0.30, 4.3, 0.40, 0.40, 0.0, spread=1.2)
        _fan(cell, 60, 0.22, 0.66, 3.4, 0.60, 0.06, 0.0, lean0=-0.2, spread=1.2, tone=1.08)
    elif form == "rosette":
        # plantain / dock seedlings: broad oval leaves flat on the ground, a few slender spikes
        for i in range(11):
            sg = -1.0 if i % 2 else 1.0
            ang = math.pi / 2 - sg * rng.uniform(0.45, 1.45)
            cell.leaf((0.5 * cw + rng.normal(0, 0.03) * cw, 0.0), ang, rng.uniform(0.22, 0.40) * cw,
                      rng.uniform(0.10, 0.15) * cw, cell.col(np.array([62, 92, 44]) * rng.uniform(0.82, 1.15)),
                      droop=rng.uniform(0.4, 1.0), rib=cell.col((104, 124, 72)))
        for tip, x, h, lean, bend in _stems(cell, 4, 0.45, 0.85, 2.0, np.array([98, 104, 62]), spread=0.07, lean_sd=0.14):
            for t in np.linspace(0.72, 1.0, 9):
                sx, sy = _at(x, h, lean, bend, t)
                cell.dot(sx, sy, 2.6 * S, cell.col(np.array([104, 92, 60]) * rng.uniform(0.85, 1.15)))
    elif form == "clover":
        # a low mat of trefoil leaflets with a few white heads
        for q in range(260):
            x = (0.5 + float(np.clip(rng.normal(0, 0.17), -0.40, 0.40))) * cw
            y = abs(rng.normal(0, 0.16)) * rh * max(0.2, 1.0 - (abs(x / cw - 0.5) / 0.42) ** 2)
            r = rng.uniform(3.2, 5.6) * S
            cell.dot(x, y + r, r, cell.col(np.array([58, 96, 44]) * rng.uniform(0.75, 1.2)))
        for q in range(7):
            x = (0.5 + rng.uniform(-0.3, 0.3)) * cw
            y = rng.uniform(0.25, 0.48) * rh
            cell.stroke([(x, 0.05 * rh), (x + rng.normal(0, 2 * S), y)], 1.6 * S, 1.2 * S, cell.col((76, 100, 52)))
            for k in range(9):
                cell.dot(x + rng.normal(0, 3.0 * S), y + rng.normal(0, 3.0 * S), 2.2 * S,
                         cell.col(np.array([208, 200, 190]) * rng.uniform(0.85, 1.03), 1.0))
    elif form == "flat_dead":
        # last year's grass pressed flat: bleached blades lying to one side
        sg = 1.0 if rng.random() < 0.5 else -1.0
        for q in range(120):
            x = (0.5 + rng.uniform(-0.20, 0.20)) * cw
            L = rng.uniform(0.16, 0.36) * cw
            a = rng.uniform(0.10, 0.75)
            dx = float(np.clip(sg * math.cos(a) * L, 0.05 * cw - x, 0.95 * cw - x))
            pts = [(x + dx * t, math.sin(a) * L * t * (1.0 - 0.55 * t)) for t in np.linspace(0, 1, 6)]
            c = DRY * rng.uniform(0.85, 1.12) if rng.random() < 0.8 else GREENS[int(rng.integers(0, 4))]
            cell.stroke(pts, 3.4 * S, 1.0 * S, cell.col(c))
    elif form == "wisp":
        _fan(cell, 26, 0.20, 0.95, 3.0, 0.25, 0.10, 0.10, spread=1.3)
    elif form == "hawkbit":
        # toothed rosette, yellow flowers and a seed clock on thin scapes (Leontodon / Taraxacum)
        for i in range(9):
            sg = -1.0 if i % 2 else 1.0
            cell.leaf((0.5 * cw, 0.0), math.pi / 2 - sg * rng.uniform(0.6, 1.4), rng.uniform(0.20, 0.34) * cw,
                      0.06 * cw, cell.col(np.array([66, 96, 46]) * rng.uniform(0.85, 1.12)), droop=0.9)
        for n_, (tip, x, h, lean, bend) in enumerate(_stems(cell, 5, 0.45, 0.92, 1.8, np.array([98, 110, 66]), spread=0.08, lean_sd=0.18)):
            if n_ % 3 == 2:
                for a in np.linspace(0, 2 * math.pi, 15):
                    cell.dot(tip[0] + math.cos(a) * 5.0 * S, tip[1] + math.sin(a) * 5.0 * S, 1.7 * S, cell.col((206, 204, 194), 1.0))
            else:
                cell.dot(tip[0], tip[1], rng.uniform(5.0, 6.5) * S, cell.col(np.array([196, 164, 38]) * rng.uniform(0.9, 1.06), 1.0))
    elif form == "yarrow_low":
        _fan(cell, 35, 0.08, 0.34, 3.8, 0.10, 0.4, 0.0, spread=0.9)
        for tip, x, h, lean, bend in _stems(cell, 4, 0.55, 0.95, 2.2, np.array([86, 104, 60]), spread=0.12, lean_sd=0.14):
            rw = rng.uniform(0.08, 0.12) * cw
            for q in range(60):
                a = rng.uniform(0, 2 * math.pi)
                r = rw * math.sqrt(rng.random())
                cell.dot(tip[0] + math.cos(a) * r, tip[1] + math.sin(a) * r * 0.25, rng.uniform(1.8, 2.6) * S,
                         cell.col(np.array([212, 210, 194]) * rng.uniform(0.86, 1.04), 1.0))


def _paint_maize(im, rng):
    """A run of maize plants over the whole row canvas (wraps at the ends): a darker back layer, then the front."""
    W, H = im.size
    px_m = W / (N_MAIZE * MAIZE_CELL_M)                       # horizontal px per metre
    py_m = H / MAIZE_H_M
    d = ImageDraw.Draw(im)

    def poly(pts, c):
        for xo in (-W, 0, W):
            d.polygon([(x + xo, H - 2 - y) for x, y in pts], fill=c)

    def line(pts, w0, w1, c):
        for xo in (-W, 0, W):
            q = [(x + xo, H - 2 - y) for x, y in pts]
            for i in range(len(q) - 1):
                w = w0 + (w1 - w0) * i / max(len(q) - 2, 1)
                d.line([q[i], q[i + 1]], fill=c, width=max(1, int(round(w))))

    def col(c, k):
        return tuple(int(v) for v in np.clip(np.asarray(c, float) * k, 0, 255)) + (255,)

    def leaf(base, sg, length, width, c, rib):
        n = 12
        mid, a = [np.array(base, float)], math.radians(rng.uniform(48, 68))
        dr = rng.uniform(1.6, 2.5)
        for i in range(n):
            ai = a - dr * ((i + 1) / n) ** 1.7
            mid.append(mid[-1] + np.array([sg * math.cos(ai) * px_m, math.sin(ai) * py_m]) * length / n)
        left, right = [], []
        for i, p in enumerate(mid):
            t = i / n
            hw = 0.5 * width * (1.0 - t) ** 0.7 * (0.55 + 0.45 * min(t * 6, 1.0))
            j = min(i + 1, n)
            dv = mid[j] - mid[j - 1]
            dv = dv / max(float(np.hypot(*dv)), 1e-6)
            nr = np.array([-dv[1], dv[0]])
            left.append(p + nr * hw * py_m)
            right.append(p - nr * hw * py_m)
        poly([tuple(p) for p in left + right[::-1]], c)
        line([tuple(p) for p in mid], 1.6 * S, 0.8 * S, rib)

    def plant(x, h, k):
        green = np.array([70, 104, 46]) * rng.uniform(0.86, 1.14)
        lean = rng.normal(0, 0.02)
        stalk = [(x + lean * t * h * px_m, t * h * py_m) for t in np.linspace(0, 1, 9)]
        line(stalk, 0.030 * px_m, 0.012 * px_m, col(np.array([104, 124, 62]), k))
        nl = int(rng.integers(11, 15))
        for i in range(nl):
            t = 0.07 + 0.80 * i / (nl - 1) + rng.normal(0, 0.012)
            sg = 1.0 if (i + int(x)) % 2 else -1.0
            c = green
            if t < 0.26:                                     # the lowest leaves dry off in August
                c = np.array([150, 132, 78]) * rng.uniform(0.85, 1.1) if rng.random() < 0.75 else green * 0.9
            elif t < 0.40 and rng.random() < 0.3:
                c = np.array([112, 122, 60])
            L = rng.uniform(0.55, 0.85) * (0.75 + 0.5 * math.sin(math.pi * min(max(t, 0.0), 1.0)))
            leaf((x + lean * t * h * px_m, t * h * py_m), sg, L, rng.uniform(0.075, 0.10),
                 col(c, k * rng.uniform(0.9, 1.1)), col(np.array([128, 150, 84]), k))
        if rng.random() < 0.85:                              # the cob: husk and brown silk
            t = rng.uniform(0.38, 0.50)
            sg = 1.0 if rng.random() < 0.5 else -1.0
            bx, by = x + lean * t * h * px_m, t * h * py_m
            ex, ey = bx + sg * 0.07 * px_m, by + 0.23 * py_m
            mx_, my_ = bx + sg * 0.05 * px_m, by + 0.12 * py_m
            line([(bx, by), (mx_, my_), (ex, ey)], 0.030 * px_m, 0.018 * px_m, col(np.array([100, 128, 60]), k))
            line([(bx, by), (mx_, my_)], 0.044 * px_m, 0.040 * px_m, col(np.array([108, 134, 64]), k))
            for q in range(8):
                line([(ex, ey), (ex + sg * rng.uniform(0.0, 0.05) * px_m, ey + rng.uniform(0.0, 0.06) * py_m)],
                     1.4 * S, 1.0 * S, col(np.array([92, 60, 36]), k))
        top = stalk[-1]
        for q in range(int(rng.integers(8, 13))):            # the tassel
            a = rng.uniform(-0.9, 0.9)
            L = rng.uniform(0.14, 0.26)
            pts = [(top[0] + math.sin(a) * L * px_m * t, top[1] + math.cos(a) * L * py_m * t * (1.0 - 0.3 * t * abs(a)))
                   for t in np.linspace(0, 1, 5)]
            line(pts, 2.0 * S, 1.1 * S, col(np.array([176, 160, 104]) * rng.uniform(0.88, 1.08), k))

    row_m = N_MAIZE * MAIZE_CELL_M
    for k, n_pl, sp in ((0.62, 30, 0.0), (1.0, 27, 0.5)):
        xs = (np.arange(n_pl) + sp + rng.uniform(-0.28, 0.28, n_pl)) * row_m / n_pl
        for x in xs[np.argsort(rng.random(n_pl))]:
            plant(float(x) * px_m, rng.uniform(2.0, 2.33) * (0.96 if k < 1 else 1.0), k)


def texture(seed=334):
    W, H = TEX_W * S, TEX_H * S
    atlas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cw, rh = W // NT, H // 4
    for r, (forms, paint) in enumerate(((TALL_FORMS, _paint_tall), (SHORT_FORMS, _paint_short))):
        for k, form in enumerate(forms):
            cell = _Cell(cw, rh, np.random.default_rng(seed + 100 * r + k))
            paint(form, cell)
            cim, mg = cell.im, int(0.035 * cw)
            bb = cim.getbbox()
            if bb and (bb[0] < mg or bb[2] > cw - mg):           # a leaf reaches the cell side: fit the plant in
                sc = (cw - 2 * mg) / float(bb[2] - bb[0])
                crop = cim.crop((bb[0], bb[1], bb[2], rh))
                crop = crop.resize((cw - 2 * mg, max(1, int(round(crop.size[1] * sc)))), Image.LANCZOS)
                cim = Image.new("RGBA", (cw, rh), (0, 0, 0, 0))
                cim.paste(crop, (mg, rh - crop.size[1]))
            atlas.paste(cim, (k * cw, H // 2 + r * rh))          # tall row above the short row (image y down)
    mz = Image.new("RGBA", (W, H // 2), (0, 0, 0, 0))
    _paint_maize(mz, np.random.default_rng(seed + 900))
    atlas.paste(mz, (0, 0))
    im = atlas.resize((TEX_W, TEX_H), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32)
    m = a[..., 3] > 8
    # transparent texels take the colour of the nearest plant texel (no dark / light halo in the mips)
    idx = ndimage.distance_transform_edt(~m, return_distances=False, return_indices=True)
    a[..., :3] = a[idx[0], idx[1], :3]
    nz = ndimage.gaussian_filter(np.random.default_rng(seed + 1).random((TEX_H, TEX_W)), 0.8)
    a[..., :3] *= (0.90 + 0.20 * (nz - nz.min()) / max(float(nz.max() - nz.min()), 1e-6))[..., None]
    # the foot of every row is darker (inside the sward / the crop)
    y = np.arange(TEX_H)
    q = TEX_H // 4
    vrow = np.where(y < TEX_H // 2, 1.0 - (y + 0.5) / (TEX_H // 2), 1.0 - (((y - TEX_H // 2) % q) + 0.5) / q)
    foot = np.where(y < TEX_H // 2, 0.62 + 0.38 * np.clip(vrow / 0.45, 0, 1), 0.78 + 0.22 * np.clip(vrow / 0.5, 0, 1))
    a[..., :3] *= foot[:, None, None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
