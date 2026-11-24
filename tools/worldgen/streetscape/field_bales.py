"""ADR 0346: round straw and wrapped silage bales on rural fields of the ADR 0334 mosaic.

Two instanced prototypes sharing ONE opaque material (`field_bale`) and ONE 512 x 512 sRGB atlas
(`field_bale_atlas.png`):
  bale_straw    round straw bale lying on its side (D = 1.38 m, L = 1.20 m, WORKING_VALUE; golden weathered
                straw stalks, baling twine / net-wrap bands, spiral straw ends, ground-contact shading).
  bale_silage   round wrapped haylage / silage bale (D = 1.26 m, L = 1.20 m, WORKING_VALUE; off-white
                agricultural stretch film with overlapping wrap strips, soft pillow shoulders, no brands).

Geometry budget: LOD0 <= 300 tris (224 tris), LOD1 ~60 tris (60 tris, 10-sided smooth cylinder: 36 deg < 38 deg
crease angle), simplified collision cylinder (.col). No billboard/impostor LOD2 (the engine's impostor pipeline
in InstanceImporter.cs is tree-only and would add an extra alpha-tested material / draw call; LOD1 is 60 tris
opaque on the shared material).

Placement (rural tiles only, deterministic from the EPSG:2180 strip layout of vegetation.field_layout / field_use):
  - `bale_straw` on arable stubble strips (`stubble_baled`, part of `stubble`);
  - `bale_silage` on mown / hay meadows (`meadow_mown`, `meadow_hay`).
  - Two agricultural patterns chosen per strip from `fid`:
      (a) clustered runs along baler passes / tramlines parallel to the strip axis (cylinder axis across the
          pass, rolled off the baler as on Wikimedia Commons cs157787294.jpg / cs158450905.jpg);
      (b) compact loader line-ups of 3-5 bales near a strip edge / headland.
  - Moderate density (WORKING_VALUE), kept clear of roads, yards, buildings, baulks, trees and steep slopes.
"""

from __future__ import annotations

import math

import numpy as np
import shapely
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter

from . import paved as PV
from . import props as PP
from . import vegetation as VG

MAT = "field_bale"
ATLAS_NAME = "field_bale_atlas"
PROTO_STRAW = "bale_straw"
PROTO_SILAGE = "bale_silage"

# Dimensions (WORKING_VALUE: Polish standard 120 cm round balers, diameter 1.2-1.5 m x length 1.2 m)
STRAW_D_M = 1.38
STRAW_L_M = 1.20
SILAGE_D_M = 1.26
SILAGE_L_M = 1.20
SINK_M = 0.04               # buried bottom margin so bales never float on gentle slopes

# Placement parameters (WORKING_VALUE, moderate density on Podlasie summer fields)
MIN_POLY_M2 = VG.FIELD_PLANT_MIN_M2   # 2 ha minimum BDOT OT_PTTR_A polygon (same as field_plants)
POLY_MARGIN_M = 10.0                  # inside BDOT polygon outline (clear of ditches / margin scrub)
ROAD_CLEAR_M = 12.0                   # clear of roads, paved yards and buildings
TREE_CLEAR_M = 4.0                    # clear of placed trees / baulk shrubs
STRIP_EDGE_CLEAR_M = 3.5              # clear of strip baulks
BLOCK_EDGE_CLEAR_M = 5.0              # clear of block / district boundaries
MAX_SLOPE = 0.18                      # ~10 deg max terrain slope under a bale

# Share of strips of each ADR 0334 use that carry bales (WORKING_VALUE)
USE_STRIP_SHARE = {
    "stubble_baled": 0.78,
    "stubble": 0.32,
    "meadow_mown": 0.42,
    "meadow_hay": 0.36,
}
USE_PROTO = {
    "stubble_baled": PROTO_STRAW,
    "stubble": PROTO_STRAW,
    "meadow_mown": PROTO_SILAGE,
    "meadow_hay": PROTO_SILAGE,
}
# Pattern split per prototype: probability of "rows along baler pass" vs "edge loader group"
ROW_PATTERN_SHARE = {PROTO_STRAW: 0.65, PROTO_SILAGE: 0.45}

# Row-along-pass parameters (WORKING_VALUE)
ROW_SEG_M = 140.0
ROW_SEG_KEEP = 0.48
ROW_STEP_M = 34.0
ROW_JITTER_ALONG_M = 4.5
ROW_JITTER_ACROSS_M = 0.8

# Edge-group parameters (WORKING_VALUE)
GROUP_SEG_M = 210.0
GROUP_SEG_KEEP = 0.55
GROUP_SIZE = (3, 5)
GROUP_GAP_M = 0.55                    # gap between neighbouring bales in a loader line-up

