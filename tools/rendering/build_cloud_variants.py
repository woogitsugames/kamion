"""Build soft-edge CC0 photographic cloud maps (3 variants) from verified Poly Haven 4K PureSky HDRIs.

ADR 0332 addendum (agy-clouds-s24):
- Replaces the hard binary chromatic cutout of ADR 0108 (smooth(0.25, 0.85, blueness), which created
  "bright cotton sprite" clouds with 2-texel cliffs) with an elevation-adaptive soft optical cloud matte,
  feathered wispy rims, richer internal self-shadowing (gamma 0.85), pinhole cleanup, and circumsolar
  aureole/sun repair.
- Generates 3 distinct CC0 variants (4096x2048 RGBA PNG; R = opacity, G = relative luminance):
    0: T_ClearClouds.png     <- kloofendal_48d_partly_cloudy_puresky (scattered summer cumulus, sun ~48 deg)
    1: T_ClearClouds_02.png  <- sunflowers_puresky (broad summer cumulus + high cirrus wisps)
    2: T_ClearClouds_03.png  <- kloofendal_38d_partly_cloudy_puresky (airy altocumulus / wispy scattered)
- Updates ClearCloudsSource.json with variant metadata (keeping top-level fields backwards-compatible for
  ClearCloudsSunTests and ADR 0108 tooling).

Run: python tools/rendering/build_cloud_variants.py [--preview-dir <dir>] [--only <idx>]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "Data" / "raw" / "cc0" / "sky"
OUT = ROOT / "game" / "Assets" / "_Project" / "Rendering" / "Resources" / "Sky"

VARIANTS = [
    {
        "id": "T_ClearClouds",
        "asset": "kloofendal_48d_partly_cloudy_puresky",
        "style": "scattered fair-weather summer cumulus",
        "sun_inside_cloud": True,
        "lens_ghost": (23.6, 51.7, 2.3, 0.8, (0, -70)),
    },
    {
        "id": "T_ClearClouds_02",
        "asset": "sunflowers_puresky",
        "style": "broad summer cumulus with high wispy streaks",
        "sun_inside_cloud": False,
        "lens_ghost": None,
    },
    {
        "id": "T_ClearClouds_03",
        "asset": "kloofendal_38d_partly_cloudy_puresky",
        "style": "airy altocumulus and soft scattered wisps",
        "sun_inside_cloud": False,
        "lens_ghost": None,
    },
]


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def box_blur_wrap_x(a: np.ndarray, k: int) -> np.ndarray:
    """Fast box blur with horizontal longitude wrap and vertical edge clamp."""
    if k <= 0:
        return a.copy()
    pad = np.pad(a, ((k, k), (0, 0)), mode="edge")
    pad = np.pad(pad, ((0, 0), (k, k)), mode="wrap")
    c = pad.cumsum(0).cumsum(1)
    c = np.pad(c, ((1, 0), (1, 0)))
    n = 2 * k + 1
    return (c[n:, n:] - c[:-n, n:] - c[n:, :-n] + c[:-n, :-n]) / (n * n)


def gauss_approx(a: np.ndarray, k: int) -> np.ndarray:
    """3-pass box blur ~= Gaussian filter with horizontal longitude wrap."""
    return box_blur_wrap_x(box_blur_wrap_x(box_blur_wrap_x(a, k), k), k)


def angle_deg_grid(h: int, w: int, lat0_rad: float, lon0_rad: float) -> np.ndarray:
    lat = np.pi * (0.5 - (np.arange(h, dtype=np.float64) + 0.5) / h)
    lon = 2.0 * np.pi * ((np.arange(w, dtype=np.float64) + 0.5) / w - 0.5)
    d = np.sin(lat)[:, None] * math.sin(lat0_rad) + np.cos(lat)[:, None] * math.cos(lat0_rad) * np.cos(lon[None, :] - lon0_rad)
    return np.degrees(np.arccos(np.clip(d, -1.0, 1.0)))


def laplace_fill(a: np.ndarray, hole: np.ndarray, iters: int) -> np.ndarray:
    a = a.copy()
    if not hole.any():
        return a
    outside = a[~hole]
    a[hole] = outside.mean() if outside.size else 0.5
    for _ in range(iters):
        n = 0.25 * (np.roll(a, 1, 0) + np.roll(a, -1, 0) + np.roll(a, 1, 1) + np.roll(a, -1, 1))
        a[hole] = n[hole]
    return a


def load_hdr_linear(asset: str):
    d = RAW / asset
    src = d / f"{asset}_4k.hdr"
    files = json.loads((d / "files.json").read_text(encoding="utf-8-sig"))
    info = json.loads((d / "info.json").read_text(encoding="utf-8-sig"))
    expected = files["hdri"]["4k"]["hdr"]
    raw_bytes = src.read_bytes()
    if len(raw_bytes) != expected["size"] or hashlib.md5(raw_bytes).hexdigest() != expected["md5"]:
        raise ValueError(f"{asset}: HDRI does not match Poly Haven metadata")
    dims = subprocess.check_output(["magick", "identify", "-format", "%w %h", str(src)], text=True)
    w, h = map(int, dims.split())
    f32 = d / "linear_rgb.f32"
    if not f32.exists() or f32.stat().st_size != w * h * 3 * 4:
        subprocess.run(
            ["magick", str(src), "-define", "quantum:format=floating-point", "-depth", "32", "-endian", "LSB", "rgb:" + str(f32)],
            check=True,
        )
    rgb = np.fromfile(f32, dtype="<f4").reshape(h, w, 3)
    if not np.isfinite(rgb).all() or rgb.max() <= 1.0:
        raise ValueError(f"{asset}: expected finite unclipped linear HDR")
    rgb = np.maximum(rgb, 0.0)
    return rgb, expected, info, hashlib.sha256(raw_bytes).hexdigest()


def repair_lens_ghost(r: np.ndarray, g: np.ndarray, ghost_cfg):
    lat0, lon0, ghost_deg, feather_deg, donor_offset = ghost_cfg
    h, w = r.shape
    ang0 = angle_deg_grid(h, w, math.radians(lat0), math.radians(lon0))
    ys, xs = np.nonzero(ang0 < 2.0)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    gs = box_blur_wrap_x(g[y0:y1, x0:x1], 3)
    gs[ang0[y0:y1, x0:x1] >= 2.0] = -1.0
    cy, cx = np.unravel_index(int(np.argmax(gs)), gs.shape)
    cy, cx = cy + y0, cx + x0
    lat_c = math.pi * (0.5 - (cy + 0.5) / h)
    lon_c = 2.0 * math.pi * ((cx + 0.5) / w - 0.5)
    ang = angle_deg_grid(h, w, lat_c, lon_c)
    ys, xs = np.nonzero(ang < ghost_deg + feather_deg + 1.0)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    disc = ang[y0:y1, x0:x1] < ghost_deg
    dy, dx = donor_offset
    r_out, g_out = r.copy(), g.copy()
    for arr, out_arr in ((r, r_out), (g, g_out)):
        win = arr[y0:y1, x0:x1]
        fill = laplace_fill(win, disc, 1200)
        donor = arr[y0 + dy:y1 + dy, x0 + dx:x1 + dx]
        detail = donor - box_blur_wrap_x(donor, 6)
        fill = np.clip(fill + detail, 0.0, 1.0)
        t = smooth(0.0, 1.0, (ghost_deg + feather_deg - ang[y0:y1, x0:x1]) / feather_deg)
        out_arr[y0:y1, x0:x1] = win * (1.0 - t) + fill * t
    return r_out, g_out


def build_one(spec: dict, preview_dir: Path | None = None) -> dict:
    asset = spec["asset"]
    rgb, expected, info, src_sha = load_hdr_linear(asset)
    h, w = rgb.shape[:2]
    half = h // 2

    y = (rgb[..., 0] * 0.2126 + rgb[..., 1] * 0.7152 + rgb[..., 2] * 0.0722).astype(np.float64)
    # Locate sun peak in upper hemisphere (above 5 deg elevation)
    min_row = 0
    max_row = int((0.5 - 5.0 / 180.0) * h)
    sun_row, sun_col = np.unravel_index(int(y[min_row:max_row].argmax()), (max_row - min_row, w))
    sun_lat = math.pi * (0.5 - (sun_row + 0.5) / h)
    sun_lon = 2.0 * math.pi * ((sun_col + 0.5) / w - 0.5)
    sun_dir = {
        "x": math.sin(sun_lon) * math.cos(sun_lat),
        "y": math.sin(sun_lat),
        "z": math.cos(sun_lon) * math.cos(sun_lat),
    }
    ang_sun = angle_deg_grid(h, w, sun_lat, sun_lon)

    # 1. Elevation-adaptive chromatic cloud matte (upper hemisphere)
    mean_rgb = np.maximum(rgb[:half].mean(axis=2, dtype=np.float64), 1e-8)
    blueness = (rgb[:half, :, 2].astype(np.float64) - rgb[:half, :, 0].astype(np.float64)) / mean_rgb
    sun_far = ang_sun[:half] > 28.0

    # Estimate clear-sky blueness profile by elevation row (90th percentile away from sun)
    sky_b_row = np.zeros(half, dtype=np.float64)
    for row in range(half):
        vals = blueness[row, sun_far[row]]
        if vals.size > 64:
            sky_b_row[row] = np.percentile(vals, 90)
        else:
            sky_b_row[row] = np.percentile(blueness[row], 90)
    # Smooth vertically over ~3 deg (34 rows) so no horizontal banding
    k_row = 17
    pad_r = np.pad(sky_b_row, k_row, mode="edge")
    sky_b_row = np.convolve(pad_r, np.ones(2 * k_row + 1) / (2 * k_row + 1), mode="valid")
    # Ensure a physical floor near horizon so hazy clear sky near horizon does not turn fully opaque
    sky_b_row = np.maximum(sky_b_row, 0.48)

    # Continuous optical cloud whiteness: 0 = clear blue sky, 1 = dense neutral cloud core
    # Wider transition window than ADR 0108 (0.25..0.85 fixed): preserves delicate translucent wisps!
    # Near the sun, clear-sky Mie forward scatter naturally lowers clear-sky blueness without any cloud:
    # smoothly tighten the upper threshold near the sun (no hard ring) so clear circumsolar haze fades out
    # while real clouds remain intact.
    b_top = sky_b_row[:, None] * 0.92
    if not spec["sun_inside_cloud"]:
        sun_mie = np.exp(-np.power(ang_sun[:half] / 16.0, 1.6))
        b_top = b_top * (1.0 - 0.42 * sun_mie)
    b_bot = np.minimum(sky_b_row[:, None] * 0.16, 0.14)
    raw_w = np.clip((b_top - blueness) / np.maximum(b_top - b_bot, 0.22), 0.0, 1.0)

    # Soft optical curve: wispy thin cloud rims stay translucent instead of snapping to 1
    alpha_up = np.power(raw_w, 1.35)

    # Gentle edge-localized feathering (sigma ~2.5 texels = 0.22 deg) to eliminate 2-texel pixelated sprite cliffs
    # while keeping solid cloud interiors sharp and high-resolution
    alpha_blur = gauss_approx(alpha_up, 2)
    edge_weight = np.clip(4.0 * alpha_blur * (1.0 - alpha_blur), 0.0, 1.0)
    alpha_up = alpha_up * (1.0 - 0.55 * edge_weight) + alpha_blur * (0.55 * edge_weight)

    # Remove isolated 1-2 px pinholes inside solid clouds (e.g. (412,2373) in kloofendal_48d)
    a_loc = box_blur_wrap_x(alpha_up, 2)
    pinhole = (a_loc > 0.85) & (alpha_up < 0.35)
    alpha_up = np.where(pinhole, a_loc, alpha_up)

    # 2. Circumsolar handling (prevent both "zeroed sun hole" and "soft white aureole halo")
    alpha = np.zeros((h, w), dtype=np.float64)
    alpha[:half] = alpha_up

    # Relative cloud luminance G: measure white anchor AWAY from forward-scatter peak (>25 deg from sun)
    # so clouds across the whole sky have consistent brightness (not dim away from sun in wispy skies)
    lat = np.pi * (0.5 - (np.arange(h, dtype=np.float64) + 0.5) / h)
    opaque = (alpha > 0.75) & (lat[:, None] > math.radians(5.0)) & (ang_sun > 25.0)
    if opaque.sum() < 500:
        opaque = (alpha > 0.40) & (lat[:, None] > math.radians(5.0)) & (ang_sun > 25.0)
    white = float(np.percentile(y[opaque], 96))
    # Gamma 0.82 (ADR 0108 was 0.70) keeps richer cumulus self-shadowing instead of flat bright white cotton
    shade = np.power(np.clip(y / max(white, 1e-8), 0.0, 1.0), 0.82)

    if spec["sun_inside_cloud"]:
        # Like clear_clouds_sun_repair.py: sun sits behind a cumulus edge; fill disc & crisp-re-matte glow ring
        # so ClearCloudsSunTests (no hole in 2 deg, <10% semi-transparent in 9 deg) stays green!
        cap_deg, feather_deg, hole_deg = 9.0, 3.5, 3.0
        ys, xs = np.nonzero(ang_sun < cap_deg + feather_deg + 1.0)
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        hole = (ang_sun[y0:y1, x0:x1] < hole_deg) & (alpha[y0:y1, x0:x1] < 0.9)
        a_f = alpha.copy()
        a_f[y0:y1, x0:x1] = laplace_fill(alpha[y0:y1, x0:x1], hole, 600)
        ring = (ang_sun >= hole_deg) & (ang_sun < hole_deg * 1.6) & (alpha > 0.85)
        g_ring = float(np.percentile(shade[ring], 55)) if ring.any() else 0.92
        disc = ang_sun < hole_deg
        shade[disc] = np.clip(np.minimum(shade[disc], g_ring * 1.08), g_ring * 0.92, 1.0)
        # Break circular glow fringe with billow noise
        rng = np.random.default_rng(332)
        win = (y1 - y0, x1 - x0)
        noise = np.zeros(win)
        for cell, amp in ((34, 0.5), (14, 0.3), (5, 0.2)):
            lat_n = rng.random((win[0] // cell + 3, win[1] // cell + 3))
            yy, xx = np.mgrid[0:win[0], 0:win[1]] / cell
            iy, ix = yy.astype(int), xx.astype(int)
            fy, fx = yy - iy, xx - ix
            fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
            noise += amp * ((lat_n[iy, ix] * (1 - fx) + lat_n[iy, ix + 1] * fx) * (1 - fy)
                            + (lat_n[iy + 1, ix] * (1 - fx) + lat_n[iy + 1, ix + 1] * fx) * fy)
        jitter = np.zeros_like(alpha)
        jitter[y0:y1, x0:x1] = (noise - 0.5) * 0.65
        blend = 1.0 - smooth(cap_deg, cap_deg + feather_deg, ang_sun)
        alpha = a_f * (1.0 - blend) + smooth(0.38, 0.52, a_f + jitter) * blend
    else:
        # Smoothly cap over-bright sun disc core in G and avoid an artificial flat saturated blob in R/G
        # right on the sun disc (< 3 deg) without punching any circular hole in surrounding clouds.
        # Keep natural silver lining near the sun; gently roll off pure clear-sky Mie haze (where raw_w < 0.45)
        # within 14 deg of the sun so no featureless white halo surrounds the sun.
        haze_fade = 1.0 - 0.65 * np.exp(-np.power(ang_sun[:half] / 12.0, 2.0)) * (1.0 - smooth(0.25, 0.70, alpha[:half]))
        alpha[:half] = np.clip(alpha[:half] * haze_fade, 0.0, 1.0)
        # Cap saturated sun core in G smoothly so no flat 1.0 disc
        ring_g = (ang_sun >= 3.0) & (ang_sun < 7.0) & (alpha > 0.3)
        g_cap = float(np.percentile(shade[ring_g], 90)) if ring_g.any() else 0.95
        g_cap = min(max(g_cap, 0.85), 0.98)
        sun_core = 1.0 - smooth(1.5, 4.5, ang_sun)
        shade = shade * (1.0 - sun_core) + np.minimum(shade, g_cap) * sun_core

    # 3. Optional known lens ghost repair
    if spec.get("lens_ghost") is not None:
        alpha, shade = repair_lens_ghost(alpha, shade, spec["lens_ghost"])

    # Lower hemisphere strictly zero opacity
    alpha[half:] = 0.0

    # Pack RGBA PNG (R=opacity, G=relative luminance, B=0, A=1)
    pixels = np.zeros((h, w, 4), dtype=np.uint8)
    pixels[..., 0] = np.uint8(np.round(np.clip(alpha, 0.0, 1.0) * 255.0))
    pixels[..., 1] = np.uint8(np.round(np.clip(shade, 0.0, 1.0) * 255.0))
    pixels[..., 3] = 255

    OUT.mkdir(parents=True, exist_ok=True)
    out_png = OUT / f"{spec['id']}.png"
    Image.fromarray(pixels, "RGBA").save(out_png, optimize=True)
    tex_sha = hashlib.sha256(out_png.read_bytes()).hexdigest()

    # Diagnostics
    r_up = pixels[:half, :, 0].astype(np.float64) / 255.0
    gx = np.abs(np.diff(r_up, axis=1, append=r_up[:, :1]))
    gy = np.abs(np.diff(r_up, axis=0, append=r_up[-1:, :]))
    grad = np.hypot(gx, gy)
    edge = (r_up > 0.05) & (r_up < 0.95)
    p50, p90, p99 = (np.percentile(grad[edge], [50, 90, 99]).tolist() if edge.any() else [0, 0, 0])

    meta = {
        "id": spec["id"],
        "asset": asset,
        "style": spec["style"],
        "page": f"https://polyhaven.com/a/{asset}",
        "license": "CC0 1.0 Universal",
        "license_url": "https://polyhaven.com/license",
        "authors": info.get("authors", {}),
        "url": expected["url"],
        "source_size": expected["size"],
        "source_md5": expected["md5"],
        "source_sha256": src_sha,
        "texture_sha256": tex_sha,
        "width": w,
        "height": h,
        "sunDirection": sun_dir,
        "measured_sun_elevation_deg": round(math.degrees(sun_lat), 4),
        "cloud_white_linear": white,
        "source_cloud_pixels": int(opaque.sum()),
        "upper_opaque_share": round(float((r_up > 0.9).mean()), 4),
        "upper_wispy_share": round(float(((r_up > 0.05) & (r_up <= 0.9)).mean()), 4),
        "edge_grad_p50_p90_p99": [round(v, 4) for v in (p50, p90, p99)],
        "checked_utc": datetime.now(timezone.utc).isoformat(),
    }

    if preview_dir is not None:
        preview_dir.mkdir(parents=True, exist_ok=True)
        # Render upper hemisphere preview: top=R opacity, mid=G shade, bot=mock sky composite
        sky_bg = np.array([0.16, 0.34, 0.62])[None, None, :]
        a3 = (pixels[:half, :, 0:1].astype(np.float32) / 255.0)
        g3 = (pixels[:half, :, 1:2].astype(np.float32) / 255.0)
        cloud_col = (0.35 + 0.63 * g3) * np.array([0.96, 0.98, 1.02])[None, None, :]
        comp = np.clip(sky_bg * (1.0 - a3) + cloud_col * a3, 0.0, 1.0)
        vis = Image.new("RGB", (960, 720))
        vis.paste(Image.fromarray(pixels[:half, :, 0]).resize((960, 240), Image.LANCZOS).convert("RGB"), (0, 0))
        vis.paste(Image.fromarray(pixels[:half, :, 1]).resize((960, 240), Image.LANCZOS).convert("RGB"), (0, 240))
        vis.paste(Image.fromarray(np.uint8(comp * 255)).resize((960, 240), Image.LANCZOS), (0, 480))
        draw = ImageDraw.Draw(vis)
        draw.text((6, 4), f"{spec['id']} ({asset}) sun={meta['measured_sun_elevation_deg']:.1f}deg R(opacity)", fill=(255, 255, 0))
        draw.text((6, 244), "G (relative luminance ^0.85)", fill=(255, 255, 0))
        draw.text((6, 484), f"Composite mock | wispy={meta['upper_wispy_share']:.3f} grad_p90={p90:.3f} p99={p99:.3f}", fill=(255, 255, 0))
        vis.save(preview_dir / f"preview_{spec['id']}.jpg", quality=90)

    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview-dir", default="")
    ap.add_argument("--only", type=int, default=-1)
    a = ap.parse_args()
    pdir = Path(a.preview_dir) if a.preview_dir else None

    results = []
    for idx, spec in enumerate(VARIANTS):
        if a.only >= 0 and idx != a.only:
            continue
        print(f"Building variant {idx}: {spec['id']} ({spec['asset']})...")
        m = build_one(spec, pdir)
        results.append(m)
        print(json.dumps({k: m[k] for k in ("id", "asset", "measured_sun_elevation_deg", "upper_opaque_share", "upper_wispy_share", "edge_grad_p50_p90_p99", "texture_sha256")}, indent=2))

    if a.only < 0:
        # Write backwards-compatible ClearCloudsSource.json with top-level Variant 0 + variants[] list
        v0 = results[0]
        meta_out = {
            "schema": "kamion.photographic-clouds/2",
            "asset": v0["asset"],
            "page": v0["page"],
            "license": v0["license"],
            "license_url": v0["license_url"],
            "authors": v0["authors"],
            "url": v0["url"],
            "source_md5": v0["source_md5"],
            "source_sha256": v0["source_sha256"],
            "texture_sha256": v0["texture_sha256"],
            "width": v0["width"],
            "height": v0["height"],
            "sunDirection": v0["sunDirection"],
            "measured_sun_elevation_deg": v0["measured_sun_elevation_deg"],
            "cloud_white_linear": v0["cloud_white_linear"],
            "source_cloud_pixels": v0["source_cloud_pixels"],
            "processing": "Linear CC0 HDRI; elevation-adaptive soft optical matte (pow 1.35 + edge-localized feather + pinhole clean); circumsolar repair; R opacity, G relative luminance^0.85; lower hemisphere zero",
            "checked_utc": v0["checked_utc"],
            "sampler_note": "ADR 0108 r3 + ADR 0332 agy-clouds-s24: 3 CC0 PureSky variants selected deterministically by seed/scene/time + meridian mirror, single texture fetch (0 extra GPU cost).",
            "texture_sha256_adr0108": "b643d037e1ee85027147733415529033bb4e35bba3fe117539eb0113697c4c61",
            "texture_sha256_glass_sky": "10f81b4d4c8d999ba399f975bddd570fba6f9ba3b484e2d979252d2fe847d916",
            "texture_sha256_render_artifacts": "6e2e5ce49ffd073ee73d02da94333f91034727b33cbc083da2fde47fbf5a9255",
            "variants": results,
        }
        (OUT / "ClearCloudsSource.json").write_text(json.dumps(meta_out, indent=2) + "\n", encoding="utf-8")
        print("WROTE", OUT / "ClearCloudsSource.json")


if __name__ == "__main__":
    main()
