"""Procedural track-bed texture of the rail stage (ADR 0217, FIX 3): crushed-stone ballast with the concrete sleepers,
fastenings and rails painted in, so the Low tier (LoD1 / LoD2 geometry: a ballast ribbon + rail boxes) still reads as
a railway track and LoD0's geometric sleepers sit exactly on painted ones (no pop at the LoD switch).

One tile `rail_bed.png`, sRGB, opaque:
  u  across the track: TEX_W_M metres centred on the track axis (u = 0.5 + lateral / TEX_W_M), clamped by geometry
  v  along the track: TILE_M metres = SLEEPERS_PER_TILE sleepers (v = along / TILE_M), periodic
Written next to the region's other generated textures only when the rail stage ran (like water_reeds.png, ADR 0213);
material `rail_bed` = {"texture": "rail_bed"} -> URP Lit with the PNG as base map (RegionImporter).

Colours. Measured on the GUGiK orthophoto 2025 (0.1 m) at the DW671 crossing, 10 cross-sections 40-120 m from the
crossing (artifacts/rail-fix-s21/ortho_measure.py): track band mean sRGB (118, 108, 94), asphalt (155, 154, 148) ->
the band is brown and darker than the road (linear luminance ratio 0.46). The game asphalt is darker than this aged
road (albedo 0.081), so absolute values are set against the game asphalt in the render loop, keeping the hue
R : G : B of the orthophoto. WORKING_VALUE until an owner photo of the track exists.
"""

from __future__ import annotations

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
from scipy.spatial import cKDTree

TEX_W_M = 5.12            # lateral coverage (1 cm / px at 512)
SLEEPERS_PER_TILE = 4
W_PX, H_PX = 512, 256
SEED = 217

# linear albedo
BALLAST = np.array([0.054, 0.045, 0.034])      # brown crushed stone (hue of the orthophoto band)
BALLAST_CLEAN = np.array([0.070, 0.066, 0.060])  # greyer stone on the shoulders (less brake dust / rust)
SLEEPER = np.array([0.150, 0.140, 0.122])      # weathered prestressed concrete
RUST = np.array([0.040, 0.024, 0.014])         # rail web / foot, fastenings
HEAD = np.array([0.30, 0.30, 0.31])            # running surface (polished)


def _srgb(lin):
    lin = np.clip(lin, 0.0, 1.0)
    return np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)