# Atlas layout (512 x 512 sRGB, v up; 4 quadrants of 256 x 256 with 12 px bleed padding)
ATLAS_SIZE = 512
ATLAS_PAD_PX = 12
_P = ATLAS_PAD_PX / ATLAS_SIZE
# (u0, v0, u1, v1) in UV space (v up: 0 = bottom of PNG, 1 = top of PNG)
UV_STRAW_SIDE = (0.0 + _P, 0.5 + _P, 0.5 - _P, 1.0 - _P)
UV_STRAW_END = (0.0 + _P, 0.0 + _P, 0.5 - _P, 0.5 - _P)
UV_SILAGE_SIDE = (0.5 + _P, 0.5 + _P, 1.0 - _P, 1.0 - _P)
UV_SILAGE_END = (0.5 + _P, 0.0 + _P, 1.0 - _P, 0.5 - _P)

PROTOS = {}                           # registered only when place() places bales (region C stays untouched)


def prototypes():
    """Currently registered prototypes (populated by place() on rural tiles)."""
    return dict(PROTOS)


def build_prototypes():
    """Return both bale prototypes {(lod0, lod1, col)} directly (for unit tests / tooling)."""
    return {
        PROTO_STRAW: _build_bale(STRAW_D_M, STRAW_L_M, kind="straw"),
        PROTO_SILAGE: _build_bale(SILAGE_D_M, SILAGE_L_M, kind="silage"),
    }


# ------------------------------------------------------------------------------------------------ geometry
def _bale_mesh(diameter, length, kind, lod):
    """Horizontal round bale lying on its side (axis along local x, +z up, resting at z = -SINK_M).

    LOD0: 16 radial x 6 axial rings + 2 end-cap fans = 224 tris (smooth barrel + bevelled/pillow shoulders,
          subtle deterministic organic bulge and flattened ground-contact belly).
    LOD1: 10 radial x 2 axial rings + 2 end-cap fans = 60 tris (36 deg radial step < 38 deg crease angle,
          so crease_normals keeps smooth curved shading at distance).
    """
    m = PP.Mesh()
    r = diameter * 0.5
    hl = length * 0.5
    zc = r - SINK_M
    is_silage = kind == "silage"
    uv_side = UV_SILAGE_SIDE if is_silage else UV_STRAW_SIDE
    uv_end = UV_SILAGE_END if is_silage else UV_STRAW_END

    if lod == 0:
        seg = 16
        if is_silage:
            # Plump pillow-wrapped shoulders (stretch film rounds the corners)
            profile = [
                (-1.00, 0.80, 0.00),
                (-0.92, 0.94, 0.10),
                (-0.78, 1.00, 0.22),
                (0.00, 1.025, 0.50),
                (0.78, 1.00, 0.78),
                (0.92, 0.94, 0.90),
                (1.00, 0.80, 1.00),
            ]
        else:
            # Straw bale: slightly firmer shoulder bevel with gentle barrel swell
            profile = [
                (-1.00, 0.90, 0.00),
                (-0.92, 0.98, 0.08),
                (-0.55, 1.015, 0.28),
                (0.00, 1.025, 0.50),
                (0.55, 1.015, 0.72),
                (0.92, 0.98, 0.92),
                (1.00, 0.90, 1.00),
            ]
    else:
        seg = 10
        r_end = 0.97 if is_silage else 0.985
        profile = [
            (-1.00, r_end, 0.00),
            (0.00, 1.008, 0.50),
            (1.00, r_end, 1.00),
        ]

    # Angle a = 0 at the bottom (-z), sweeping around +y -> +z -> -y -> -z (right-handed around +x):
    # y = sin(a), z = -cos(a) -> (+tangent) x (+x) = outward radial normal (0, sin(a), -cos(a)).
    ang = np.linspace(0.0, 2.0 * math.pi, seg + 1)
    su0, sv0, su1, sv1 = uv_side
    eu0, ev0, eu1, ev1 = uv_end
    euc, evc = 0.5 * (eu0 + eu1), 0.5 * (ev0 + ev1)
    eur, evr = 0.5 * (eu1 - eu0), 0.5 * (ev1 - ev0)

    def _ring_yz(rad, x_norm):
        wobble = 1.0
        if lod == 0:
            ph = 0.7 if is_silage else 2.1
            wobble = 1.0 + (0.014 * np.sin(3.0 * ang + ph + 1.1 * x_norm)
                            + 0.009 * np.cos(2.0 * ang - 0.8 * x_norm))
        yy = rad * wobble * np.sin(ang)
        zz = zc - rad * wobble * np.cos(ang)
        floor_z = -SINK_M
        zz = np.where(zz < floor_z + 0.05, floor_z + 0.35 * np.maximum(zz - floor_z, 0.0), zz)
        return yy, zz

    n_rings = len(profile)
    stride = seg + 1
    Vs, UVs = [], []
    for x_norm, r_fac, v_fac in profile:
        yy, zz = _ring_yz(r * r_fac, x_norm)
        xx = np.full(stride, x_norm * hl)
        Vs.append(np.column_stack([xx, yy, zz]))
        u_vals = su0 + (ang / (2.0 * math.pi)) * (su1 - su0)
        v_vals = np.full(stride, sv0 + v_fac * (sv1 - sv0))
        UVs.append(np.column_stack([u_vals, v_vals]))
    V_side = np.concatenate(Vs, axis=0)
    UV_side = np.concatenate(UVs, axis=0)
    T_side = []
    for ri in range(n_rings - 1):
        b0 = ri * stride
        b1 = (ri + 1) * stride
        for i in range(seg):
            T_side.append((b0 + i, b0 + i + 1, b1 + i + 1))
            T_side.append((b0 + i, b1 + i + 1, b1 + i))
    m.add(MAT, V_side, T_side, UV_side)

    for side_idx, (x_norm, r_fac, _) in ((0, profile[0]), (1, profile[-1])):
        yy, zz = _ring_yz(r * r_fac, x_norm)
        x_end = x_norm * hl
        x_ctr = x_end + (0.025 if side_idx == 1 else -0.025) * (1.0 if is_silage else -0.4) * (1.0 if lod == 0 else 0.0)
        V_cap = np.vstack([[x_ctr, 0.0, zc], np.column_stack([np.full(seg, x_end), yy[:-1], zz[:-1]])])
        a_cap = ang[:-1]
        u_cap = euc + eur * np.sin(a_cap) * (1.0 if side_idx == 1 else -1.0)
        v_cap = evc - evr * np.cos(a_cap)
        UV_cap = np.vstack([[euc, evc], np.column_stack([u_cap, v_cap])])
        if side_idx == 1:
            T_cap = [(0, 1 + i, 1 + (i + 1) % seg) for i in range(seg)]
        else:
            T_cap = [(0, 1 + (i + 1) % seg, 1 + i) for i in range(seg)]
        m.add(MAT, V_cap, T_cap, UV_cap)
    return m


