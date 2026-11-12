"""Unit tests (no Data/raw): mesh triangulation/extrusion, terrain chunking, barriers along a curve.

Covers roads.meshing.grid_tris / MeshBuf.add, terrain_mesh.chunks (lod_grid, grid_mesh, build_chunks)
and streetscape.furniture.guardrail (W-beam barrier generated along a synthetic arc).

Run: uv run --project tools/worldgen pytest tests/gis -q -m unit
"""

import math

import numpy as np
import pytest

from roads import standards as S
from roads.meshing import MeshBuf, grid_tris
from streetscape import furniture as F
from terrain_mesh import chunks as C

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------- triangulation / extrusion

def test_grid_tris_count_bounds_and_winding():
    nr, nc = 5, 4
    t = grid_tris(nr, nc)
    assert len(t) == 2 * (nr - 1) * (nc - 1)
    assert t.min() >= 0 and t.max() < nr * nc
    assert (t[:, 0] != t[:, 1]).all() and (t[:, 1] != t[:, 2]).all() and (t[:, 0] != t[:, 2]).all()
    tf = grid_tris(nr, nc, flip=True)
    assert len(tf) == len(t)
    assert set(map(tuple, tf[:, [0, 2, 1]])) == set(map(tuple, t))   # flip = reversed winding


def test_meshbuf_add_drops_degenerate_triangles():
    buf = MeshBuf()
    V = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [2.0, 2.0, 0.0]])
    T = np.array([[0, 1, 2], [0, 1, 1]])          # second triangle is degenerate
    buf.add("road", "road_asphalt", V, V[:, :2], T)
    assert len(buf.parts) == 1
    assert np.array_equal(buf.parts[0].T, [[0, 1, 2]])
    buf.add("road", "road_asphalt", V, V[:, :2], np.zeros((0, 3), int))   # empty -> no part
    assert len(buf.parts) == 1


def test_grid_mesh_extrusion_vertices_tris_and_skirts():
    z = np.arange(12.0).reshape(3, 4) + 100.0
    nrm = C.normals(z, 1.0)
    skirt = 1.5
    V, N, T = C.grid_mesh(z, nrm, e0=-10.0, n0=10.0, step=1.0, i0=0, i1=3, j0=0, j1=2, skirt=skirt)
    h, w = 3, 4
    n_grid = h * w
    assert np.isfinite(V).all() and np.isfinite(N).all()
    n_skirt_tris = 2 * (2 * (w - 1) + 2 * (h - 1))   # 4 border loops, 2 tris per edge
    assert len(T) == 2 * (h - 1) * (w - 1) + n_skirt_tris
    assert T.max() < len(V)
    # grid interior keeps the input heights; node (j, i) at E = e0 + i*step, N = n0 - j*step
    assert np.allclose(V[:n_grid, 2].reshape(h, w), z)
    assert V[0, 0] == pytest.approx(-10.0) and V[0, 1] == pytest.approx(10.0)
    # skirts: every hanging vertex is exactly `skirt` below a border vertex with the same E, N
    top, bot = V[:n_grid], V[n_grid:]
    assert len(bot) == 2 * (w + h)
    for b in bot:
        d = np.hypot(*(top[:, :2] - b[:2]).T)
        i = int(d.argmin())
        assert d[i] < 1e-9 and top[i, 2] - b[2] == pytest.approx(skirt)


# ---------------------------------------------------------------- chunking

@pytest.fixture(scope="module")
def tile():
    rng = np.random.default_rng(7)
    zc = 100.0 + rng.normal(0, 1, (513, 513))       # 512 m tile at 1 m resolution + 1
    mask = np.zeros((513, 513), bool)
    mask[100:110, 200:210] = True                    # "road footprint" window
    return zc, mask


