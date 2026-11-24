"""ADR 0335 (critic build #5 pkt 4): repairs come in kinds (milled / trench / hot-mix blob / rut fill), the kind rides in
the integer part of UV1.y, the age distribution is three-modal, and none of it changes the triangle count (ADR 0327)."""
from types import SimpleNamespace

import numpy as np

from roads import decals as DC
from test_road_surface_0323 import _Buf, _chain


def _patches(length=4000.0, **kw):
    c, _ = _chain(length=length, cls="L", **kw)
    buf = _Buf()
    orig = DC.gullies
    DC.gullies = lambda *a, **k: None               # gully placement needs the chain side tables, not under test
    try:
        DC.build(buf, SimpleNamespace(chains=[c], sec_list=[]), [], {})
    finally:
        DC.gullies = orig
    parts = [p for p in buf.parts if p.mat == "decal_patch"]
    return buf, parts


def test_kinds_are_encoded_decodable_and_all_present():
    _, parts = _patches()
    assert len(parts) > 60
    kinds = []
    for p in parts:
        w = p.UV1[:, 1]
        assert np.ptp(w) == 0.0                          # constant per patch (clipping interpolation stays exact)
        k = int(np.floor(w[0]))
        assert 1 <= k <= 4 and 0.02 <= w[0] - k <= 0.98  # frac never within 0.02 of an integer boundary
        assert 0.0 <= p.UV1[0, 0] <= 1.0
        kinds.append(k)
    assert set(kinds) == {DC.PATCH_MILLED, DC.PATCH_TRENCH, DC.PATCH_HOT, DC.PATCH_RUT}


def test_kind_geometry_rules():
    _, parts = _patches()
    for p in parts:
        k = int(np.floor(p.UV1[0, 1]))
        L = np.ptp(p.UV[:, 0]); W = np.ptp(p.UV[:, 1])     # UV0 in metres (not yet normalised)
        if k == DC.PATCH_MILLED:
            assert L >= 3.0 - 1e-6 and W > 2.5          # a lane section, cut across the lane
        if k == DC.PATCH_HOT:
            assert max(L, W) < 2.5                         # a pothole, not a strip
        if k == DC.PATCH_RUT:
            assert W < 1.5


def test_age_is_three_modal_and_in_range():
    u = np.linspace(0, 1, 2001)
    a = np.array([DC.patch_age(x) for x in u])
    assert a.min() == 0.0 and abs(a.max() - 1.0) < 1e-9 and np.all(np.diff(a) >= 0)
    assert 0.33 < np.mean(a < 0.3) < 0.37 and 0.28 < np.mean(a > 0.7) < 0.32


def test_deterministic_and_triangle_count_unchanged_by_kinds():
    b1, p1 = _patches(length=1500.0)
    b2, p2 = _patches(length=1500.0)
    assert [p.src for p in p1] == [p.src for p in p2]
    assert all(np.array_equal(a.UV1, b.UV1) and np.array_equal(a.T, b.T) for a, b in zip(p1, p2))
    # ADR 0327: one quad per 2.5 x 2 m cell regardless of the kind - the mask is pixel work
    for p in p1:
        L = np.ptp(p.UV[:, 0]); W = np.ptp(p.UV[:, 1])
        cells = int(np.ceil(L / 2.5 - 1e-9)) * int(np.ceil(W / 2.0 - 1e-9))
        assert len(p.T) == 2 * cells


def test_no_asphalt_repairs_on_stone_concrete_gravel():
    for surface in ("road_sett", "road_cobble", "road_concrete", "road_gravel", "road_asphalt_new"):
        _, parts = _patches(length=1500.0, surface=surface)
        assert parts == [], surface
