"""seam-knw-s24: a chain cut by a tile seam ends with its cross-section ON the seam line (meshing.seam_shear), so the
two tiles of an oblique road (Tykocka / DW671 at the knyszyn | knyszyn-w seam, 41 deg) meet without terrain triangles."""
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "worldgen"))

from roads import meshing as M  # noqa: E402
from roads import network as Nw  # noqa: E402

BBOX = [760587.0, 611583.0, 762635.0, 613631.0]


def test_seam_dir_from_graph_bbox():
    assert np.allclose(Nw._seam_dir({"boundary": True, "x": 760587.0, "y": 611964.5}, BBOX), [0, 1])
    assert np.allclose(Nw._seam_dir({"boundary": True, "x": 761000.0, "y": 611583.0}, BBOX), [1, 0])
    assert Nw._seam_dir({"boundary": False, "x": 760587.0, "y": 611964.5}, BBOX) is None
    assert Nw._seam_dir({"boundary": True, "x": 760587.0, "y": 611583.0}, BBOX) is None      # corner
    assert Nw._seam_dir({"boundary": True, "x": 760587.0, "y": 611964.5}, None) is None


def _chain(angle_deg, L=30.0, ext=3.0):
    a = np.radians(angle_deg)
    t = np.array([np.cos(a), np.sin(a)])
    st = np.arange(0.0, L + 1e-9, 2.0)
    T = np.repeat(t[None], len(st), 0)
    N = np.column_stack([-T[:, 1], T[:, 0]])
    c = SimpleNamespace(node_a="j", node_b="seam", length=L, side={}, _ext=ext)
    return c, st, T, N


def test_end_row_lies_on_the_seam_and_keeps_square_widths(monkeypatch):
    monkeypatch.setattr(M, "side_params", lambda c, sd, s: ())
    monkeypatch.setattr(M, "side_extent", lambda *a: 3.0)
    c, st, T, N = _chain(221.0)                      # running SW into a vertical seam, like Tykocka in knyszyn
    net = SimpleNamespace(nodes={"j": {"boundary": False}, "seam": {"boundary": True, "seam_u": np.array([0.0, 1.0])}})
    hw = np.full(len(st), 5.875)
    NL, NR, clip = M.seam_shear(net, c, st, T, N, hw)
    assert not clip
    P = st[:, None] * T[0]
    for N2, lat in ((NL, 5.875 + 3.0), (NR, -(5.875 + 3.0))):
        assert abs(N2[-1, 0]) < 1e-9                 # end row parallel to the seam line (x = const)
        assert np.allclose(np.einsum("ij,ij->i", N2, N), 1.0)     # lateral offsets square to the axis unchanged
        assert np.allclose(N2[0], N[0])              # junction end untouched
        assert np.all(np.diff((P + lat * N2) @ T[0]) > 0)    # no row overtakes the next one (no folded triangles)


def test_short_stub_limits_the_pulled_back_side_and_asks_for_a_clip(monkeypatch):
    monkeypatch.setattr(M, "side_params", lambda c, sd, s: ())
    monkeypatch.setattr(M, "side_extent", lambda *a: 2.75)
    c, st, T, N = _chain(221.0, L=6.6)                # Knyszyn W arm: 6.6 m from the splitter node to the seam
    st = np.linspace(0.0, 6.6, 5)
    T, N = np.repeat(T[:1], 5, 0), np.repeat(N[:1], 5, 0)
    net = SimpleNamespace(nodes={"j": {"boundary": False}, "seam": {"boundary": True, "seam_u": np.array([0.0, 1.0])}})
    NL, NR, clip = M.seam_shear(net, c, st, T, N, np.full(len(st), 5.875))
    assert clip
    P = st[:, None] * T[0]
    ext = 5.875 + 2.75
    for N2, lat in ((NL, ext), (NR, -ext)):
        assert np.all(np.diff((P + lat * N2) @ T[0]) > 0)    # still no fold on either side
    xs = [float((P[-1] + l * N2[-1])[0] - P[-1][0]) for N2, l in ((NL, ext), (NR, -ext))]
    assert min(abs(x) for x in xs) < 1e-9            # one side exactly on the seam line
    assert max(xs) > 0 or min(xs) < 0                 # the other side reaches past it (clipped by build_world)


def test_square_crossing_and_inner_end_unchanged(monkeypatch):
    monkeypatch.setattr(M, "side_params", lambda c, sd, s: ())
    monkeypatch.setattr(M, "side_extent", lambda *a: 3.0)
    c, st, T, N = _chain(180.0)
    net = SimpleNamespace(nodes={"j": {"boundary": False}, "seam": {"boundary": True, "seam_u": np.array([0.0, 1.0])}})
    nl, nr, clip = M.seam_shear(net, c, st, T, N, np.full(len(st), 3.0))
    assert nl is N and nr is N and not clip
    c, st, T, N = _chain(221.0)
    net = SimpleNamespace(nodes={"j": {"boundary": False}, "seam": {"boundary": False}})
    nl, nr, clip = M.seam_shear(net, c, st, T, N, np.full(len(st), 3.0))
    assert nl is N and nr is N and not clip


def test_markings_clipped_to_the_tile_box():
    buf = M.MeshBuf()
    V = np.array([[-2.0, 0.0, 1.0], [2.0, 0.0, 1.0], [2.0, 0.2, 1.0], [-2.0, 0.2, 1.0]])
    buf.add("markings", "marking_white", V, V[:, :2] * 10.0, np.array([(0, 1, 2), (0, 2, 3)]), UV1=V[:, :2])
    V2 = V + [5.0, 5.0, 0.0]
    buf.add("markings", "marking_white", V2, V2[:, :2], np.array([(0, 1, 2), (0, 2, 3)]))
    rep = M.clip_layer_to_box(buf, "markings", (-10.0, -10.0, 0.0, 10.0))
    p, q = buf.parts
    used = np.unique(p.T)
    assert p.V[used, 0].max() <= 1e-9 and p.V[used, 0].min() == -2.0
    area = sum(0.5 * abs(np.cross(p.V[b] - p.V[a], p.V[c] - p.V[a])[2]) for a, b, c in p.T)
    assert abs(area - 0.4) < 1e-9                      # half of the 4 x 0.2 m stripe
    assert np.allclose(p.UV[used], p.V[used, :2] * 10.0) and np.allclose(p.UV1[used], p.V[used, :2])
    assert len(q.T) == 0 and rep["dropped"] == 2 and rep["clipped"] == 2