def test_build_chunks_tiles_the_whole_tile(tile):
    zc, mask = tile
    out = C.build_chunks(zc, mask, e0=-256.0, n0=256.0, size_m=512.0)
    assert sorted(out.keys()) == [(0, 0), (0, 1), (1, 0), (1, 1)]   # 2 x 2 chunks of 256 m
    for lods in out.values():
        assert sorted(lods.keys()) == [0, 1, 2, 3]
        # LOD0 (1 m) splits each 256 m chunk into 4 x 128 m sub-grids; coarser LODs are single prims
        assert [len(lods[li]) for li in range(4)] == [4, 1, 1, 1]
        for prims in lods.values():
            for pr in prims:
                assert np.isfinite(pr["V"]).all() and np.isfinite(pr["N"]).all()
                assert pr["T"].max() < len(pr["V"])                 # valid indices
                assert len(pr["V"]) < 65536                          # 16-bit index budget


def test_lod0_heights_match_input_and_lod_grid_min_near_road(tile):
    zc, mask = tile
    out = C.build_chunks(zc, mask, e0=0.0, n0=512.0, size_m=512.0)
    v0 = np.concatenate([pr["V"][:, 2] for pr in out[(0, 0)][0]])
    assert v0.max() <= zc.max() + 1e-9
    assert v0.min() >= zc.min() - 1.6            # LOD0 skirt hangs 1.5 m below the border
    zl = C.lod_grid(zc, mask, 8)
    assert zl.shape == (65, 65)
    near = zl[13, 25]     # coarse node whose window covers the masked road window
    assert near == pytest.approx(zc[100:109, 200:209].min(), abs=1.0)  # min near road: never pokes through
    assert zl[0, 0] == pytest.approx(zc[0, 0])                          # away from road: plain decimation


# ---------------------------------------------------------------- barrier along a curve

class _Lin:
    def __init__(self):
        self.buf = MeshBuf()


def _arc_points(radius=50.0, sweep=math.pi / 2, n=30):
    t = np.linspace(0, sweep, n)
    return np.column_stack([radius * np.cos(t), radius * np.sin(t)])


def test_guardrail_along_arc_follows_curve_no_nan():
    P = _arc_points()
    lin = _Lin()
    F.guardrail(lin, P, np.zeros(len(P)), "unit:rail")
    assert lin.buf.parts, "guardrail produced no parts"
    layers = {p.layer for p in lin.buf.parts}
    assert "furniture" in layers and "collision" in layers
    assert all(p.mat in ("barrier_steel", "collision_steel") for p in lin.buf.parts)
    V = np.vstack([p.V for p in lin.buf.parts])
    assert np.isfinite(V).all()
    assert V[:, 2].max() <= S.GUARDRAIL_H + 1e-9 and V[:, 2].min() >= -0.5   # beam + posts, no floating junk
    # the beam follows the curve: every vertex stays within the W-profile width of the arc
    d = np.abs(np.hypot(V[:, 0], V[:, 1]) - 50.0)
    assert d.max() < 0.25
    for p in lin.buf.parts:
        assert p.T.max() < len(p.V)


def test_guardrail_is_deterministic_and_symmetric():
    P = _arc_points()
    l1, l2 = _Lin(), _Lin()
    F.guardrail(l1, P, np.zeros(len(P)), "unit:rail")
    F.guardrail(l2, P, np.zeros(len(P)), "unit:rail")
    assert len(l1.buf.parts) == len(l2.buf.parts)
    for a, b in zip(l1.buf.parts, l2.buf.parts):
        assert np.array_equal(a.V, b.V) and np.array_equal(a.T, b.T)
    # the same curve rotated 180 deg about the vertical axis (orientation-preserving) rotates the beam:
    # (E, N) -> (-E, -N), heights unchanged
    l3 = _Lin()
    F.guardrail(l3, -P, np.zeros(len(P)), "unit:rail")
    V1 = np.vstack([p.V for p in l1.buf.parts if p.layer == "furniture"])
    V3 = np.vstack([p.V for p in l3.buf.parts if p.layer == "furniture"])
    assert len(V1) == len(V3)
    assert np.allclose(V3[:, 0], -V1[:, 0], atol=1e-9)
    assert np.allclose(V3[:, 1], -V1[:, 1], atol=1e-9)
    assert np.allclose(V3[:, 2], V1[:, 2], atol=1e-9)
