"""Remove the lens-flare ghost from the photographic Clear cloud map (render-artifacts-s24, ADR 0332 addendum 2).

Why: critic s24 wave 11 pkt 10 - "jasne okragle plamy w chmurach" (knyszyn-w tykocka-dw671-out x~740 / y~165, tykocin
route-s0160 x~1440 / y~150). Not the shader: the source HDRI (CC0 Poly Haven kloofendal_48d_partly_cloudy_puresky, ADR
0108) holds a camera lens ghost of the sun - a ~3.5 deg bright disc inside the small cumulus 18 deg east of and 23 deg
below the photographed sun. The chromatic matte read it as opaque (R 1.0 where the cloud body around it is 0.4-0.6) and
its luminance G ~0.95 where the cloud is ~0.5, so Kamion/Sky draws a white round blot in a grey cloud. WorldAtmosphere
rotates the map so the photographed sun sits on the game sun, so the blot always hangs at the same place relative to the
sun (measured: tykocka camera heading 230 deg, sun azimuth 200 deg -> predicted screen x 762 / y ~140, seen at 740 / 165).

What: inside a disc of GHOST_DEG around the ghost centre (located automatically as the G peak within SEARCH_DEG of the
nominal direction) R and G are replaced by a harmonic (Laplace) fill from the ring around it plus the high-frequency
cloud texture of a donor patch of the same cloud (offset DONOR_OFFSET texels), feathered over FEATHER_DEG. Everything
outside the disc + feather is unchanged byte for byte. Deterministic; refuses any input but the glass-sky-s24 map.

Run:  uv run --no-project --with numpy --with pillow python tools/rendering/clear_clouds_ghost_repair.py [--src <png>] [--out <png>] [--preview <jpg>]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os

import numpy as np
from PIL import Image

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SKY = os.path.join(REPO, "game", "Assets", "_Project", "Rendering", "Resources", "Sky")
TEX = os.path.join(SKY, "T_ClearClouds.png")
SRC_SHA = "10f81b4d4c8d999ba399f975bddd570fba6f9ba3b484e2d979252d2fe847d916"   # glass-sky-s24 texture_sha256
NOMINAL = (23.6, 51.7)      # ghost centre (lat, lon deg) read off the map (texel 755 / 2635 of 2048 x 4096)
SEARCH_DEG = 2.0            # the centre is the G peak within this distance of NOMINAL
GHOST_DEG = 2.3             # replaced disc radius (the ghost core + its bright rim is ~1.8 deg; WORKING_VALUE)
FEATHER_DEG = 0.8           # blend back to the untouched map
DONOR_OFFSET = (0, -70)     # texel offset of the donor patch (same cumulus, west part: no ghost light)
FILL_ITER = 1500


def angle_deg(h, w, lat0, lon0):
    lat = np.pi * (0.5 - (np.arange(h, dtype=np.float64) + 0.5) / h)
    lon = 2 * np.pi * ((np.arange(w, dtype=np.float64) + 0.5) / w - 0.5)
    la, lo = math.radians(lat0), math.radians(lon0)
    d = np.sin(lat)[:, None] * math.sin(la) + np.cos(lat)[:, None] * math.cos(la) * np.cos(lon[None, :] - lo)
    return np.degrees(np.arccos(np.clip(d, -1.0, 1.0)))


def texel(h, w, lat, lon):
    return int((0.5 - lat / 180.0) * h), int((lon / 360.0 + 0.5) * w)


def laplace_fill(a, hole, iters):
    a = a.copy()
    a[hole] = a[~hole].mean()
    for _ in range(iters):
        n = 0.25 * (np.roll(a, 1, 0) + np.roll(a, -1, 0) + np.roll(a, 1, 1) + np.roll(a, -1, 1))
        a[hole] = n[hole]
    return a


def box_blur(a, k):
    pad = np.pad(a, k, mode="edge")
    c = pad.cumsum(0).cumsum(1)
    c = np.pad(c, ((1, 0), (1, 0)))
    n = 2 * k + 1
    return (c[n:, n:] - c[:-n, n:] - c[n:, :-n] + c[:-n, :-n]) / (n * n)


def repair(px: np.ndarray):
    h, w = px.shape[:2]
    r = px[..., 0].astype(np.float64) / 255.0
    g = px[..., 1].astype(np.float64) / 255.0
    # 1. locate: the G peak (smoothed over ~0.5 deg) near the nominal direction
    ang0 = angle_deg(h, w, *NOMINAL)
    ys, xs = np.nonzero(ang0 < SEARCH_DEG)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    gs = box_blur(g[y0:y1, x0:x1], 3)
    gs[ang0[y0:y1, x0:x1] >= SEARCH_DEG] = -1.0
    cy, cx = np.unravel_index(int(np.argmax(gs)), gs.shape)
    cy, cx = cy + y0, cx + x0
    lat_c = 90.0 - (cy + 0.5) / h * 180.0
    lon_c = ((cx + 0.5) / w - 0.5) * 360.0
    ang = angle_deg(h, w, lat_c, lon_c)
    # 2. window around the disc
    ys, xs = np.nonzero(ang < GHOST_DEG + FEATHER_DEG + 1.0)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    disc = ang[y0:y1, x0:x1] < GHOST_DEG
    dy, dx = DONOR_OFFSET
    out_ch = []
    for ch in (r, g):
        win = ch[y0:y1, x0:x1]
        fill = laplace_fill(win, disc, FILL_ITER)
        donor = ch[y0 + dy:y1 + dy, x0 + dx:x1 + dx]
        detail = donor - box_blur(donor, 6)                    # cloud texture finer than ~1 deg
        fill = np.clip(fill + detail, 0.0, 1.0)
        t = np.clip((GHOST_DEG + FEATHER_DEG - ang[y0:y1, x0:x1]) / FEATHER_DEG, 0.0, 1.0)
        t = t * t * (3.0 - 2.0 * t)
        res = ch.copy()
        res[y0:y1, x0:x1] = win * (1.0 - t) + fill * t
        out_ch.append(res)
    out = px.copy()
    out[..., 0] = np.uint8(np.round(out_ch[0] * 255))
    out[..., 1] = np.uint8(np.round(out_ch[1] * 255))
    core = ang < 1.2
    ring = (ang >= GHOST_DEG + FEATHER_DEG) & (ang < GHOST_DEG + FEATHER_DEG + 2.0) & (r > 0.1)
    stats = {
        "ghost_texel": [int(cy), int(cx)], "ghost_lat_lon_deg": [round(lat_c, 2), round(lon_c, 2)],
        "ghost_deg": GHOST_DEG, "feather_deg": FEATHER_DEG,
        "core_g_mean_before": round(float(g[core].mean()), 3), "core_g_mean_after": round(float(out_ch[1][core].mean()), 3),
        "core_r_mean_before": round(float(r[core].mean()), 3), "core_r_mean_after": round(float(out_ch[0][core].mean()), 3),
        "ring_g_p50": round(float(np.percentile(g[ring], 50)), 3), "ring_g_p95": round(float(np.percentile(g[ring], 95)), 3),
        "changed_outside": int(((out != px).any(axis=-1) & (ang > GHOST_DEG + FEATHER_DEG + 0.05)).sum()),
    }
    return out, stats, (y0, y1, x0, x1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=TEX)
    ap.add_argument("--out", default=TEX)
    ap.add_argument("--preview", default="")
    a = ap.parse_args()
    raw = open(a.src, "rb").read()
    if hashlib.sha256(raw).hexdigest() != SRC_SHA:
        raise SystemExit("source is not the glass-sky-s24 map (texture_sha256 mismatch) - pass --src <that png>")
    px = np.array(Image.open(a.src).convert("RGBA"))
    out, stats, (y0, y1, x0, x1) = repair(px)
    Image.fromarray(out, "RGBA").save(a.out, optimize=True)
    if a.preview:
        cy, cx = stats["ghost_texel"]
        sl = (slice(cy - 90, cy + 90), slice(cx - 160, cx + 160))
        top = np.concatenate([px[sl + (0,)], px[sl + (1,)]], axis=1)
        bot = np.concatenate([out[sl + (0,)], out[sl + (1,)]], axis=1)
        Image.fromarray(np.concatenate([top, bot], axis=0)).resize((1280, 720), Image.LANCZOS).save(a.preview, quality=92)
    stats["out"] = a.out
    stats["out_sha256"] = hashlib.sha256(open(a.out, "rb").read()).hexdigest()
    print(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main()