def _build_bale(diameter, length, kind):
    lod0 = _bale_mesh(diameter, length, kind, lod=0)
    lod1 = _bale_mesh(diameter, length, kind, lod=1)
    col = PP.Mesh()
    r = diameter * 0.5
    col.tube("collision_steel", [-length * 0.5, 0.0, r - SINK_M], [length * 0.5, 0.0, r - SINK_M], r * 0.95, None, 6)
    return lod0, lod1, col


# ------------------------------------------------------------------------------------------------ texture atlas
def _smooth_noise(rng, h, w, sx, sy):
    a = rng.normal(0.0, 1.0, (h, w))
    b = gaussian_filter(a, sigma=(sy, sx), mode="wrap")
    std = float(b.std())
    return b / std if std > 1e-9 else b


def _straw_side_tile(n, rng):
    """Golden weathered straw bale side: crisp overlapping stalks, baling twine rings, subtle bottom AO."""
    # Render at 2x supersampled resolution so individual straw stalks stay crisp and anti-aliased
    s = n * 2
    base = np.array([152.0, 125.0, 74.0])
    # Subtle large-scale golden/weathered variation under the stalks
    bg_var = _smooth_noise(rng, s, s, sx=28.0, sy=18.0) * 14.0
    bg = np.clip(base[None, None, :] + bg_var[..., None], 0, 255).astype(np.uint8)
    im = Image.fromarray(bg, "RGB")
    draw = ImageDraw.Draw(im)

    # Dense overlapping individual straw stalks wrapping circumferentially (u = x in image)
    palette = (
        (114, 88, 48),   # deep recessed straw shadow
        (138, 110, 62),  # dark ochre stalk
        (164, 134, 78),  # mid golden wheat
        (184, 154, 94),  # sunlit golden straw
        (202, 174, 112), # pale dry wheat/barley stalk
        (216, 190, 130), # highlight oat/barley fibre
    )
    weights = np.array([0.14, 0.18, 0.24, 0.22, 0.14, 0.08])
    n_stalks = 4200
    xs = rng.uniform(0.0, s, n_stalks)
    ys = rng.uniform(0.0, s, n_stalks)
    lens = rng.uniform(20.0, 68.0, n_stalks)
    angs = rng.normal(0.0, 0.14, n_stalks)        # mostly circumferential, organic criss-cross ±8 deg
    cidx = rng.choice(len(palette), size=n_stalks, p=weights)
    wds = rng.choice([1, 2, 2, 3], size=n_stalks)
    for x0, y0, ln, a, ci, wd in zip(xs, ys, lens, angs, cidx, wds):
        dx = ln * math.cos(a)
        dy = ln * math.sin(a)
        col = palette[int(ci)]
        # Wrap horizontally across u seam so the cylinder has no seam line
        for ox in (0.0, -s, s):
            xa, xb = x0 + ox, x0 + dx + ox
            if xb >= 0.0 and xa <= s:
                draw.line([(xa, y0), (xb, y0 + dy)], fill=col, width=int(wd))

    rgb = np.asarray(im.resize((n, n), Image.Resampling.LANCZOS), np.float64)
    u = np.linspace(0.0, 1.0, n, endpoint=False)[None, :]
    v = np.linspace(1.0, 0.0, n, endpoint=False)[:, None]

    # Taut baling twine / net-wrap circumferential bands (5 narrow recessed grooves + pale cord)
    for tv in (0.13, 0.31, 0.50, 0.69, 0.87):
        d = np.abs(v - tv)
        groove = np.exp(-((d / 0.015) ** 2))
        cord = np.exp(-((d / 0.005) ** 2))
        rgb = rgb * (1.0 - 0.24 * groove[..., None]) + np.array([212.0, 202.0, 168.0])[None, None, :] * (0.34 * cord[..., None])

    # Subtle diagonal net-wrap threads (low contrast: visible close up, zero moire at distance)
    net = 0.5 + 0.5 * np.sin((u * 32.0 + v * 10.0) * 2.0 * math.pi)
    net = (net > 0.93).astype(np.float64) * 0.05
    rgb = rgb * (1.0 - net[..., None]) + np.array([212.0, 206.0, 188.0])[None, None, :] * net[..., None]

    # Shoulder edge darkening (v near 0, 1) and ground-contact AO + soil smudge (u near 0, 1 = bottom belly)
    edge_v = np.exp(-((np.minimum(v, 1.0 - v) / 0.065) ** 2))
    bottom_u = np.exp(-((np.minimum(u, 1.0 - u) / 0.14) ** 2))
    ao = 1.0 - 0.12 * edge_v - 0.30 * bottom_u
    dirt = np.array([96.0, 78.0, 50.0])[None, None, :]
    rgb = rgb * ao[..., None] * (1.0 - 0.22 * bottom_u[..., None]) + dirt * (0.22 * bottom_u[..., None])
    return np.clip(rgb, 0, 255).astype(np.uint8)


