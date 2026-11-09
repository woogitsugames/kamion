"""Procedural foliage-card and ground-detail textures (our own; no photos, no generators).

    uv run --project tools/worldgen tools/worldgen/streetscape/leaf_textures.py

Writes art-source/world/vegetation/{leaves_<species>.png, grass_tuft.png, bark_<species>.png} (RGBA, sRGB).
Each foliage card is a cluster of leaves / needle tufts drawn from primitives with per-leaf colour jitter
(sun-side lighter, inner darker) so the crown has depth when cards overlap. Deterministic seeds.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "art-source" / "world" / "vegetation"

# base leaf colours (sRGB), summer, muted (docs/06: przygaszone zielenie)
COL = {"birch": (86, 104, 46), "alder": (52, 68, 34), "maple": (70, 92, 40), "linden": (74, 94, 42),
       "pine": (44, 62, 38), "shrub": (66, 84, 40)}


def jitter(c, rng, k=0.18):
    f = 1 + rng.uniform(-k, k)
    h = rng.uniform(-8, 8)
    return tuple(int(np.clip(v * f + h * (i == 0) - h * 0.5 * (i == 2), 0, 255)) for i, v in enumerate(c))


def leaf_poly(kind, cx, cy, size, ang):
    """Outline of one leaf (in pixels)."""
    if kind == "maple":         # 5 lobes
        pts = []
        for k in range(40):
            t = 2 * math.pi * k / 40
            r = size * (0.55 + 0.45 * abs(math.cos(2.5 * t)) ** 0.6)
            pts.append((cx + r * math.cos(t + ang), cy + r * math.sin(t + ang)))
        return pts
    if kind == "linden":        # heart
        pts = []
        for k in range(30):
            t = 2 * math.pi * k / 30
            x = 16 * math.sin(t) ** 3
            y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
            x, y = x * size / 17, -y * size / 17
            pts.append((cx + x * math.cos(ang) - y * math.sin(ang), cy + x * math.sin(ang) + y * math.cos(ang)))
        return pts
    # ovate / triangular (birch, alder, shrub)
    ln, wd = (size * 1.3, size * 0.75) if kind != "alder" else (size * 1.1, size * 0.95)
    pts = []
    for k in range(24):
        t = 2 * math.pi * k / 24
        x = ln * math.cos(t)
        y = wd * math.sin(t) * (0.6 + 0.4 * math.cos(t)) if kind == "birch" else wd * math.sin(t)
        pts.append((cx + x * math.cos(ang) - y * math.sin(ang), cy + x * math.sin(ang) + y * math.cos(ang)))
    return pts


def foliage(species, seed, n=512):
    rng = np.random.default_rng(seed)
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    base = COL[species]
    cx, cy = n / 2, n / 2
    if species == "pine":
        # needle tufts: radiating short strokes around twig ends
        for _ in range(60):
            a = rng.uniform(0, 2 * math.pi)
            r = rng.uniform(0, n * 0.38) ** 1.0
            x, y = cx + r * math.cos(a), cy + r * math.sin(a)
            twig_end = (x, y)
            d.line([(cx + (x - cx) * 0.5, cy + (y - cy) * 0.5), twig_end], fill=(70, 50, 34, 255), width=3)
            for _ in range(28):
                b = rng.uniform(0, 2 * math.pi)
                L = rng.uniform(n * 0.03, n * 0.07)
                c = jitter(base, rng, 0.25)
                shade = 0.75 + 0.35 * (1 - r / (n * 0.4))
                c = tuple(int(min(255, v * shade)) for v in c)
                d.line([twig_end, (x + L * math.cos(b), y + L * math.sin(b))], fill=(*c, 255), width=2)
        return im
    # broadleaf: twigs + leaves
    for _ in range(14):
        a = rng.uniform(0, 2 * math.pi)
        d.line([(cx, cy), (cx + n * 0.4 * math.cos(a), cy + n * 0.4 * math.sin(a))], fill=(60, 50, 40, 255), width=3)
    count = {"birch": 170, "alder": 120, "maple": 70, "linden": 95, "shrub": 140}[species]
    size = {"birch": n * 0.035, "alder": n * 0.05, "maple": n * 0.07, "linden": n * 0.06, "shrub": n * 0.04}[species]
    for _ in range(count):
        r = n * 0.40 * math.sqrt(rng.uniform(0, 1))
        a = rng.uniform(0, 2 * math.pi)
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        c = jitter(base, rng)
        shade = 0.70 + 0.45 * (y < cy) * rng.uniform(0.3, 1.0)
        c = tuple(int(min(255, v * shade)) for v in c)
        d.polygon(leaf_poly(species, x, y, size * rng.uniform(0.75, 1.2), rng.uniform(0, 2 * math.pi)), fill=(*c, 255))
        # midrib
        d.line([(x, y), (x + size * 0.6 * math.cos(a), y + size * 0.6 * math.sin(a))], fill=(*tuple(int(v * 0.7) for v in c), 255))
    return im


def bark(species, seed, n=256):
    rng = np.random.default_rng(seed)
    if species == "birch":
        a = np.full((n, n, 3), (205, 202, 192), float)
        for _ in range(60):     # black lenticel dashes
            y = rng.integers(0, n)
            x0 = rng.integers(0, n)
            w = rng.integers(8, 40)
            h = rng.integers(2, 5)
            a[y:y + h, x0:x0 + w] = (35, 33, 30)
        a *= rng.uniform(0.85, 1.0, (n, 1, 1))
    else:
        base = {"pine": (112, 84, 66), "alder": (78, 72, 64), "maple": (92, 86, 76), "linden": (84, 78, 70),
                "shrub": (80, 70, 60), "twig": (66, 60, 54)}[species]
        noise = rng.normal(0, 1, (n, n // 8))
        noise = np.repeat(noise, 8, axis=1)
        from scipy import ndimage
        noise = ndimage.gaussian_filter(noise, (6, 1.5))
        a = np.array(base, float)[None, None, :] * (1 + 0.35 * noise[..., None])
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")


def grass_tuft(seed=3, n=256):
    """Card of grass blades + a few dry stems and a weed (kerb-line / verge detail)."""
    rng = np.random.default_rng(seed)
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for _ in range(90):
        x0 = rng.uniform(n * 0.1, n * 0.9)
        h = rng.uniform(n * 0.3, n * 0.95)
        bend = rng.uniform(-n * 0.15, n * 0.15)
        dry = rng.uniform() < 0.25
        c = (168, 156, 104) if dry else jitter((96, 122, 58), rng, 0.25)
        pts = [(x0 + bend * (t ** 2), n - 1 - h * t) for t in np.linspace(0, 1, 8)]
        d.line(pts, fill=(*c, 255), width=int(rng.integers(2, 4)))
    return im


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for k, sp in enumerate(["pine", "birch", "alder", "maple", "linden", "shrub"]):
        foliage(sp, 100 + k).save(OUT / f"leaves_{sp}.png", optimize=True)
        bark(sp, 200 + k).save(OUT / f"bark_{sp}.png", optimize=True)
    bark("twig", 210).save(OUT / "bark_twig.png", optimize=True)
    grass_tuft().save(OUT / "grass_tuft.png", optimize=True)
    print("written", sorted(p.name for p in OUT.glob("*.png")))


if __name__ == "__main__":
    sys.exit(main())
