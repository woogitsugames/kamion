"""Clipped-hedge foliage textures (our own, drawn from primitives; no photos, no image generators).

Two alpha-clip textures per hedge species, written by streetscape.export to art-source/world/textures/:

  hedge_shell_<sp>.png   tileable leaf layer for the alpha shell 5 cm outside the opaque hedge core
                         (streetscape.plantings). Tile HEDGE_TILE_M x HEDGE_TILE_M, leaves at true size
                         (berberis 12-28 mm, privet 30-50 mm, hornbeam 50-80 mm, thuja scale sprays 40-90 mm),
                         drawn in clumps around twig tips, deeper leaves darker; coverage ~0.55-0.65 so the dark
                         core shows through as depth and the silhouette is ragged where the shell is seen edge-on.
  hedge_sprig_<sp>.png   2 x 2 atlas of loose shoots (cell 256 x 256 px = SPRIG_CELL_M) that stick out of the
                         clipped top / ends: dense at the cell bottom (it sits inside the shell), sparse at the top.

Colours are sRGB leaf albedo (material colour white): WORKING_VALUE, read off the CC0 Bieżeństwa photo
(20201102_152339, overcast: berberis lit ~ (110, 45, 40), shade ~ (70, 30, 30)) and general knowledge of the species
(muted summer greens, docs/06). Transparent texels carry the blurred leaf colour (no black fringe in the mips; the
importer keeps alpha coverage per mip). Deterministic seeds.
"""

from __future__ import annotations

import functools
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HEDGE_TILE_M = 0.6          # m per shell tile
SPRIG_CELL_M = 0.30         # m per sprig atlas cell (square)

# leaf colour (sRGB), leaf length m, leaf width / length, drawing kind
SPECIES = {
    # Berberis thunbergii 'Atropurpurea': obovate 1-3 cm, purple-red to brown-red, a few scarlet ones
    # tip: young shoot leaves above the last cut are lighter and more copper (photo: orange-brown highlights on the top
    # and the ends; ADR 0060, review r7 N-4), share of the outer leaves; deep: darkening of the inner leaves
    "berberis": dict(col=(96, 44, 36), alt=[((114, 48, 32), 0.10), ((72, 36, 34), 0.25)], leaf=(0.012, 0.028),
                     ratio=0.55, kind="obovate", clumps=340, per_clump=(7, 14), cover=0.62,
                     tip=((150, 80, 50), 0.4), deep=0.35),
    # Ligustrum vulgare: lanceolate 3-5 cm, dark glossy green, opposite pairs
    "privet": dict(col=(54, 72, 36), alt=[((70, 88, 42), 0.2), ((40, 56, 30), 0.25)], leaf=(0.028, 0.05),
                   ratio=0.38, kind="lanceolate", clumps=150, per_clump=(6, 10), cover=0.62),
    # Carpinus betulus: ovate 5-8 cm, serrated, mid green (summer)
    "hornbeam": dict(col=(66, 86, 40), alt=[((84, 100, 46), 0.2), ((50, 66, 32), 0.25)], leaf=(0.045, 0.08),
                     ratio=0.55, kind="serrate", clumps=70, per_clump=(5, 8), cover=0.60),
    # Thuja occidentalis 'Smaragd' / 'Brabant': flat scale-leaf sprays, dark green with yellowish tips
    "thuja": dict(col=(46, 70, 36), alt=[((70, 88, 40), 0.18), ((34, 50, 28), 0.3)], leaf=(0.04, 0.09),
                  ratio=0.5, kind="spray", clumps=120, per_clump=(3, 5), cover=0.66),
}


def _jit(c, rng, k=0.16):
    f = 1 + rng.uniform(-k, k)
    return np.clip(np.array(c, float) * f, 0, 255)


def _leaf(kind, x, y, L, ratio, ang):
    """leaf outline (pixels)"""
    W = L * ratio
    pts = []
    m = 18 if kind != "serrate" else 28
    for k in range(m):
        t = 2 * math.pi * k / m
        cx = 0.5 * L * math.cos(t)
        if kind == "obovate":          # widest beyond the middle
            cy = 0.5 * W * math.sin(t) * (0.75 + 0.35 * math.cos(t))
        elif kind == "lanceolate":
            cy = 0.5 * W * math.sin(t) * (0.9 - 0.25 * math.cos(t))
        else:                          # ovate, serrate margin
            cy = 0.5 * W * math.sin(t) * (0.85 - 0.2 * math.cos(t))
            if kind == "serrate" and k % 2:
                cx *= 1.06
                cy *= 1.08
        cx += 0.5 * L                  # petiole end at the origin
        pts.append((x + cx * math.cos(ang) - cy * math.sin(ang), y + cx * math.sin(ang) + cy * math.cos(ang)))
    return pts