def _straw_end_tile(n, rng):
    """Flat circular end of a straw bale: tangentially wound dense straw stalks with natural subtle spiral tone."""
    s = n * 2
    cx, cy = s * 0.5, s * 0.5
    xs = np.linspace(-1.0, 1.0, s)[None, :]
    ys = np.linspace(1.0, -1.0, s)[:, None]
    r = np.hypot(xs, ys)
    ang = np.arctan2(ys, xs)

    # Soft natural spiral tonal flow (low contrast so it reads as real layered straw, never a drawn bullseye)
    wob = _smooth_noise(rng, s, s, sx=20.0, sy=20.0) * 0.9
    spiral = np.sin(r * 5.5 * 2.0 * math.pi + ang + wob)
    base = np.array([142.0, 114.0, 66.0])[None, None, :]
    bg = base * (1.0 + 0.08 * spiral)[..., None]
    im = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8), "RGB")
    draw = ImageDraw.Draw(im)

    # ~3,400 short compressed straw stalks oriented tangentially around the centre
    palette = (
        (98, 75, 40),
        (124, 98, 54),
        (150, 122, 70),
        (172, 142, 84),
        (192, 164, 104),
    )
    weights = np.array([0.16, 0.24, 0.26, 0.22, 0.12])
    n_stalks = 3400
    rr = np.sqrt(rng.uniform(0.0, 1.35, n_stalks)) * (s * 0.52)
    th = rng.uniform(0.0, 2.0 * math.pi, n_stalks)
    ln = rng.uniform(10.0, 32.0, n_stalks)
    da = rng.normal(0.0, 0.26, n_stalks)
    cidx = rng.choice(len(palette), size=n_stalks, p=weights)
    wds = rng.choice([1, 2, 2], size=n_stalks)
    for rad, t, l_, d_, ci, wd in zip(rr, th, ln, da, cidx, wds):
        px = cx + rad * math.cos(t)
        py = cy - rad * math.sin(t)
        # Tangential direction (+ subtle inward spiral angle)
        ta = t + math.pi * 0.5 + d_
        hx, hy = 0.5 * l_ * math.cos(ta), -0.5 * l_ * math.sin(ta)
        draw.line([(px - hx, py - hy), (px + hx, py + hy)], fill=palette[int(ci)], width=int(wd))

    rgb = np.asarray(im.resize((n, n), Image.Resampling.LANCZOS), np.float64)
    xn = np.linspace(-1.0, 1.0, n)[None, :]
    yn = np.linspace(1.0, -1.0, n)[:, None]
    rn = np.hypot(xn, yn)
    core_ao = 1.0 - 0.18 * np.exp(-((rn / 0.24) ** 2))
    rim_bright = 1.0 + 0.07 * np.clip((rn - 0.72) / 0.28, 0.0, 1.0)
    bottom_ao = 1.0 - 0.28 * np.clip((-yn - 0.45) / 0.55, 0.0, 1.0)
    rgb = rgb * (core_ao * rim_bright * bottom_ao)[..., None]
    return np.clip(rgb, 0, 255).astype(np.uint8)


