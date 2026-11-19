"""Branchlet-spray foliage atlases for the broadleaf roadside trees (ADR 0308).

    uv run --project tools/worldgen tools/worldgen/streetscape/leaf_sprays.py [--out <dir>] [--only linden,maple]

Writes art-source/world/vegetation/leaves_<species>.png: a 2 x 2 atlas (1024 x 1024, RGBA sRGB) of four different
branchlets. One cell = one leafy twig system seen flat: the twig base sits at the bottom centre of the cell, the leaves
are drawn with the outline of the species (cordate linden, five-lobed Norway maple, rhombic birch, notched alder, deltoid
poplar, lanceolate willow), two-tone blades split at the midrib, darker leaves underneath and lighter ones on top.
The old cards (leaf_textures.foliage) were round pompons of flat discs around the card centre: every card read as a
ball, a crown of them as broccoli.

Our own procedural drawing (numpy + PIL): no photo, no scan, no third-party pixels. Leaf lengths are the usual blade
sizes of the species (WORKING_VALUE, not measured on a specimen): the card that carries a cell is CARD_M[species] wide.
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "art-source" / "world" / "vegetation"

CELL = 512                      # one branchlet
GRID = 2                        # atlas = GRID x GRID cells
SS = 2                          # supersampling of the drawing
SPECIES = ("linden", "maple", "birch", "alder", "poplar")    # willow: drawn on request (--only willow), not in the library yet
# base blade colour (sRGB, summer, muted - docs/06); linden / maple / birch / alder = leaf_textures.COL
COL = {"birch": (100, 116, 50), "alder": (52, 68, 34), "maple": (70, 92, 40), "linden": (74, 94, 42),
       "poplar": (84, 104, 50), "willow": (104, 118, 78)}
TWIG = {"birch": (58, 44, 40), "willow": (112, 104, 62)}
# blade length as a share of the cell, leaves per cell, style of the twig system
#   spray  = forking twig with alternate leaves (linden, maple, alder, poplar)
#   strand = long slender twigs fanning from the base with small leaves (birch, willow: the hanging twigs)
FORM = {"linden": (0.082, 250, "spray"), "maple": (0.128, 125, "spray"), "alder": (0.080, 230, "spray"),
        "poplar": (0.074, 250, "spray"), "birch": (0.052, 420, "strand"), "willow": (0.105, 330, "strand")}
# birch: cells 0-1 are upright sprays (the crown mass), cells 2-3 the hanging strands (make_trees `hang` cards);
# a crown of strand fans alone read as bursts of spikes (preview r1)
UPRIGHT_CELLS = {"birch": (2, 520)}             # species -> (cells drawn as sprays, their leaf count)
CARD_M = {"linden": 1.25, "maple": 1.35, "alder": 1.2, "poplar": 1.25, "birch": 1.15, "willow": 1.3}
SEED = {"linden": 3081, "maple": 3082, "birch": 3083, "alder": 3084, "poplar": 3085, "willow": 3086}


def blade(species):
    """Outline of one blade: (x, y) with the petiole at (0, 0), the tip at (1, 0); y = half-width side."""
    pts = []
    if species == "maple":                              # Acer platanoides: 5 pointed lobes, the middle one longest
        lobes = ((0.0, 1.0), (0.96, 0.86), (-0.96, 0.86), (1.92, 0.56), (-1.92, 0.56))
        for k in range(120):
            th = -math.pi + 2 * math.pi * k / 120
            r = 0.30
            for a, ln in lobes:
                d = abs((th - a + math.pi) % (2 * math.pi) - math.pi)
                r = max(r, ln * max(0.0, 1.0 - d / 0.50) ** 0.55)
                for side in (-0.26, 0.26):              # the two side teeth of every lobe
                    d2 = abs((th - a - side + math.pi) % (2 * math.pi) - math.pi)
                    r = max(r, ln * 0.72 * max(0.0, 1.0 - d2 / 0.20) ** 0.6)
            pts.append((0.42 + 0.58 * r * math.cos(th), 0.58 * r * math.sin(th)))
        return pts
    n = 64
    for k in range(n):
        t = 2 * math.pi * k / n
        c, s = math.cos(t), math.sin(t)
        if species == "linden":                         # Tilia cordata: heart with a drawn-out tip, fine teeth
            x = 0.5 + 0.5 * c
            w = 0.50 * (math.sin(math.pi * x ** 0.62)) ** 0.62 * (1.0 + 0.12 * (x < 0.3))
            if x > 0.86:
                w *= 0.55 + 0.45 * (1.0 - x) / 0.14     # acuminate tip
            y = w * (1 if s >= 0 else -1) * (1 + 0.05 * math.sin(26 * t))
            x = x - 0.07 * math.exp(-(abs(y) / 0.10) ** 2) * (x < 0.2)      # the notch at the petiole
        elif species == "birch":                        # Betula pendula: rhombic-triangular, long tip, double teeth
            x = 0.5 + 0.5 * c
            w = 0.36 * min(x / 0.30, 1.0) ** 0.8 * (1.0 - max(x - 0.30, 0.0) / 0.70) ** 0.95
            y = w * (1 if s >= 0 else -1) * (1 + 0.10 * math.sin(20 * t))
        elif species == "alder":                        # Alnus glutinosa: obovate, blunt notched apex
            x = 0.5 + 0.5 * c
            w = 0.42 * math.sin(math.pi * x ** 1.25) ** 0.7
            y = w * (1 if s >= 0 else -1) * (1 + 0.04 * math.sin(24 * t))
            x = x - 0.06 * math.exp(-(abs(y) / 0.12) ** 2) * (x > 0.8)
        elif species == "poplar":                       # Populus nigra / x canadensis: deltoid, widest near the base
            x = 0.5 + 0.5 * c
            w = 0.47 * min(x / 0.16, 1.0) ** 0.6 * (1.0 - max(x - 0.16, 0.0) / 0.84) ** 0.85
            y = w * (1 if s >= 0 else -1) * (1 + 0.04 * math.sin(22 * t))
        else:                                           # Salix alba: lanceolate, 1 : 7
            x = 0.5 + 0.5 * c
            y = 0.075 * math.sin(math.pi * x ** 0.85) ** 0.75 * (1 if s >= 0 else -1)
        pts.append((x, y))
    return pts


def _twigs(style, rng):
    """Twig system of one cell in cell coordinates (x right, y up, base at (0.5, 0.03)).
    Returns [(points [(x, y)], width share)] - the first is the main axis."""
    out = []

    def path(p0, ang, length, n, bend, wob):
        pts = [p0]
        a = ang
        for _ in range(n):
            a += bend / n + rng.uniform(-wob, wob)
            x, y = pts[-1]
            pts.append((x + math.cos(a) * length / n, y + math.sin(a) * length / n))
        return pts

    if style == "strand":
        k = int(rng.integers(5, 8))
        for i in range(k):
            a = math.pi / 2 + (i - (k - 1) / 2) * rng.uniform(0.17, 0.25) + rng.uniform(-0.05, 0.05)
            ln = rng.uniform(0.62, 0.88) * (1.0 - 0.25 * abs(i - (k - 1) / 2) / k)
            out.append((path((0.5 + rng.uniform(-0.02, 0.02), 0.03), a, ln, 8, rng.uniform(-0.22, 0.22), 0.05), 0.0045))
        return out
    lean = rng.uniform(-0.22, 0.22)
    main = path((0.5, 0.03), math.pi / 2 + lean, rng.uniform(0.74, 0.86), 8, -lean * 1.4 + rng.uniform(-0.2, 0.2), 0.06)
    out.append((main, 0.011))
    side = 1 if rng.random() < 0.5 else -1
    for i in range(int(rng.integers(5, 8))):
        t = 0.10 + 0.78 * (i + rng.uniform(0.1, 0.9)) / 7.0
        k = min(int(t * 8), 7)
        p = main[k]
        a0 = math.atan2(main[k + 1][1] - p[1], main[k + 1][0] - p[0])
        a = a0 + side * rng.uniform(0.55, 1.05)
        ln = rng.uniform(0.34, 0.58) * (1.0 - 0.40 * t)
        tw = path(p, a, ln, 5, -side * rng.uniform(0.0, 0.5), 0.07)
        out.append((tw, 0.006))
        if rng.random() < 0.7:
            j = int(rng.integers(1, 4))
            out.append((path(tw[j], a - side * rng.uniform(0.5, 0.9), ln * rng.uniform(0.4, 0.6), 3, 0.0, 0.08), 0.004))
        side = -side
    return out


def _fit(twigs, margin):
    """Scale / shift the twig system so every point keeps `margin` to the cell edge (leaves must not be cut)."""
    xs = [p[0] for tw, _ in twigs for p in tw]
    ys = [p[1] for tw, _ in twigs for p in tw]
    k = min(1.7, (0.5 - margin) / max(1e-6, max(0.5 - min(xs), max(xs) - 0.5)), (1.0 - margin - 0.03) / max(1e-6, max(ys) - 0.03))
    return [([(0.5 + (x - 0.5) * k, 0.03 + (y - 0.03) * k) for x, y in tw], w) for tw, w in twigs]


def spray(species, seed, n=CELL, upright=False):
    """One branchlet cell, RGBA uint8 (n x n x 4). Deterministic in (species, seed, upright)."""
    rng = np.random.default_rng(seed)
    length, count, style = FORM[species]
    if upright:
        style, count = "spray", UPRIGHT_CELLS[species][1]
    twigs = _fit(_twigs(style, rng), margin=length * 0.72 + 0.02)
    S = n * SS
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    def px(x, y):
        return (x * S, (1.0 - y) * S)

    tw_col = TWIG.get(species, (66, 54, 42))
    for tw, w in twigs:
        d.line([px(*p) for p in tw], fill=(*tw_col, 255), width=max(2, int(w * S)), joint="curve")
    # leaf sites: alternate along every twig (terminal leaf at its end), then fillers around random twig points
    sites = []
    for tw, _ in twigs:
        seg = [math.dist(tw[i], tw[i + 1]) for i in range(len(tw) - 1)]
        total = sum(seg)
        step = length * (0.50 if style == "spray" else 0.42)
        s, side = step * rng.uniform(0.6, 1.4), 1
        while s < total:
            acc, i = s, 0
            while i < len(seg) - 1 and acc > seg[i]:
                acc -= seg[i]
                i += 1
            f = acc / max(seg[i], 1e-9)
            x = tw[i][0] + (tw[i + 1][0] - tw[i][0]) * f
            y = tw[i][1] + (tw[i + 1][1] - tw[i][1]) * f
            a = math.atan2(tw[i + 1][1] - tw[i][1], tw[i + 1][0] - tw[i][0])
            spread = rng.uniform(0.55, 1.15) if style == "spray" else rng.uniform(0.35, 1.0)
            sites.append((x, y, a + side * spread))
            side = -side
            s += step * rng.uniform(0.7, 1.3)
        a = math.atan2(tw[-1][1] - tw[-2][1], tw[-1][0] - tw[-2][0])
        sites.append((tw[-1][0], tw[-1][1], a + rng.uniform(-0.3, 0.3)))
    guard = 0
    while len(sites) < count and guard < count * 4:
        guard += 1
        tw, _ = twigs[int(rng.integers(len(twigs)))]
        i = int(rng.integers(1, len(tw)))
        a = math.atan2(tw[i][1] - tw[i - 1][1], tw[i][0] - tw[i - 1][0]) + rng.uniform(-1.3, 1.3)
        r = rng.uniform(0.0, length * (1.3 if style == "spray" else 0.5))
        b = rng.uniform(0, 2 * math.pi)
        sites.append((tw[i][0] + r * math.cos(b), tw[i][1] + r * math.sin(b), a))
    sites = sites[:max(count, 1)]
    outline = blade(species)
    base = np.array(COL[species], float)
    order = rng.permutation(len(sites))
    m = length + 0.012
    for rank, si in enumerate(order):
        x, y, a = sites[si]
        ln = length * rng.uniform(0.72, 1.12)
        # the petiole end stays on the twig; the blade must stay inside the cell
        tx, ty = x + ln * math.cos(a), y + ln * math.sin(a)
        if not (m * 0.25 < tx < 1 - m * 0.25 and m * 0.25 < ty < 1 - m * 0.25 and 0.012 < x < 0.988 and 0.012 < y < 0.988):
            continue
        depth = rank / max(len(order) - 1, 1)                 # drawn later = nearer = lighter
        shade = (0.56 + 0.52 * depth) * (0.90 + 0.18 * y) * rng.uniform(0.90, 1.10)
        hue = rng.uniform(-7, 9)
        c = np.clip(base * shade + np.array([hue, hue * 0.4, -hue * 0.6]), 0, 255)
        fold = rng.uniform(0.84, 0.95)
        ca, sa = math.cos(a), math.sin(a)
        wk = rng.uniform(0.85, 1.12)                            # blades seen slightly edge-on are narrower
        if rng.random() < 0.22:
            wk *= rng.uniform(0.35, 0.7)
        up, lo = [], []
        for bx, by in outline:
            q = px(x + (bx * ca - by * wk * sa) * ln, y + (bx * sa + by * wk * ca) * ln)
            (up if by >= 0 else lo).append(q)
        p0, p1 = px(x, y), px(tx, ty)
        if len(up) > 2:                                         # each half closes along the midrib
            d.polygon(up, fill=(*[int(v) for v in c], 255))
        if len(lo) > 2:
            d.polygon([p0] + lo + [p1], fill=(*[int(v) for v in np.clip(c * fold, 0, 255)], 255))
        d.line([p0, p1], fill=(*[int(v) for v in np.clip(c * 1.10 + 3, 0, 255)], 255), width=max(1, SS - 1 + (species == "maple")))
    im = im.resize((n, n), Image.LANCZOS)
    arr = np.asarray(im).copy()
    # colour under the transparent texels = mean blade colour (no black fringe in the mips of the alpha-tested card)
    al = arr[..., 3:4].astype(float) / 255.0
    mean = (arr[..., :3] * al).sum(axis=(0, 1)) / max(al.sum(), 1.0)
    rgb = np.where(al > 0.02, arr[..., :3], mean)       # Pillow resizes RGBA premultiplied: colours stay true
    arr[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    return arr


def atlas(species, seed=None, n=CELL):
    seed = SEED[species] if seed is None else seed
    out = np.zeros((n * GRID, n * GRID, 4), np.uint8)
    for i in range(GRID * GRID):
        r, c = divmod(i, GRID)
        out[r * n:(r + 1) * n, c * n:(c + 1) * n] = spray(species, seed * 31 + i * 7919, n,
                                                           upright=i < UPRIGHT_CELLS.get(species, (0, 0))[0])
    return out


def cell_uv(cell, mirror=False):
    """UVs (bottom-left, bottom-right, top-right, top-left) of atlas cell 0..3; v = 0 is the twig base."""
    r, c = divmod(int(cell) % (GRID * GRID), GRID)
    u0, u1 = c / GRID, (c + 1) / GRID
    v1, v0 = 1.0 - r / GRID, 1.0 - (r + 1) / GRID
    if mirror:
        u0, u1 = u1, u0
    return ((u0, v0), (u1, v0), (u1, v1), (u0, v1))


def coverage(arr):
    return float((arr[..., 3] > 127).mean())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    for sp in (a.only.split(",") if a.only else SPECIES):
        arr = atlas(sp)
        Image.fromarray(arr, "RGBA").save(a.out / f"leaves_{sp}.png", optimize=True)
        print(f"leaves_{sp}.png coverage {coverage(arr):.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
