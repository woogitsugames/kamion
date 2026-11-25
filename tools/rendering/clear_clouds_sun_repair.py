"""Repair the circumsolar area of the photographic Clear cloud map (glass-sky-s24, ADR 0332 addendum).

Why: T_ClearClouds.png (ADR 0108, CC0 Poly Haven kloofendal_48d_partly_cloudy_puresky) is derived from an HDRI with a
chromatic blue-gap matte. Around the photographed sun that matte fails in two ways, and WorldAtmosphere rotates the map
so the photographed sun sits exactly on the game sun - so the defect is ALWAYS next to the sun (critic s24 build #8 P1#4,
t2370 / t2480 / t2590 / t2700 / t3140):
  1. "hole": the generator zeroed the opacity within 1.5 deg of the sun (a black disc in a white cloud);
  2. "halo": the bright, nearly neutral circumsolar sky has no blue excess, so the matte keeps it as semi-transparent
     cloud with saturated luminance - a soft white ring around the hole that has no cloud structure at all.
Real cumulus edges near the sun are crisp silver linings; the sky between them is the analytic circumsolar Perez dome.

What: inside the circumsolar cap (sun angle < CAP_DEG, smooth to 0 at CAP_DEG + FEATHER_DEG) the opacity R is re-matted
with a hard-ish threshold (the glow ramps go to clear sky, the cloud bodies stay opaque; the zeroed sun disc and its
semi-transparent surroundings become a clear gap, so the sun disc of Kamion/Sky stays visible and agrees with the hard sun
shadows of the scene), and the luminance G is capped at the cloud-body percentile measured outside the cap (the silver
edge stays the brightest part, but no saturated white blob). Outside the cap the map is unchanged byte for byte.

Input: the existing derived PNG (the raw HDRI is not kept on disk); the original is backed up next to the script output
once as T_ClearClouds.orig.png in artifacts (not shipped). Deterministic, idempotent on the original.

Run:  uv run --no-project --with numpy --with pillow python tools/rendering/clear_clouds_sun_repair.py [--src <png>] [--out <png>] [--preview <jpg>]
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
META = os.path.join(SKY, "ClearCloudsSource.json")
ORIG_SHA = "b643d037e1ee85027147733415529033bb4e35bba3fe117539eb0113697c4c61"   # ADR 0108 texture_sha256
HOLE_DEG = 3.0        # the zeroed sun disc (1.5 deg) and the semi-transparent blobs beside it: filled from the cloud around
CAP_DEG = 9.0         # circumsolar cap: the soft glow fringe of this HDRI ends ~7 deg below the sun (WORKING_VALUE)
FEATHER_DEG = 2.5     # blend back to the untouched map
MATTE = (0.30, 0.60)  # opacity re-matte inside the cap (smoothstep): the soft glow ramp becomes a crisp cloud edge
EDGE_NOISE = 0.9      # amplitude of the threshold noise (in opacity units)
FILL_ITER = 600       # Jacobi iterations of the Laplace fill (converged for a ~70 px hole)


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def sun_angle_deg(w, h, sun):
    # Texture layout of Kamion/Sky: u = atan2(x, z) / 2pi + 0.5, v = asin(y) / pi + 0.5 (PNG row 0 = top = v 1).
    lat = np.pi * (0.5 - (np.arange(h, dtype=np.float64) + 0.5) / h)
    lon = 2 * np.pi * ((np.arange(w, dtype=np.float64) + 0.5) / w - 0.5)
    s = np.array([sun["x"], sun["y"], sun["z"]], np.float64)
    s /= np.linalg.norm(s)
    s_lat, s_lon = math.asin(s[1]), math.atan2(s[0], s[2])
    d = np.sin(lat)[:, None] * math.sin(s_lat) + np.cos(lat)[:, None] * math.cos(s_lat) * np.cos(lon[None, :] - s_lon)
    return np.degrees(np.arccos(np.clip(d, -1.0, 1.0)))


def laplace_fill(a, hole, iters):
    """Harmonic fill of a[hole] from its boundary (4-neighbour Jacobi; a is a small window)."""
    a = a.copy()
    a[hole] = a[~hole].mean()
    for _ in range(iters):
        n = 0.25 * (np.roll(a, 1, 0) + np.roll(a, -1, 0) + np.roll(a, 1, 1) + np.roll(a, -1, 1))
        a[hole] = n[hole]
    return a


def repair(px: np.ndarray, sun: dict):
    h, w = px.shape[:2]
    r = px[..., 0].astype(np.float64) / 255.0
    g = px[..., 1].astype(np.float64) / 255.0
    ang = sun_angle_deg(w, h, sun)
    # 1. hole: Laplace fill of the opacity and luminance from the cloud around the photographed sun
    ys, xs = np.nonzero(ang < CAP_DEG + FEATHER_DEG + 1.0)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    hole = (ang[y0:y1, x0:x1] < HOLE_DEG) & (r[y0:y1, x0:x1] < 0.9)
    r_f, g_f = r.copy(), g.copy()
    r_f[y0:y1, x0:x1] = laplace_fill(r[y0:y1, x0:x1], hole, FILL_ITER)
    # luminance of the filled disc: the brightness of the opaque cloud ring just outside it (the photo's sun core and the
    # removed disc left a darker spot in G that would read as a grey blot in the white cloud)
    ring = (ang >= HOLE_DEG) & (ang < HOLE_DEG * 1.5) & (r > 0.9)
    g_ring = float(np.percentile(g[ring], 50)) if ring.any() else 1.0
    disc = ang < HOLE_DEG
    g_f[disc] = np.maximum(g[disc], g_ring)
    # the glow made the fringe a smooth circular arc: break the re-matte threshold with billow-scale noise
    # (fractal value noise, 0.4-3 deg, seed 332) so the new edge has the ragged outline of the cumulus around it
    rng = np.random.default_rng(332)
    win = (y1 - y0, x1 - x0)
    noise = np.zeros(win)
    for cell, amp in ((34, 0.5), (14, 0.3), (5, 0.2)):          # texels (1 texel = 0.088 deg)
        lat = rng.random((win[0] // cell + 3, win[1] // cell + 3))
        yy, xx = np.mgrid[0:win[0], 0:win[1]] / cell
        iy, ix = yy.astype(int), xx.astype(int)
        fy, fx = yy - iy, xx - ix
        fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
        noise += amp * ((lat[iy, ix] * (1 - fx) + lat[iy, ix + 1] * fx) * (1 - fy)
                        + (lat[iy + 1, ix] * (1 - fx) + lat[iy + 1, ix + 1] * fx) * fy)
    jitter = np.zeros_like(r)
    jitter[y0:y1, x0:x1] = (noise - 0.5) * EDGE_NOISE
    # 2. halo: crisp re-matte of the soft glow fringe inside the cap, feathered back to the original map
    blend = 1.0 - smooth(CAP_DEG, CAP_DEG + FEATHER_DEG, ang)          # 1 inside the cap, 0 outside
    r_out = r_f * (1.0 - blend) + smooth(MATTE[0], MATTE[1], r_f + jitter) * blend
    g_out = g_f
    out = px.copy()
    out[..., 0] = np.uint8(np.round(np.clip(r_out, 0, 1) * 255))
    out[..., 1] = np.uint8(np.round(np.clip(g_out, 0, 1) * 255))
    cap = ang < CAP_DEG
    stats = {
        "hole_deg": HOLE_DEG, "hole_pixels": int(hole.sum()), "cap_deg": CAP_DEG, "feather_deg": FEATHER_DEG,
        "matte": list(MATTE),
        "cap_pixels": int(cap.sum()),
        "cap_semi_transparent_before": float(((r > 0.1) & (r < 0.9) & cap).sum() / max(cap.sum(), 1)),
        "cap_semi_transparent_after": float(((r_out > 0.1) & (r_out < 0.9) & cap).sum() / max(cap.sum(), 1)),
        "cap_g_saturated_before": float(((g > 0.98) & (r > 0.1) & cap).sum() / max(cap.sum(), 1)),
        "cap_g_saturated_after": float(((g_out > 0.98) & (r_out > 0.1) & cap).sum() / max(cap.sum(), 1)),
        "changed_outside_feather": int(((out != px).any(axis=-1) & (ang > CAP_DEG + FEATHER_DEG)).sum()),
    }
    return out, stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=TEX)
    ap.add_argument("--out", default=TEX)
    ap.add_argument("--preview", default="")
    a = ap.parse_args()
    meta = json.load(open(META, encoding="utf-8"))
    raw = open(a.src, "rb").read()
    if hashlib.sha256(raw).hexdigest() != ORIG_SHA:
        raise SystemExit("source is not the ADR 0108 original (texture_sha256 mismatch) - pass --src <original png>")
    px = np.array(Image.open(a.src).convert("RGBA"))
    out, stats = repair(px, meta["sunDirection"])
    Image.fromarray(out, "RGBA").save(a.out, optimize=True)
    if a.preview:
        # 30 x 20 deg window around the photographed sun: R | G before (top) and after (bottom)
        h, w = px.shape[:2]
        s = meta["sunDirection"]
        u = (math.atan2(s["x"], s["z"]) / (2 * math.pi) + 0.5) * w
        v = (1.0 - (math.asin(s["y"]) / math.pi + 0.5)) * h
        x0, y0 = int(u - 240), int(v - 160)
        crop = lambda im, c: im[y0:y0 + 320, x0:x0 + 480, c]
        top = np.concatenate([crop(px, 0), crop(px, 1)], axis=1)
        bot = np.concatenate([crop(out, 0), crop(out, 1)], axis=1)
        Image.fromarray(np.concatenate([top, bot], axis=0)).save(a.preview, quality=92)
    stats["out"] = a.out
    stats["out_sha256"] = hashlib.sha256(open(a.out, "rb").read()).hexdigest()
    print(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main()