def _silage_side_tile(n, rng):
    """Off-white agricultural stretch-film silage wrap: soft overlapping film bands, creases, gentle bottom dust."""
    u = np.linspace(0.0, 1.0, n, endpoint=False)[None, :]
    v = np.linspace(1.0, 0.0, n, endpoint=False)[:, None]

    # Off-white slightly warm-sage stretch film (linear ~0.62: stands out clearly on green meadows without clipping)
    base = np.array([214.0, 217.0, 207.0])[None, None, :]

    # Smooth overlapping stretch-film bands (5 wrap passes across the bale with soft translucent step lines)
    wob = 0.06 * np.sin(u * 2.0 * math.pi + 0.8) + 0.03 * np.cos(u * 4.0 * math.pi - 0.4)
    phase = (v * 5.0 + wob) % 1.0
    # Soft sawtooth shade across each overlapping film edge (light lip + delicate shadow right next to overlap)
    overlap_shade = (phase - 0.5) * 0.032 - 0.035 * np.exp(-((phase / 0.055) ** 2))
    # Organic compacted-grass pillow bulges + delicate circumferential stretch tension folds
    lumps = _smooth_noise(rng, n, n, sx=20.0, sy=16.0)
    folds = _smooth_noise(rng, n, n, sx=28.0, sy=2.8)
    fine = _smooth_noise(rng, n, n, sx=5.0, sy=5.0)

    shade = 1.0 + overlap_shade + 0.026 * lumps + 0.018 * folds + 0.008 * fine
    rgb = base * shade[..., None]
    # Very faint cool-sage undertone where extra wrap layers overlap
    lip = np.exp(-((phase / 0.07) ** 2))
    rgb = rgb * (1.0 - 0.05 * lip[..., None]) + np.array([182.0, 192.0, 174.0])[None, None, :] * (0.05 * lip[..., None])

    # Gentle shoulder tuck shading (v near 0, 1) and meadow dust/grass smudge only along ground contact (u near 0, 1)
    edge_v = np.exp(-((np.minimum(v, 1.0 - v) / 0.075) ** 2))
    bottom_u = np.exp(-((np.minimum(u, 1.0 - u) / 0.11) ** 2))
    dust_var = 0.65 + 0.35 * np.clip(_smooth_noise(rng, n, n, sx=12.0, sy=12.0), -1.0, 1.0)
    dust = np.clip(bottom_u * dust_var * 0.32, 0.0, 0.35)
    rgb = rgb * (1.0 - 0.06 * edge_v[..., None]) * (1.0 - dust[..., None]) + np.array([128.0, 126.0, 102.0])[None, None, :] * dust[..., None]
    return np.clip(rgb, 0, 255).astype(np.uint8)


def _silage_end_tile(n, rng):
    """Flat circular end of a wrapped silage bale: overlapping rotated stretch-film bands & subtle edge creases."""
    xs = np.linspace(-1.0, 1.0, n)[None, :]
    ys = np.linspace(1.0, -1.0, n)[:, None]
    r = np.hypot(xs, ys)
    ang = np.arctan2(ys, xs)

    base = np.array([208.0, 212.0, 202.0])[None, None, :]
    # 5 rotated overlapping stretch-film bands crossing the flat circular end (organic edge wobble)
    wob = _smooth_noise(rng, n, n, sx=18.0, sy=18.0) * 0.035
    layer_count = np.zeros((n, n), np.float64)
    edge_lines = np.zeros((n, n), np.float64)
    for k in range(5):
        a = k * math.pi / 5.0 + 0.25 + 0.06 * math.sin(k * 2.3)
        d = np.abs(xs * math.cos(a) + ys * math.sin(a) + wob)
        band_hw = 0.34 + 0.02 * math.cos(k * 1.7)
        layer_count += (d < band_hw).astype(np.float64)
        edge_lines = np.maximum(edge_lines, np.exp(-(((d - band_hw) / 0.028) ** 2)))

    # Soft radial tension pleats near the outer rim where film bends over the shoulder
    pleats = np.sin(ang * 10.0 + 0.5 * r) * np.clip((r - 0.45) / 0.55, 0.0, 1.0)
    lumps = _smooth_noise(rng, n, n, sx=16.0, sy=16.0)
    fine = _smooth_noise(rng, n, n, sx=5.0, sy=5.0)

    shade = 1.0 + 0.012 * (layer_count - 2.0) - 0.022 * edge_lines - 0.018 * np.abs(pleats) + 0.026 * lumps + 0.008 * fine
    rim_ao = 1.0 - 0.08 * np.clip((r - 0.74) / 0.26, 0.0, 1.0)
    bottom_ao = 1.0 - 0.22 * np.clip((-ys - 0.55) / 0.45, 0.0, 1.0)
    rgb = base * (shade * rim_ao * bottom_ao)[..., None]
    dust = np.clip((-ys - 0.65) / 0.35, 0.0, 1.0) * 0.26
    rgb = rgb * (1.0 - dust[..., None]) + np.array([128.0, 126.0, 102.0])[None, None, :] * dust[..., None]
    return np.clip(rgb, 0, 255).astype(np.uint8)


def _pad_quadrant(tile, q):
    """Place a (q - 2*pad) tile inside a (q x q) quadrant with edge-replicated bleed padding (ASTC / mip safe)."""
    pad = ATLAS_PAD_PX
    inner = q - 2 * pad
    im = Image.fromarray(tile, "RGB").resize((inner, inner), Image.Resampling.LANCZOS)
    arr = np.asarray(im, np.uint8)
    return np.pad(arr, ((pad, pad), (pad, pad), (0, 0)), mode="edge")


