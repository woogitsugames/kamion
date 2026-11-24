"""Procedural windscreen dirt mask for Kamion/Truck Glass (ADR 0341, windscreen-s24).

Output: game/Assets/_Project/Rendering/Textures/Truck/T_Windscreen_Grime.png (RGB, linear data, 2048 x 1024).
The texture is mapped in the windscreen OBJECT space (glass object xy = cab frame x right, y up; the pane is 1.5 deg from
vertical, so the xy projection is undistorted): uv = (p.xy - RECT_MIN) / RECT_SIZE, the same rectangle as the material
vector _GrimeRect written by TruckAssetBuilder. 1 texel = 1.27 mm (driver eye ~1 m away: 1 px at 1080p / FOV 70 deg ~ 1.1 mm).

Channels (all 0..1, summer truck on the road, a few days after the last wash - WORKING_VALUE):
  R  dust / dried road film that SCATTERS light (veiling glare against the sun, faint grey against a dark background):
     edge accumulation along the glass border (spray rises at the bottom edge, the seals catch dust), a thin patchy film in
     the areas the blades do not reach, the ragged ridge of dirt the blade leaves at the end of its sweep.
  G  wiper streaks: thin concentric arcs of residual film inside the two sweeps (worn blade edge). Invisible in diffuse
     light, they only light up against a low sun (the shader uses G only with the forward-scatter phase).
  B  insect remains: small opaque splats (1-3 mm core, lighter halo), smeared along the arc inside the sweeps.
Design rule from the s24 drive review #11: NO broad smooth zones - a large soft film read as "smoke columns" from the seat.
Everything here is high-frequency (mm to a few cm) and concentrated near edges; coverage is checked at the end
(critic s24 build5 #6: 3-6 % of the pane).

Wiper geometry = the glass material contract (_WiperPivotA/B, _WiperSweep in TruckAssetBuilder, from the exterior
manifest WIPER_L/R): pivots (-1.00, 0.87) and (-0.08, 0.87), blade radii 0.18-0.95 m, sweep -5..100 deg from +X.

Run:  uv run --no-project --with numpy --with pillow python tools/rendering/windscreen_grime.py [--seed 341] [--stats]
"""
from __future__ import annotations

import argparse
import json
import math
import os

import numpy as np
from PIL import Image

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(REPO, "game", "Assets", "_Project", "Rendering", "Textures", "Truck", "T_Windscreen_Grime.png")
W, H = 2048, 1024
RECT_MIN = (-1.30, 0.75)
RECT_SIZE = (2.60, 1.30)
PIVOTS = ((-1.00, 0.87), (-0.08, 0.87))
R_IN, R_OUT = 0.18, 0.95
SWEEP = (-5.0, 100.0)
# Visible glass (glass_interface.json: bottom edge y 0.778 half width 1.25, top ~1.98 half width 1.16, cab frame).
GLASS_Y = (0.80, 1.97)
GLASS_HALF_W = (1.20, 1.12)


def grid():
    xs = RECT_MIN[0] + (np.arange(W) + 0.5) / W * RECT_SIZE[0]
    ys = RECT_MIN[1] + (np.arange(H) + 0.5) / H * RECT_SIZE[1]
    return np.meshgrid(xs, ys)          # row 0 = bottom (y min); flipped when saved (PNG row 0 = top = v 1)


