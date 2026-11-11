"""ADR 0102: visible contact, sign clearance, foundation reach and rigid fence construction."""
import numpy as np
import pytest
from shapely.geometry import LineString

from streetscape import furniture as F, props as P


class Top:
    def __init__(self, fn):
        self.fn = fn

    def top(self, e, n, below=None):
        return self.fn(e, n)


def test_visible_axis_contact_is_independent_of_low_collision():
    flat = lambda e, n: np.zeros_like(e, dtype=float)
    pl = F.Placer(flat, flat, Top(lambda e, n: 1.087 if e >= 0 else 0), Top(lambda e, n: 0))
    z, step = pl.seat("lamp_12m", (0, 0))
    assert z == 1.087 and step == 1.087
    # Do not bury a metre of visible shaft: shift locally to stable ground, then use a shallow footing.
    pl.add("lamp_12m", (0, 0), 0)
    it = pl.items[-1]
    assert np.hypot(it["e"], it["n"]) <= 1.051
    assert it["e"] < -0.25 and it["z"] == 0
    m = P.lamp(12, 2)[0].out()
    v = next(p["V"] for p in m if p["mat"] == "concrete_base")[:, 2]
    assert -0.6 < v.min() < 0 and v.max() > 0


def test_explicit_bridge_lamp_position_and_height_are_preserved():
    flat = lambda e, n: np.zeros_like(e, dtype=float)
    pl = F.Placer(flat, flat, Top(lambda e, n: 1.087 if e >= 0 else 0))
    pl.add("lamp_12m", (0, 0), 0, z=8)
    assert pl.items[-1]["e"] == 0 and pl.items[-1]["z"] == 8
    assert not pl.support_moves


def test_sign_assembly_keeps_legal_clearance_on_kerb():
    flat = lambda e, n: np.zeros_like(e, dtype=float)
    pl = F.Placer(flat, flat, Top(lambda e, n: 0.16))
    F.sign_assembly(pl, (0, 0), (0, 1), ["B-33_50"], "unit", sidewalk=True)
    post, plate = pl.items
    assert post["z"] == 0.16
    from roads import standards as S
    assert plate["z"] - S.SIGN_SIZE["disc"] / 2 - post["z"] == pytest.approx(S.SIGN_H_SIDEWALK)


@pytest.mark.parametrize("kind,height", [("concrete", 9), ("steel", 8)])
def test_lamp_lods_keep_material_slot_count_and_no_degenerate_triangles(kind, height):
    for mesh in P.lamp_old(height, kind)[:2]:
        prims = mesh.out()
        assert len(prims) == 4
        for p in prims:
            a, b, c = np.moveaxis(p["V"][p["T"]], 1, 0)
            assert np.all(np.linalg.norm(np.cross(b-a, c-a), axis=1) > 1e-10)


class Buffer:
    def __init__(self):
        self.parts = []

    def add(self, layer, mat, V, UV, T, **kwargs):
        self.parts.append((layer, mat, np.asarray(V), np.asarray(T)))


def test_panel_fence_has_level_bays_corner_posts_and_buried_feet():
    buf = Buffer()
    lin = F.Lin(buf, lambda e, n: 0.4 * e)
    F.panel_fence(lin, LineString([(0, 0), (4, 0), (4, 2)]), "fence_green", "test")
    mesh = [v for layer, mat, v, t in buf.parts if mat == "fence_green_mesh"]
    for v in mesh:
        assert np.ptp(v[len(v)//2:, 2]) == 0  # level top, not sheared mesh
    posts = next(v for layer, mat, v, t in buf.parts if mat == "fence_green")
    for v in posts.reshape(-1, 8, 3):
        e = v[:, 0].mean()
        assert v[:, 2].min() == pytest.approx(0.4 * e - 0.3)
    assert any(np.allclose(v[:, :2].mean(axis=0), [4, 0]) for v in posts.reshape(-1, 8, 3))