def atlas_image():
    """Generate the shared 512 x 512 sRGB atlas (`field_bale_atlas.png`) for both bale prototypes."""
    q = ATLAS_SIZE // 2
    rng = np.random.default_rng(346)
    canvas = np.zeros((ATLAS_SIZE, ATLAS_SIZE, 3), np.uint8)
    # Top row in PNG = v in [0.5, 1.0]: side wraps (left = straw, right = silage)
    canvas[:q, :q] = _pad_quadrant(_straw_side_tile(q, rng), q)
    canvas[:q, q:] = _pad_quadrant(_silage_side_tile(q, rng), q)
    # Bottom row in PNG = v in [0.0, 0.5]: circular end caps (left = straw, right = silage)
    canvas[q:, :q] = _pad_quadrant(_straw_end_tile(q, rng), q)
    canvas[q:, q:] = _pad_quadrant(_silage_end_tile(q, rng), q)
    return Image.fromarray(canvas, "RGB")


def textures():
    return {ATLAS_NAME: atlas_image()}


# ------------------------------------------------------------------------------------------------ placement
def _slope_ok(Q, hf, zc):
    """True for points where local terrain slope <= MAX_SLOPE."""
    H, W = zc.shape
    i = np.clip(np.rint(Q[:, 0] - hf.x0).astype(int), 1, W - 2)
    j = np.clip(np.rint(hf.y1 - Q[:, 1]).astype(int), 1, H - 2)
    gx = 0.5 * (zc[j, i + 1] - zc[j, i - 1])
    gy = 0.5 * (zc[j - 1, i] - zc[j + 1, i])
    return np.hypot(gx, gy) <= MAX_SLOPE