def value_noise(rng, cell_m, x, y):
    """Smooth value noise with cells of cell_m metres (bilinear on a random lattice, smoothstep weights)."""
    gx = (x - RECT_MIN[0]) / cell_m
    gy = (y - RECT_MIN[1]) / cell_m
    nx, ny = int(gx.max()) + 3, int(gy.max()) + 3
    lat = rng.random((ny, nx)).astype(np.float32)
    ix, iy = np.floor(gx).astype(int), np.floor(gy).astype(int)
    fx, fy = gx - ix, gy - iy
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b = lat[iy, ix], lat[iy, ix + 1]
    c, d = lat[iy + 1, ix], lat[iy + 1, ix + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def fbm(rng, x, y, cells):
    acc, wsum = 0.0, 0.0
    for i, c in enumerate(cells):
        w = 0.55 ** i
        acc = acc + w * value_noise(rng, c, x, y)
        wsum += w
    return acc / wsum


def sweep_mask(x, y, soft=0.03, soft_deg=4.0):
    """1 inside either wiper sweep, 0 outside; also polar coordinates of the nearer pivot (for arcs)."""
    best = np.zeros_like(x)
    rr = np.full_like(x, 9.0)
    aa = np.zeros_like(x)
    which = np.zeros(x.shape, np.int8)
    for k, (px, py) in enumerate(PIVOTS):
        dx, dy = x - px, y - py
        r = np.hypot(dx, dy)
        a = np.degrees(np.arctan2(dy, dx))
        s = lambda e0, e1, v: np.clip((v - e0) / (e1 - e0), 0, 1)
        inr = s(R_IN - soft, R_IN + soft, r) * (1 - s(R_OUT - soft, R_OUT + soft, r))
        ina = s(SWEEP[0] - soft_deg, SWEEP[0] + soft_deg, a) * (1 - s(SWEEP[1] - soft_deg, SWEEP[1] + soft_deg, a))
        m = inr * ina
        take = m > best
        best = np.where(take, m, best)
        rr = np.where(take, r, rr)
        aa = np.where(take, a, aa)
        which = np.where(take, k, which)
    return best, rr, aa, which


def edge_distance(x, y):
    """Distance (m) to the nearest edge of the visible glass trapezoid (negative outside)."""
    t = np.clip((y - GLASS_Y[0]) / (GLASS_Y[1] - GLASS_Y[0]), 0, 1)
    hw = GLASS_HALF_W[0] + (GLASS_HALF_W[1] - GLASS_HALF_W[0]) * t
    return np.minimum(np.minimum(y - GLASS_Y[0], GLASS_Y[1] - y), hw - np.abs(x))


def splat(img, cx, cy, rx, ry, ang, amp, halo=0.0):
    """Add an elliptical splat (metres) with a hard-ish core and an optional faint halo (max blend)."""
    u0 = (cx - RECT_MIN[0]) / RECT_SIZE[0] * W
    v0 = (cy - RECT_MIN[1]) / RECT_SIZE[1] * H
    ext = max(rx, ry) * (3.0 if halo > 0 else 1.6)
    pu, pv = ext / RECT_SIZE[0] * W, ext / RECT_SIZE[1] * H
    i0, i1 = max(int(u0 - pu) - 1, 0), min(int(u0 + pu) + 2, W)
    j0, j1 = max(int(v0 - pv) - 1, 0), min(int(v0 + pv) + 2, H)
    if i0 >= i1 or j0 >= j1:
        return
    xs = RECT_MIN[0] + (np.arange(i0, i1) + 0.5) / W * RECT_SIZE[0]
    ys = RECT_MIN[1] + (np.arange(j0, j1) + 0.5) / H * RECT_SIZE[1]
    X, Y = np.meshgrid(xs, ys)
    c, s = math.cos(ang), math.sin(ang)
    du, dv = (X - cx) * c + (Y - cy) * s, -(X - cx) * s + (Y - cy) * c
    d = np.sqrt((du / rx) ** 2 + (dv / ry) ** 2)
    core = np.clip(1.4 - d, 0, 1) ** 0.7
    val = amp * core
    if halo > 0:
        val = np.maximum(val, amp * halo * np.clip(1 - d / 3.0, 0, 1) ** 2)
    img[j0:j1, i0:i1] = np.maximum(img[j0:j1, i0:i1], val)


def build(seed: int):
    rng = np.random.default_rng(seed)
    x, y = grid()
    wiped, r, a, which = sweep_mask(x, y)
    e = edge_distance(x, y)
    on_glass = (e > -0.01).astype(np.float32)
    hgt = np.clip((y - GLASS_Y[0]) / (GLASS_Y[1] - GLASS_Y[0]), 0, 1)

    # ---- R: dust that scatters ----
    fine = fbm(rng, x, y, (0.006, 0.003, 0.0015))          # mm-scale grain of dried spray
    patch = fbm(rng, x, y, (0.05, 0.02, 0.01))               # 1-5 cm patches (never larger: no smooth zones)
    speck = (fine > 0.62).astype(np.float32) * (fine - 0.62) / 0.38
    # border accumulation: rubber seal + spray rising at the bottom edge (3-4 cm), sides ~2 cm, top ~1.5 cm
    reach = np.where(y < 1.0, 0.022, 0.010) * (0.5 + 0.9 * patch)
    edge = np.exp(-np.maximum(e, 0) / reach) * np.clip(fine * 1.6 - 0.3, 0, 1)
    edge *= np.where(hgt < 0.15, 1.0, 0.55)
    # unwiped areas (corners, right edge, the strip between the sweeps at the top): thin, patchy, speckled film
    unwiped = (1 - wiped) * (0.10 * (patch > 0.55) * (patch - 0.55) / 0.45 + 0.20 * speck)
    unwiped *= np.clip(1.0 - np.maximum(e - 0.12, 0) / 0.25, 0.25, 1.0)   # fades away from the border, never a column
    # the blade end ridge: dirt pushed to the end of the sweep, ragged and broken
    ridge = np.zeros_like(x)
    for k, (px, py) in enumerate(PIVOTS):
        dx, dy = x - px, y - py
        rk = np.hypot(dx, dy)
        ak = np.degrees(np.arctan2(dy, dx))
        breaks = (value_noise(rng, 0.03, x, y) > 0.35).astype(np.float32)
        wob = (value_noise(rng, 0.08, x, y) - 0.5) * 3.0           # +-1.5 deg wobble
        # no reversal line at the end of the stroke: a near-vertical ridge read as a column in the sky (ADR 0080 r11)
        outer_arc = np.exp(-((rk - (R_OUT + 0.012 + wob * 0.004)) / 0.0045) ** 2) * (ak > SWEEP[0]) * (ak < SWEEP[1])
        ridge = np.maximum(ridge, (0.08 * outer_arc) * breaks * (0.5 + 0.5 * fine))
    wiped_film = wiped * 0.03 * speck                                # the blade never leaves the glass perfectly clean
    R = np.clip(edge * 0.55 + unwiped + ridge + wiped_film, 0, 1) * on_glass

    # ---- G: wiper arcs (residual film of a worn blade) ----
    G = np.zeros_like(x)
    for k, (px, py) in enumerate(PIVOTS):
        dx, dy = x - px, y - py
        rk = np.hypot(dx, dy)
        ak = np.degrees(np.arctan2(dy, dx))
        for _ in range(10):
            rad = rng.uniform(R_IN + 0.05, R_OUT - 0.02)
            width = rng.uniform(0.0006, 0.0012)
            a0 = rng.uniform(SWEEP[0], SWEEP[1] - 20)
            a1 = min(a0 + rng.uniform(25, 105), SWEEP[1])
            amp = rng.uniform(0.12, 0.4)
            line = np.exp(-((rk - rad) / width) ** 2)
            span = np.clip((ak - a0) / 6, 0, 1) * np.clip((a1 - ak) / 6, 0, 1)
            G = np.maximum(G, amp * line * span)
    G *= (value_noise(rng, 0.04, x, y) > 0.3) * (0.6 + 0.4 * fine) * wiped * on_glass

    # ---- B: insects ----
    B = np.zeros_like(x)
    n = 520
    k = 0
    while k < n:
        cx = rng.uniform(-1.18, 1.18)
        cy = rng.uniform(GLASS_Y[0] + 0.02, GLASS_Y[1] - 0.02)
        # more hits low and in the middle (air flow over the mask; the upper pane is in the roof deflector's wake)
        if rng.random() > (1.0 - 0.55 * (cy - GLASS_Y[0]) / (GLASS_Y[1] - GLASS_Y[0])) * (1.0 - 0.3 * abs(cx)):
            continue
        k += 1
        jx = int((cx - RECT_MIN[0]) / RECT_SIZE[0] * W)
        jy = int((cy - RECT_MIN[1]) / RECT_SIZE[1] * H)
        inside = wiped[min(jy, H - 1), min(jx, W - 1)] > 0.5
        size = rng.uniform(0.0012, 0.0032)
        if inside:
            # smeared by the blade: long thin streak along the arc, faint (most of it wiped off)
            if rng.random() < 0.8:
                continue
            px, py = PIVOTS[int(which[min(jy, H - 1), min(jx, W - 1)])]
            tang = math.atan2(cy - py, cx - px) + math.pi / 2
            splat(B, cx, cy, size * rng.uniform(3, 6), size * 0.7, tang, rng.uniform(0.1, 0.2))
        else:
            # air flow drives the remains upward: a short tail above the core
            splat(B, cx, cy, size, size * rng.uniform(0.8, 1.2), rng.uniform(0, math.pi), rng.uniform(0.7, 0.95), halo=0.25)
            if rng.random() < 0.5:
                splat(B, cx, cy + size * 1.8, size * 0.45, size * rng.uniform(1.5, 2.6), math.pi / 2 + rng.uniform(-0.3, 0.3),
                      rng.uniform(0.3, 0.55))
    B *= on_glass
    return R.astype(np.float32), G.astype(np.float32), B.astype(np.float32), wiped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=341)
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    R, G, B, wiped = build(a.seed)
    rgb = np.stack([R, G, B], axis=-1)
    img = (np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8)[::-1]     # row 0 = top (v = 1 = y max)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    Image.fromarray(img, "RGB").save(a.out, optimize=True)
    x, y = grid()
    glass = edge_distance(x, y) > 0
    cov = {
        "dust_R_gt_0.1": float(((R > 0.1) & glass).sum() / glass.sum()),
        "streak_G_gt_0.1": float(((G > 0.1) & glass).sum() / glass.sum()),
        "insect_B_gt_0.1": float(((B > 0.1) & glass).sum() / glass.sum()),
        "any_gt_0.1": float((((R > 0.1) | (G > 0.1) | (B > 0.1)) & glass).sum() / glass.sum()),
        "mean_R": float(R[glass].mean()), "mean_G": float(G[glass].mean()), "mean_B": float(B[glass].mean()),
        "wiped_share": float((wiped[glass] > 0.5).mean()),
    }
    print("WROTE", a.out)
    print(json.dumps(cov, indent=1))


if __name__ == "__main__":
    main()
