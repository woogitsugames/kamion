"""ADR 0321: the conformed terrain under a rural ditch (soft verge nodes) never cuts through the ditch surface.

Synthetic: a straight 1 : 1.5 ditch with a 0.4 m flat bottom, 0.6 m deep, crossing the 1 m terrain grid at an
oblique angle (DK65 knyszyn-w: sawtooth of terrain grass across the back slope, vqa-wave5 dk65-fields-nw). The
terrain grid is interpolated with BOTH cell diagonals, so the check holds for any triangulation of the grid."""

from __future__ import annotations

import types

import numpy as np

from terrain_mesh import conform as CF

ANGLE = np.radians(27.0)
PROFILE = [(0.0, 0.0), (0.9, -0.6), (1.3, -0.6), (2.2, 0.0)]       # (u, dz): inner slope, bottom, back slope


def _ditch(z_top=100.0, length=60.0, u0=10.0):
    d = np.array([np.cos(ANGLE), np.sin(ANGLE)])
    n = np.array([-d[1], d[0]])
    s = np.arange(-length / 2, length / 2 + 1e-6, 2.0)
    rows = []
    for si in s:
        for u, dz in PROFILE:
            p = d * si + n * (u0 + u)
            rows.append([p[0], p[1], z_top + dz])
    V = np.array(rows)
    k = len(PROFILE)
    T = []
    for i in range(len(s) - 1):
        for j in range(k - 1):
            a, b, c, e = i * k + j, i * k + j + 1, (i + 1) * k + j, (i + 1) * k + j + 1
            T += [(a, c, b), (b, c, e)]
    return types.SimpleNamespace(V=V, T=np.array(T), footprint=True, mat="verge_grass"), d, n


def _surface_z(d, n, P, z_top=100.0, u0=10.0):
    u = P @ n - u0
    us, zs = zip(*PROFILE)
    return np.interp(u, us, np.array(zs) + z_top, left=np.nan, right=np.nan)


def _max_poke(zc, hf, d, n):
    """max(terrain - ditch surface) over a dense sample of the ditch, both grid diagonals."""
    rng = np.random.default_rng(0)
    s = rng.uniform(-20, 20, 40000)
    u = rng.uniform(0.0, 2.2, 40000)
    P = d[None] * s[:, None] + n[None] * (10.0 + u)[:, None]
    fi, fj = P[:, 0] - hf.x0, hf.y1 - P[:, 1]
    i, j = np.floor(fi).astype(int), np.floor(fj).astype(int)
    x, y = fi - i, fj - j
    z00, z10, z01, z11 = zc[j, i], zc[j, i + 1], zc[j + 1, i], zc[j + 1, i + 1]
    # diagonal 00-11
    t1 = np.where(x >= y, z00 + x * (z10 - z00) + y * (z11 - z10), z00 + y * (z01 - z00) + x * (z11 - z01))
    # diagonal 10-01
    t2 = np.where(x + y <= 1, z00 + x * (z10 - z00) + y * (z01 - z00),
                  z11 + (1 - x) * (z01 - z11) + (1 - y) * (z10 - z11))
    surf = _surface_z(d, n, P)
    ok = np.isfinite(surf)
    return float(max((t1 - surf)[ok].max(), (t2 - surf)[ok].max()))


def test_soft_floor_keeps_terrain_under_ditch():
    part, d, n = _ditch()
    hf = types.SimpleNamespace(z=np.full((80, 80), 100.0), x0=-40.0, y1=40.0)
    road, mask = CF.rasterise([part], hf)
    soft = mask.copy()
    old, _ = CF.conform(hf, road, mask, soft=soft)
    floor = CF.rasterise_floor([part], hf)
    new, _ = CF.conform(hf, road, mask, soft=soft, soft_floor=floor)
    poke_old = _max_poke(old, hf, d, n)
    poke_new = _max_poke(new, hf, d, n)
    assert poke_old > 0.05, poke_old           # the node-only rule cuts through the ditch (the reported sawtooth)
    assert poke_new <= 0.005, poke_new          # outside nodes drop at most FLOOR_OUTSIDE_DROP_M
    assert (old - new)[~mask].max() <= CF.FLOOR_OUTSIDE_DROP_M + 1e-9
    # flat verge: the floor changes nothing under it (urban verges / islands keep SOFT_UNDER, ADR 0110)
    flat = types.SimpleNamespace(V=part.V * [1, 1, 0] + [0, 0, 100.0], T=part.T, footprint=True, mat="verge_grass")
    r2, m2 = CF.rasterise([flat], hf)
    a, _ = CF.conform(hf, r2, m2, soft=m2.copy())
    b, _ = CF.conform(hf, r2, m2, soft=m2.copy(), soft_floor=CF.rasterise_floor([flat], hf))
    assert np.abs(a - b)[m2].max() < 1e-9
    assert b.min() >= 100.0 - CF.SOFT_UNDER - 1e-9     # outside: one cell at most down to the verge - SOFT_UNDER