def plan_bales(src, origin, hf, zc=None, blocked=None, road_dist=None, trees=()):
    """Deterministic list of bale records `{"p", "e", "n", "z", "yaw", "src"}` on rural farmland strips.

    Pure function of the EPSG:2180 ADR 0334 mosaic (`vegetation.field_layout` / `field_use`) and BDOT10k
    OT_PTTR_A polygons >= MIN_POLY_M2: two neighbouring tiles agree along their seam.
    """
    feats = (src.get("bdot10k") or {}).get("OT_PTTR_A") or []
    if not feats:
        return []
    polys = {r: [] for r in VG.FIELD_FLAG_B}
    for f in feats:
        r = (f.get("props") or {}).get("rodzaj")
        if r in polys:
            g = shapely.make_valid(PV._poly_local(f["geometry"]["coordinates"], origin))
            if g.area >= MIN_POLY_M2:
                polys[r].append(g)
    areas = {r: shapely.union_all(p) if p else shapely.Polygon() for r, p in polys.items()}
    arable_area = areas["uprawa na gruntach ornych"]
    grass_area = areas["roślinność trawiasta"]
    all_area = shapely.union_all([g for g in (arable_area, grass_area) if not g.is_empty])
    if all_area.is_empty:
        return []
    inner_arable = arable_area.buffer(-POLY_MARGIN_M) if not arable_area.is_empty else shapely.Polygon()
    inner_grass = grass_area.buffer(-POLY_MARGIN_M) if not grass_area.is_empty else shapely.Polygon()
    if inner_arable.is_empty and inner_grass.is_empty:
        return []
    shapely.prepare(inner_arable)
    shapely.prepare(inner_grass)

    H, W = hf.z.shape
    x0, y1 = hf.x0, hf.y1
    ox, oy = float(origin[0]), float(origin[1])

    # Discover all mosaic strips intersecting the tile's farmland on an EPSG:2180-aligned 8 m lattice
    # (every strip is >= 16 m wide, so 8 m hits every strip at any rotation and is 100 % tile-seam invariant).
    step = 8.0
    gx0 = math.floor((x0 + ox - 48.0) / step) * step - ox
    gy0 = math.floor((y1 - H + oy - 48.0) / step) * step - oy
    gx, gy = np.meshgrid(np.arange(gx0, x0 + W + 48.0, step),
                         np.arange(gy0, y1 + 48.0, step))
    G = np.column_stack([gx.ravel(), gy.ravel()])
    in_a = shapely.contains_xy(arable_area, G[:, 0], G[:, 1]) if not arable_area.is_empty else np.zeros(len(G), bool)
    in_g = shapely.contains_xy(grass_area, G[:, 0], G[:, 1]) if not grass_area.is_empty else np.zeros(len(G), bool)
    if not (in_a | in_g).any():
        return []

    cand = []  # (qx_abs, qy_abs, proto, yaw, arable_flag, tag)
    for is_arable, mask_g in ((True, in_a), (False, in_g & ~in_a)):
        P = G[mask_g]
        if not len(P):
            continue
        L = VG.field_layout(P[:, 0] + ox, P[:, 1] + oy)
        uses = VG.field_use(L, is_arable)
        strips = {}
        for i in range(len(P)):
            uname = VG.FIELD_USES[int(uses[i])]
            if uname not in USE_STRIP_SHARE:
                continue
            fid = int(L["fid"][i])
            rec = strips.get(fid)
            al = float(L["along"][i])
            if rec is None:
                strips[fid] = [int(L["bid"][i]), int(L["k"][i]), float(L["th"][i]), float(L["w"][i]),
                               float(L["sx"][i]), float(L["sy"][i]), uname, al, al]
            else:
                if al < rec[7]:
                    rec[7] = al
                if al > rec[8]:
                    rec[8] = al

        for fid in sorted(strips):
            bid, k_idx, th, w, sx, sy, uname, s_min, s_max = strips[fid]
            u_sel = float(VG._u01(VG._h32(np.array([fid]), np.array([0]), 981))[0])
            if u_sel >= USE_STRIP_SHARE[uname]:
                continue
            proto = USE_PROTO[uname]
            u_pat = float(VG._u01(VG._h32(np.array([fid]), np.array([0]), 983))[0])
            is_row = u_pat < ROW_PATTERN_SHARE[proto]
            ct, st = math.cos(th), math.sin(th)
            # In props frame, local +x is the bale cylinder axis; yaw = th puts cylinder axis along +across
            # (perpendicular to baler travel along the strip).
            base_yaw = th
            if is_row:
                if w < 25.0:
                    tracks = [0.5 * w]
                else:
                    off = min(0.28 * w, 7.5)
                    tracks = [0.5 * w - off, 0.5 * w + off]
                seg0 = int(math.floor((s_min - ROW_SEG_M) / ROW_SEG_M))
                seg1 = int(math.ceil((s_max + ROW_SEG_M) / ROW_SEG_M))
                for ti, tr_across in enumerate(tracks):
                    for seg in range(seg0, seg1 + 1):
                        if float(VG._u01(VG._h32(np.array([fid]), np.array([seg * 7 + ti]), 985))[0]) >= ROW_SEG_KEEP:
                            continue
                        n_cells = max(1, int(ROW_SEG_M // ROW_STEP_M))
                        for ci in range(n_cells):
                            cid = seg * 31 + ci * 3 + ti
                            if float(VG._u01(VG._h32(np.array([fid]), np.array([cid]), 987))[0]) < 0.25:
                                continue
                            ja = (float(VG._u01(VG._h32(np.array([fid]), np.array([cid]), 989))[0]) - 0.5) * 2.0 * ROW_JITTER_ALONG_M
                            jc = (float(VG._u01(VG._h32(np.array([fid]), np.array([cid]), 991))[0]) - 0.5) * 2.0 * ROW_JITTER_ACROSS_M
                            jy = (float(VG._u01(VG._h32(np.array([fid]), np.array([cid]), 993))[0]) - 0.5) * 0.32
                            s_val = seg * ROW_SEG_M + (ci + 0.5) * ROW_STEP_M + ja
                            ac = min(max(tr_across + jc, STRIP_EDGE_CLEAR_M), w - STRIP_EDGE_CLEAR_M)
                            n_coord = k_idx * w + ac
                            qx = sx + n_coord * ct - s_val * st
                            qy = sy + n_coord * st + s_val * ct
                            cand.append((qx, qy, proto, base_yaw + jy, is_arable, f"bale:row:{uname}"))
            else:
                side_hi = float(VG._u01(VG._h32(np.array([fid]), np.array([1]), 995))[0]) < 0.5
                ac_base = (w - STRIP_EDGE_CLEAR_M - 1.2) if side_hi else (STRIP_EDGE_CLEAR_M + 1.2)
                seg0 = int(math.floor((s_min - GROUP_SEG_M) / GROUP_SEG_M))
                seg1 = int(math.ceil((s_max + GROUP_SEG_M) / GROUP_SEG_M))
                pitch = (STRAW_D_M if proto == PROTO_STRAW else SILAGE_D_M) + GROUP_GAP_M
                for seg in range(seg0, seg1 + 1):
                    if float(VG._u01(VG._h32(np.array([fid]), np.array([seg]), 997))[0]) >= GROUP_SEG_KEEP:
                        continue
                    u_n = float(VG._u01(VG._h32(np.array([fid]), np.array([seg]), 999))[0])
                    n_grp = GROUP_SIZE[0] + int(u_n * (GROUP_SIZE[1] - GROUP_SIZE[0] + 1))
                    n_grp = min(n_grp, GROUP_SIZE[1])
                    s_anchor = (seg + 0.25 + 0.50 * float(VG._u01(VG._h32(np.array([fid]), np.array([seg]), 1001))[0])) * GROUP_SEG_M
                    for bi in range(n_grp):
                        bid_key = seg * 17 + bi
                        ja = (float(VG._u01(VG._h32(np.array([fid]), np.array([bid_key]), 1003))[0]) - 0.5) * 0.28
                        jc = (float(VG._u01(VG._h32(np.array([fid]), np.array([bid_key]), 1005))[0]) - 0.5) * 0.24
                        jy = (float(VG._u01(VG._h32(np.array([fid]), np.array([bid_key]), 1007))[0]) - 0.5) * 0.18
                        s_val = s_anchor + (bi - 0.5 * (n_grp - 1)) * pitch + ja
                        n_coord = k_idx * w + ac_base + jc
                        qx = sx + n_coord * ct - s_val * st
                        qy = sy + n_coord * st + s_val * ct
                        cand.append((qx, qy, proto, base_yaw + jy, is_arable, f"bale:edge:{uname}"))

    if not cand:
        return []

    Q_abs = np.array([[c[0], c[1]] for c in cand], np.float64)
    Q = np.column_stack([Q_abs[:, 0] - ox, Q_abs[:, 1] - oy])
    is_ar = np.array([c[4] for c in cand], bool)

    ok = (Q[:, 0] >= x0) & (Q[:, 0] < x0 + W - 1) & (Q[:, 1] <= y1) & (Q[:, 1] > y1 - H + 1)
    if not ok.any():
        return []

    in_poly = np.zeros(len(Q), bool)
    if ok.any() and not inner_arable.is_empty:
        ma = ok & is_ar
        if ma.any():
            in_poly[ma] = shapely.contains_xy(inner_arable, Q[ma, 0], Q[ma, 1])
    if ok.any() and not inner_grass.is_empty:
        mg = ok & ~is_ar
        if mg.any():
            in_poly[mg] = shapely.contains_xy(inner_grass, Q[mg, 0], Q[mg, 1])
    ok &= in_poly
    if not ok.any():
        return []

    Lq = VG.field_layout(Q_abs[ok, 0], Q_abs[ok, 1])
    uq = VG.field_use(Lq, is_ar[ok])
    edge_ok = (Lq["block_edge"] >= BLOCK_EDGE_CLEAR_M) & (np.minimum(Lq["across"], Lq["w"] - Lq["across"]) >= STRIP_EDGE_CLEAR_M)
    use_ok = np.array([VG.FIELD_USES[int(u)] in USE_STRIP_SHARE and USE_PROTO[VG.FIELD_USES[int(u)]] == cand[idx][2]
                       for idx, u in zip(np.flatnonzero(ok), uq)], bool)
    idx_ok = np.flatnonzero(ok)
    ok[idx_ok] = edge_ok & use_ok
    if not ok.any():
        return []

    idx_ok = np.flatnonzero(ok)
    Qi = Q[idx_ok]
    ii = np.clip(np.rint(Qi[:, 0] - x0).astype(int), 0, W - 1)
    jj = np.clip(np.rint(y1 - Qi[:, 1]).astype(int), 0, H - 1)
    keep = np.ones(len(idx_ok), bool)
    if blocked is not None:
        keep &= ~blocked[jj, ii]
    if road_dist is not None:
        keep &= road_dist[jj, ii] > ROAD_CLEAR_M
    if zc is not None:
        keep &= _slope_ok(Qi, hf, zc)
    if trees and keep.any():
        from scipy.spatial import cKDTree
        tpts = np.array([[t["e"], t["n"]] for t in trees], np.float64)
        dk, _ = cKDTree(tpts).query(Qi[keep])
        sub = np.flatnonzero(keep)
        keep[sub] = dk >= TREE_CLEAR_M
    idx_ok = idx_ok[keep]
    if not len(idx_ok):
        return []

    Qf = Q[idx_ok]
    if len(Qf) > 1:
        from scipy.spatial import cKDTree
        kd = cKDTree(Qf)
        drop = np.zeros(len(Qf), bool)
        for a, b in sorted(kd.query_pairs(1.5)):
            if not drop[a] and not drop[b]:
                drop[b] = True
        idx_ok = idx_ok[~drop]

    zgrid = zc if zc is not None else hf.z
    Qf = Q[idx_ok]
    zs = PV.bilinear(zgrid, hf, Qf[:, 0], Qf[:, 1])
    out = []
    for k, zval in zip(idx_ok, zs):
        _, _, proto, yaw, _, tag = cand[k]
        yaw_norm = float(yaw % (2.0 * math.pi))
        out.append({
            "p": proto,
            "e": round(float(Q[k, 0]), 2),
            "n": round(float(Q[k, 1]), 2),
            "z": round(float(zval), 2),
            "yaw": round(yaw_norm, 3),
            "src": tag,
        })
    return out


def place(src, origin, hf, zc, blocked, report, trees=(), enabled=True):
    """Place field bales on rural tiles, registering prototypes into PROTOS only when used."""
    PROTOS.clear()
    if not enabled:
        report["field_bales"] = {"enabled": False, "straw": 0, "silage": 0, "row": 0, "edge": 0}
        return []
    from scipy import ndimage as _ndi
    road_dist = _ndi.distance_transform_edt(~blocked) if blocked is not None and blocked.any() else None
    items = plan_bales(src, origin, hf, zc=zc, blocked=blocked, road_dist=road_dist, trees=trees)
    used = {it["p"] for it in items}
    if used:
        built = build_prototypes()
        for name in sorted(used):
            PROTOS[name] = built[name]
    report["field_bales"] = {
        "enabled": True,
        "straw": sum(1 for it in items if it["p"] == PROTO_STRAW),
        "silage": sum(1 for it in items if it["p"] == PROTO_SILAGE),
        "row": sum(1 for it in items if it["src"].startswith("bale:row:")),
        "edge": sum(1 for it in items if it["src"].startswith("bale:edge:")),
    }
    return items