def _spray(d, rng, x, y, L, ang, col):
    """thuja: a flat fan of scale-leaf branchlets (overlapping small lozenges along forking lines)"""
    for b in range(int(rng.integers(4, 7))):
        a = ang + rng.uniform(-0.7, 0.7)
        ln = L * rng.uniform(0.5, 1.0)
        for s in np.linspace(0, 1, 9):
            px, py = x + ln * s * math.cos(a), y + ln * s * math.sin(a)
            r = L * 0.075 * (1.15 - 0.6 * s)
            c = tuple(int(v) for v in _jit(col, rng, 0.08) * (0.9 + 0.25 * s))
            d.ellipse([px - r * 1.6, py - r, px + r * 1.6, py + r], fill=(*c, 255))


def _fill_rgb(im, base):
    """transparent texels get the blurred leaf colour (mip-safe; no dark fringe)"""
    a = np.asarray(im, float)
    m = a[..., 3:4] / 255.0
    rgb = a[..., :3]
    blur = np.asarray(Image.fromarray((rgb * m).astype(np.uint8)).filter(ImageFilter.GaussianBlur(10)), float)
    w = np.asarray(Image.fromarray((m[..., 0] * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(10)), float)[..., None] / 255.0
    fill = np.where(w > 0.02, blur / np.maximum(w, 1e-3), np.array(base, float) * 0.6)
    out = np.where(m > 0.5, rgb, np.clip(fill * 0.7, 0, 255))
    return Image.fromarray(np.dstack([out, a[..., 3]]).astype(np.uint8), "RGBA")


def shell(sp, n=512, seed=0):
    """tileable leaf layer, HEDGE_TILE_M square (wrap-around drawing on a 3x canvas, centre crop)"""
    S = SPECIES[sp]
    rng = np.random.default_rng(1000 + seed + sum(map(ord, sp)))
    px_m = n / HEDGE_TILE_M
    big = Image.new("RGBA", (3 * n, 3 * n), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    leaves = []
    # clump centres: jittered grid (no clustering artefacts at the tile seam), depth per clump
    for _ in range(S["clumps"]):
        cx, cy = rng.uniform(0, n), rng.uniform(0, n)
        depth = rng.uniform(0, 1)                      # 0 = deep inside the hedge, 1 = cut surface
        for _ in range(int(rng.integers(*S["per_clump"]))):
            L = rng.uniform(*S["leaf"]) * px_m
            r = rng.uniform(0.2, 1.0) * L * 1.2
            a = rng.uniform(0, 2 * math.pi)
            leaves.append((depth + rng.uniform(-0.1, 0.1), cx + r * math.cos(a), cy + r * math.sin(a), L,
                           a + rng.uniform(-0.6, 0.6)))
    leaves.sort(key=lambda t: t[0])                    # back to front
    for depth, x, y, L, ang in leaves:
        c = S["col"]
        u = rng.uniform()
        acc = 0.0
        for alt, p in S["alt"]:
            acc += p
            if u < acc:
                c = alt
                break
        tip = S.get("tip")
        if tip and depth > 0.72 and rng.uniform() < tip[1]:
            c = tip[0]
        dk = S.get("deep", 0.5)
        c = _jit(c, rng) * ((1.0 - dk) + dk * np.clip(depth, 0, 1) ** 1.3)   # deeper leaves darker
        col = tuple(int(v) for v in np.clip(c, 0, 255))
        for ox in (0, n, 2 * n):
            for oy in (0, n, 2 * n):
                if S["kind"] == "spray":
                    _spray(d, rng, x + ox, y + oy, L, ang, col)
                else:
                    d.polygon(_leaf(S["kind"], x + ox, y + oy, L, S["ratio"], ang), fill=(*col, 255))
                    e = tuple(int(v * 0.72) for v in col)
                    d.line([(x + ox, y + oy), (x + ox + 0.8 * L * math.cos(ang), y + oy + 0.8 * L * math.sin(ang))],
                           fill=(*e, 255), width=1)
    im = big.crop((n, n, 2 * n, 2 * n))
    return _fill_rgb(im, S["col"])


def sprigs(sp, n=256, seed=0):
    """2 x 2 atlas of loose shoots; each cell: a twig rising from the bottom centre with leaves, sparse at the tip"""
    S = SPECIES[sp]
    rng = np.random.default_rng(2000 + seed + sum(map(ord, sp)))
    px_m = n / SPRIG_CELL_M
    im = Image.new("RGBA", (2 * n, 2 * n), (0, 0, 0, 0))
    for cell in range(4):
        x0, y0 = 0, 0
        ci = Image.new("RGBA", (n, n), (0, 0, 0, 0))   # own canvas per cell: nothing spills into a neighbour
        d = ImageDraw.Draw(ci)
        Lmax = S["leaf"][1] * px_m
        lo, hi = 0.08 * n + 0.5 * Lmax, 0.92 * n - 0.5 * Lmax
        items = []
        # leafy tuft under a ragged top outline (3-6 shoot peaks): dense enough to read at 5-30 m, where single
        # twigs vanish in the mips (iteration 1: the shoots were invisible in the WorldC frames)
        xs = np.arange(n)
        top = np.full(n, float(n))
        for _ in range(int(rng.integers(3, 7))):
            cx, hgt, wd = n * rng.uniform(0.2, 0.8), n * rng.uniform(0.35, 0.85), n * rng.uniform(0.07, 0.16)
            top = np.minimum(top, n - hgt * np.exp(-0.5 * ((xs - cx) / wd) ** 2) - n * 0.12)
        top = np.clip(top, 0.08 * n + 0.5 * Lmax, n)
        for _ in range(int(220 * (0.028 / S["leaf"][1]) ** 1.2) + 20):
            px = rng.uniform(lo, hi)
            yt = top[int(px)]
            if yt >= n - 4:
                continue
            py = yt + (n - yt) * rng.uniform(0, 1) ** 1.6
            lit = 1.0 - 0.6 * (py - yt) / max(n - yt, 1)
            items.append(("leaf", (px, py), (rng.uniform(*S["leaf"]) * px_m, -math.pi / 2 + rng.uniform(-1.4, 1.4), lit)))
        items.sort(key=lambda t: -t[1][1] if t[0] == "leaf" else 0)       # lower (deeper) leaves first
        for _ in range(int(rng.integers(1, 3))):
            bx = x0 + n * rng.uniform(0.32, 0.68)
            a = -math.pi / 2 + rng.uniform(-0.6, 0.6)
            ln = (n * 0.9 - Lmax) * rng.uniform(0.4, 0.95)
            tip = (bx + ln * math.cos(a), y0 + n - 2 + ln * math.sin(a))
            items.append(("twig", (bx, y0 + n - 2), tip))
            for s in np.linspace(0.05, 1.0, int(rng.integers(14, 24))):
                if rng.uniform() < 0.2 * s:
                    continue
                px, py = bx + ln * s * math.cos(a), y0 + n - 2 + ln * s * math.sin(a)
                if not (lo <= px <= hi and py >= 0.06 * n + 0.5 * Lmax):
                    continue
                L = rng.uniform(*S["leaf"]) * px_m * (1.1 - 0.35 * s)
                side = 1 if rng.uniform() < 0.5 else -1
                items.append(("leaf", (px, py), (L, a + side * rng.uniform(0.4, 1.3), 1.0 - 0.35 * s)))
        # dense base (sits inside the shell; the straight bottom edge of the cell is buried)
        for _ in range(int(30 * (0.028 / S["leaf"][1]) ** 0.7) + 6):
            px, py = n * rng.uniform(0.2, 0.8), n - rng.uniform(0, n * 0.25)
            L = rng.uniform(*S["leaf"]) * px_m
            items.insert(0, ("leaf", (px, py), (L, rng.uniform(0, 2 * math.pi), 0.6)))
        for kind, p, q in items:
            if kind == "twig":
                d.line([p, q], fill=(62, 44, 36, 255), width=1)
                continue
            L, ang, lit = q
            c = S["col"]
            if rng.uniform() < S["alt"][0][1]:
                c = S["alt"][0][0]
            if S.get("tip") and lit > 0.7 and rng.uniform() < S["tip"][1] * 1.4:
                c = S["tip"][0]
            col = tuple(int(v) for v in np.clip(_jit(c, rng) * (0.5 + 0.4 * lit), 0, 255))
            if S["kind"] == "spray":
                _spray(d, rng, p[0], p[1], L, ang, col)
            else:
                d.polygon(_leaf(S["kind"], p[0], p[1], L, S["ratio"], ang), fill=(*col, 255))
        a = np.asarray(ci).copy()
        a[:3, :, 3] = 0                 # top / side frame transparent (no straight clip edge)
        a[:, :3, 3] = 0
        a[:, -3:, 3] = 0
        im.paste(Image.fromarray(a, "RGBA"), ((cell % 2) * n, (cell // 2) * n))
    return _fill_rgb(im, S["col"])


def coverage(im):
    return float((np.asarray(im)[..., 3] > 127).mean())


@functools.lru_cache(maxsize=1)
def textures():
    """{'hedge_shell_<sp>': Image, 'hedge_sprig_<sp>': Image} for every species (cached: export calls it twice)"""
    out = {}
    for sp in SPECIES:
        out[f"hedge_shell_{sp}"] = shell(sp)
        out[f"hedge_sprig_{sp}"] = sprigs(sp)
    return out


if __name__ == "__main__":       # preview: uv run --project tools/worldgen python -m streetscape.hedge_textures <dir>
    import sys
    from pathlib import Path
    od = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    od.mkdir(parents=True, exist_ok=True)
    for k, im in textures().items():
        im.save(od / f"{k}.png")
        print(k, "coverage", round(coverage(im), 3))
