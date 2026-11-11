"""ADR 0050: contact shadow / AO patch of parked vehicles (life_props.contact_spec + Kamion/World Vehicle Contact).
The occlusion below is a numpy port of the shader's fragment function (keep the two in sync)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "worldgen"))

from streetscape import life_props as LP  # noqa: E402


def _strip(x, a, h):
    l, r = a - x, a + x
    return 0.5 * (l / np.sqrt(l * l + h * h) + r / np.sqrt(r * r + h * h))


def _slab(px, pz, s):
    return np.clip(_strip(px, s[1], s[3]), 0, 1) * np.clip(_strip(pz - s[0], s[2], s[3]), 0, 1)


def occlusion(spec, px, pz):
    st = spec["strength"]
    op = (1 - st[0] * _slab(px, pz, spec["slab0"])) * (1 - st[1] * _slab(px, pz, spec["slab1"]))
    ty = spec["tyre"]
    tx = np.clip(_strip(np.abs(px) - ty[0], ty[1], ty[3]), 0, 1)
    for a in spec["axles"]:
        op = op * (1 - st[2] * tx * np.clip(_strip(pz - a, ty[2], ty[3]), 0, 1))
    pa = spec["patch"]
    edge = np.minimum(pa[1] - np.abs(px), pa[2] - np.abs(pz - pa[0]))
    f = np.clip(edge / pa[3], 0, 1)
    f = f * f * (3 - 2 * f)
    return (1 - op) * f


NAMES = [f"car_{b}_silver" for b in LP.CARS] + ["van_white", "tractor_white", "trailer_curtain_0", "trailer_box_0"]


def test_every_vehicle_has_a_spec_and_others_none():
    for n in NAMES:
        s = LP.contact_spec(n)
        assert s is not None, n
        assert all(len(v) == 4 for v in s.values()), n
    for n in ("bench", "lamp_x", "bin_1100_green", "pallet_load"):
        assert LP.contact_spec(n) is None
    # ADR 0071 r11: static yard props resting on the ground carry a one-slab spec without tyres (the importer names
    # their patch prototype "propcontact_*": culled with the prop, not at the fixed vehicle distance)
    for n in ("container_20_0", "container_40_3", "gatehouse", "barrier_base"):
        s = LP.contact_spec(n)
        assert s is not None and all(len(v) == 4 for v in s.values()) and s["strength"][2] == 0.0, n


def test_car_occlusion_profile():
    """Darkest under the body, ~half at the sill line, soft edge ~0.3 m outside, nothing at the patch edge."""
    for b, d in LP.CARS.items():
        s = LP.contact_spec(f"car_{b}_silver")
        hw = d["W"] / 2
        assert occlusion(s, 0.0, 0.0) > 0.9, b
        at_edge = occlusion(s, hw, 0.0)
        assert 0.35 < at_edge < 0.75, (b, at_edge)
        out = occlusion(s, hw + 0.30, 0.0)
        assert out < 0.25, (b, out)
        assert occlusion(s, hw + 0.60, 0.0) < 0.05, b
        assert occlusion(s, s["patch"][1] - 0.01, 0.0) < 0.01
        assert occlusion(s, 0.0, s["patch"][0] + s["patch"][2] - 0.01) < 0.01
        # monotone falloff across the sill (no ring, no step)
        xs = np.linspace(0, s["patch"][1], 200)
        o = occlusion(s, xs, np.zeros_like(xs))
        assert np.all(np.diff(o) <= 1e-6), b


def test_patch_covers_footprint_with_margin():
    for n in NAMES:
        s = LP.contact_spec(n)
        cz, hx, hz, fade = s["patch"]
        assert fade > 0.2
        for key in ("slab0", "slab1", "sun_box"):
            c, a, b = s[key][0], s[key][1], s[key][2]
            assert hx >= a + 0.5 and cz - hz <= c - b - 0.5 and cz + hz >= c + b + 0.5, (n, key)


def test_trailer_darkest_at_axles_open_under_floor():
    s = LP.contact_spec("trailer_curtain_0")
    hw = LP.TRAILER_W / 2
    tyre = occlusion(s, hw - 0.27, LP.TRAILER_AXLES[1])
    floor = occlusion(s, 0.0, 9.0)
    assert tyre > 0.85 and 0.4 < floor < 0.9, (tyre, floor)


def test_cie_overcast_band_fraction():
    """Shader overcast correction: a horizon band up to elevation E of the CIE standard overcast sky (L ~ 1 + 2 sin e)
    carries o (3 + 4 sqrt(o)) / 7 of the horizontal irradiance, o = sin^2 E the uniform-sky cosine-weighted fraction."""
    e = np.linspace(0, np.pi / 2, 20001)
    w = (1 + 2 * np.sin(e)) * np.sin(e) * np.cos(e)
    total = np.trapezoid(w, e)
    for E in (0.05, 0.2, 0.5, 1.0, np.pi / 2):
        m = e <= E
        num = np.trapezoid(w[m], e[m]) / total
        o = np.sin(E) ** 2
        assert abs(num - o * (3 + 4 * np.sqrt(o)) / 7) < 1e-3, (E, num)
