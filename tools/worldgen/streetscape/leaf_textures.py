"""Our foliage/ground cards, with optional hash-pinned CC0 pine bark and needles.

    uv run --project tools/worldgen tools/worldgen/streetscape/leaf_textures.py

Writes art-source/world/vegetation/{leaves_<species>.png, grass_tuft.png, bark_<species>.png} (RGBA, sRGB).
Broadleaf cards are clusters drawn from primitives with per-leaf colour jitter
(sun-side lighter, inner darker). Pine uses a clean CC0 twig crop when available,
with a deterministic procedural fallback. Source hashes / crop: pine_needles_manifest.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "art-source" / "world" / "vegetation"

# base leaf colours (sRGB), summer, muted (docs/06: przygaszone zielenie)
# ADR0088: the old pine covered-texel median linear luminance was .0353.
# Muted needle / leaf reflectance starting values, WORKING_VALUE; final acceptance
# uses lit crown p10/p50 against the same photographic metric, not these swatches.
COL = {"birch": (100, 116, 50), "alder": (52, 68, 34), "maple": (70, 92, 40), "linden": (74, 94, 42),
       "pine": (66, 85, 52), "shrub": (66, 84, 40),
       # ADR 0187: Norway spruce (Picea abies) needles are the darkest green of a Podlasie stand, slightly blue.
       # WORKING_VALUE (read against the pine card; same muted family as plot_kit._spruce_card after ADR 0170).
       "spruce": (36, 56, 38)}


def spruce_spray(seed, n=512):
    """ADR 0187: one Norway spruce bough seen from above: axis from the bottom centre (v = 0, at the stem) to the
    tip (v = 1), forward-pointing side twigs that get shorter towards the tip, short dense needles on both sides
    of every twig. make_trees.py uses the whole card as the flat bough and its right half (axis on the edge) as the
    hanging curtain of twigs under the bough."""
    rng = np.random.default_rng(seed)
    S = 2                                    # supersampling
    N = n * S
    im = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    base = COL["spruce"]
    cx = N / 2

    def needles(p, q, length, shade):
        k = max(2, int(math.hypot(q[0] - p[0], q[1] - p[1]) / (N * 0.006)))
        ang = math.atan2(q[1] - p[1], q[0] - p[0])
        for i in range(k):
            t = (i + rng.uniform(0, 1)) / k
            x, y = p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t
            for sgn in (-1, 1):
                b = ang + sgn * rng.uniform(0.75, 1.25)
                L = length * rng.uniform(0.7, 1.15)
                c = jitter(base, rng, 0.22)
                c = tuple(int(min(255, v * shade * rng.uniform(0.85, 1.15))) for v in c)
                d.line([(x, y), (x + L * math.cos(b), y + L * math.sin(b))], fill=(*c, 255), width=S + 1)

    y0, y1 = N * 0.985, N * 0.03             # stem end, tip (image y grows downwards)
    steps = 34
    for i in range(steps):
        t = (i + 0.5) / steps                # 0 at the stem, 1 at the tip
        y = y0 + (y1 - y0) * t
        env = N * 0.47 * (0.35 + 0.65 * min(1.0, t / 0.22)) * (1 - t) ** 0.62      # half width of the bough
        for sgn in (-1, 1):
            a = -math.pi / 2 + sgn * rng.uniform(0.78, 1.05)                        # forward-pointing twig
            L = env / max(abs(math.cos(a)), 0.3) * rng.uniform(0.82, 1.0)
            q = (cx + L * math.cos(a), y + L * math.sin(a))
            d.line([(cx, y), q], fill=(58, 44, 30, 255), width=S + 1)
            shade = 0.72 + 0.4 * min(1.0, L / (N * 0.3))                           # lighter at the outer ends
            needles((cx, y), q, N * 0.022, shade)
            for j in range(int(L / (N * 0.07))):                                    # second-order twigs
                u = (j + rng.uniform(0.3, 1.0)) / max(1, int(L / (N * 0.07)))
                bx, by = cx + (q[0] - cx) * u, y + (q[1] - y) * u
                a2 = a + rng.choice((-1, 1)) * rng.uniform(0.5, 0.9)
                L2 = L * (1 - u) * rng.uniform(0.35, 0.6) + N * 0.02
                q2 = (bx + L2 * math.cos(a2), by + L2 * math.sin(a2))
                needles((bx, by), q2, N * 0.02, shade * 1.05)
    d.line([(cx, y0), (cx, y1)], fill=(52, 40, 28, 255), width=2 * S + 1)
    needles((cx, y0 - N * 0.02), (cx, y1), N * 0.024, 1.0)
    im = im.resize((n, n), Image.Resampling.LANCZOS)
    a = np.array(im)
    # colour under the alpha = nearest covered texel (alpha-to-coverage mips, no dark fringe)
    from scipy import ndimage
    empty = a[..., 3] < 8
    idx = ndimage.distance_transform_edt(empty, return_distances=False, return_indices=True)
    a[..., :3][empty] = a[idx[0][empty], idx[1][empty], :3]
    return Image.fromarray(a)


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
    if species == "spruce":
        return spruce_spray(seed, n)
    if species == "pine":
        if __package__:
            from .pine_needles import needle_card
        else:
            from pine_needles import needle_card
        scan = needle_card(n)
        if scan is not None:
            return scan
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
        # v3.1: albedo lowered from (205, 202, 192): a sunlit white trunk read as a bare white pole in the
        # dark stand (REVIEW r2 #7); weathered birch bark is a dull grey-white with many dark lenticels
        a = np.full((n, n, 3), (176, 173, 164), float)
        for _ in range(95):     # black lenticel dashes
            y = rng.integers(0, n)
            x0 = rng.integers(0, n)
            w = rng.integers(8, 40)
            h = rng.integers(2, 5)
            a[y:y + h, x0:x0 + w] = (35, 33, 30)
        a *= rng.uniform(0.85, 1.0, (n, 1, 1))
    else:
        base = {"pine": (104, 86, 74), "alder": (78, 72, 64), "maple": (92, 86, 76), "linden": (84, 78, 70),
                "shrub": (80, 70, 60), "twig": (66, 60, 54)}[species]
        noise = rng.normal(0, 1, (n, n // 8))
        noise = np.repeat(noise, 8, axis=1)
        from scipy import ndimage
        noise = ndimage.gaussian_filter(noise, (6, 1.5))
        a = np.array(base, float)[None, None, :] * (1 + 0.35 * noise[..., None])
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")


def pine_scan(lower=False, n=512, root=REPO):
    """Hash-pinned Poly Haven CC0 pine bark; never the rejected Fab mulch atlas."""
    manifest = root / "art-source/world/cc0/cc0_manifest.json"
    try:
        asset = next(a for a in json.loads(manifest.read_text(encoding="utf-8"))["assets"] if a["id"] == "pine_bark")
        source = next(f for f in asset["files"] if f["map"] == "Diffuse")
        path = root / "art-source/world/cc0/_raw/pine_bark" / source["url"].rsplit("/", 1)[1]
        if hashlib.sha256(path.read_bytes()).hexdigest() != source["sha256"]:
            raise ValueError("CC0 pine bark SHA mismatch")
        with Image.open(path) as image:
            a = np.asarray(image.convert("RGB").resize((n, n), Image.Resampling.LANCZOS), dtype=np.float32) / 255
        linear = np.where(a <= .04045, a / 12.92, ((a + .055) / 1.055) ** 2.4)
        # Same muted bark palette as the public generator, with warmer upper bole.
        rgb = np.array((94, 84, 72) if lower else (124, 94, 69), np.float32) / 255
        target = np.where(rgb <= .04045, rgb / 12.92, ((rgb + .055) / 1.055) ** 2.4)
        linear *= target / np.maximum(linear.mean((0, 1)), .001)
        linear = np.clip(linear, 0, 1)
        out = np.where(linear <= .0031308, linear * 12.92, 1.055 * linear ** (1 / 2.4) - .055)
        return Image.fromarray(np.round(out * 255).astype(np.uint8)).convert("RGBA")
    except (OSError, KeyError, StopIteration, ValueError) as error:
        logging.warning("CC0 pine bark unavailable (%s); procedural bark retained", error)
        return bark("pine" if not lower else "alder", 200, n)


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


SEED_ONLY = {"spruce": 106}     # species added after the first six keep the old files byte-identical


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--only", default="", help="write only leaves_<species>.png for these species (ADR 0187: spruce)")
    args = parser.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    if args.only:
        for sp in args.only.split(","):
            foliage(sp, SEED_ONLY[sp]).save(out / f"leaves_{sp}.png", optimize=True)
        print("written", [f"leaves_{sp}.png" for sp in args.only.split(",")])
        return 0
    for k, sp in enumerate(["pine", "birch", "alder", "maple", "linden", "shrub"]):
        foliage(sp, 100 + k).save(out / f"leaves_{sp}.png", optimize=True)
        (pine_scan() if sp == "pine" else bark(sp, 200 + k)).save(out / f"bark_{sp}.png", optimize=True)
    pine_scan(lower=True).save(out / "bark_pine_lower.png", optimize=True)
    bark("twig", 210).save(out / "bark_twig.png", optimize=True)
    grass_tuft().save(out / "grass_tuft.png", optimize=True)
    print("written", sorted(p.name for p in out.glob("*.png")))


if __name__ == "__main__":
    sys.exit(main())