def bed(gauge_m=1.435, head_w_m=0.072, sleeper_l_m=2.60, sleeper_w_m=0.30, spacing_m=0.60):
    """RGB image of the bed tile (PIL)."""
    rng = np.random.default_rng(SEED)
    tile_m = SLEEPERS_PER_TILE * spacing_m
    px_u = TEX_W_M / W_PX
    px_v = tile_m / H_PX
    lat = (np.arange(W_PX) + 0.5) * px_u - TEX_W_M / 2            # lateral metres of every column
    along = (np.arange(H_PX) + 0.5) * px_v                         # metres along of every row
    LAT, AL = np.meshgrid(lat, along)

    # ---- stones: Voronoi cells of a jittered point set, periodic along the track
    n = int(TEX_W_M * tile_m / (0.045 * 0.045))                    # ~4.5 cm stones (31.5-50 mm ballast grading)
    pts = np.column_stack([rng.uniform(-TEX_W_M / 2, TEX_W_M / 2, n), rng.uniform(0, tile_m, n)])
    tone = rng.normal(1.0, 0.28, n).clip(0.45, 1.9)
    rusty = rng.uniform(0, 1, n)
    allp = np.concatenate([pts, pts + [0, tile_m], pts - [0, tile_m]])
    tree = cKDTree(allp)
    d, idx = tree.query(np.column_stack([LAT.ravel(), AL.ravel()]), k=2)
    cell = (idx[:, 0] % n).reshape(H_PX, W_PX)
    gap = ((d[:, 1] - d[:, 0]) / 0.045).reshape(H_PX, W_PX)       # 0 at a stone edge
    shade = np.clip(0.35 + 1.6 * gap, 0.35, 1.0)                   # dark joints between stones
    centre = np.clip(1.0 - (np.abs(LAT) - 1.0) / 0.7, 0.0, 1.0)    # 1 inside +-1.0 m, 0 beyond 1.7 m: dusty / rusty zone
    base = BALLAST[None, None, :] * centre[..., None] + BALLAST_CLEAN[None, None, :] * (1 - centre[..., None])
    warm = (rusty[cell] > 0.82)[..., None] * centre[..., None]     # single rust-brown stones near the rails
    base = base * (1 - 0.5 * warm) + 0.5 * warm * np.array([0.085, 0.045, 0.022])
    img = base * (tone[cell] * shade)[..., None]

    # ---- sleepers
    half_l = sleeper_l_m / 2
    conc_noise = gaussian_filter(rng.normal(0, 1, (H_PX, W_PX)), (3, 6), mode="wrap")
    conc_noise /= np.abs(conc_noise).max()
    fine = rng.normal(0, 1, (H_PX, W_PX))
    for k in range(SLEEPERS_PER_TILE):
        vc = (k + 0.5) * spacing_m
        dv = np.abs(AL - vc)
        # ballast creeps over the sleeper edges: ragged outline from low-pass noise
        rag = 0.018 * gaussian_filter(rng.normal(0, 1, (H_PX, W_PX)), 2.5, mode="wrap") / 0.12
        inside = (dv < sleeper_w_m / 2 + rag) & (np.abs(LAT) < half_l + rag)
        tint = 1.0 + 0.16 * conc_noise + 0.05 * fine + rng.normal(0, 0.05)
        # darker, dirtier concrete between the rails and at the fastenings
        grime = 1.0 - 0.30 * np.clip(1.0 - np.abs(LAT) / (gauge_m / 2), 0, 1) ** 0.5
        col = SLEEPER[None, None, :] * (tint * grime)[..., None]
        img = np.where(inside[..., None], col, img)
        # contact shadow of the proud sleeper on the crib ballast
        edge = np.clip((dv - sleeper_w_m / 2) / 0.05, 0, 1)
        near = (~inside) & (np.abs(LAT) < half_l + 0.03) & (dv < sleeper_w_m / 2 + 0.05)
        img = np.where(near[..., None], img * (0.55 + 0.45 * edge)[..., None], img)
        # fastening: base plate / clips, both sides of each rail
        for sgn in (-1, 1):
            rc = sgn * (gauge_m / 2 + head_w_m / 2)
            plate = (np.abs(LAT - rc) < 0.17) & (dv < 0.085)
            img = np.where(plate[..., None], RUST[None, None, :] * (1.5 + 0.4 * conc_noise)[..., None], img)

    # ---- rails: foot (rust) with the polished head on top; soft shadow beside the foot
    for sgn in (-1, 1):
        rc = sgn * (gauge_m / 2 + head_w_m / 2)
        dl = np.abs(LAT - rc)
        shadow = np.clip((dl - 0.075) / 0.07, 0.0, 1.0)
        img = img * (0.5 + 0.5 * shadow)[..., None]
        foot = dl < 0.075
        streak = 1.0 + 0.25 * gaussian_filter(rng.normal(0, 1, (H_PX, W_PX)), (8, 1), mode="wrap") / 0.2
        img = np.where(foot[..., None], RUST[None, None, :] * streak[..., None], img)
        head = dl < head_w_m / 2
        run = np.clip(1.0 - dl / (head_w_m / 2), 0, 1) ** 0.5       # brightest along the running band
        img = np.where(head[..., None], RUST[None, None, :] * (1 - run[..., None]) + HEAD[None, None, :] * run[..., None], img)

    out = (_srgb(img) * 255.0 + 0.5).astype(np.uint8)
    return Image.fromarray(out, "RGB")


def rail_u(left, gauge_m=1.435, head_w_m=0.072):
    """u of the four ribbon edges of a rail box (outer low, outer top, inner top, inner low; lateral growing to the
    left) on the painted rail of the tile: `left` = the rail on the +lateral side of its track axis."""
    rc = (1 if left else -1) * (gauge_m / 2 + head_w_m / 2)
    return [0.5 + (rc + d) / TEX_W_M for d in (-0.066, -0.022, 0.022, 0.066)]


def textures():
    return {"rail_bed": bed()}


if __name__ == "__main__":
    import sys
    im = bed()
    im.save(sys.argv[1] if len(sys.argv) > 1 else "rail_bed.png")
    a = np.asarray(im).astype(float)
    print("mean sRGB", a.reshape(-1, 3).mean(0).round(1), "crown (+-1.7 m) mean",
          a[:, 86:426].reshape(-1, 3).mean(0).round(1))
