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
    N2 = M.seam_shear(net, c, st, T, N, hw)
    assert abs(N2[-1, 0]) < 1e-9                     # end row parallel to the seam line (x = const)
    assert np.allclose(np.einsum("ij,ij->i", N2, N), 1.0)     # lateral offsets square to the axis unchanged
    assert np.allclose(N2[0], N[0])                  # junction end untouched
    # no row overtakes the next one at the outer edge (no folded triangles)
    P = st[:, None] * T[0]
    for lat in (-(5.875 + 3.0), 5.875 + 3.0):
        along = ((P + lat * N2) @ T[0])
        assert np.all(np.diff(along) > 0)


def test_square_crossing_and_inner_end_unchanged(monkeypatch):
    monkeypatch.setattr(M, "side_params", lambda c, sd, s: ())
    monkeypatch.setattr(M, "side_extent", lambda *a: 3.0)
    c, st, T, N = _chain(180.0)
    net = SimpleNamespace(nodes={"j": {"boundary": False}, "seam": {"boundary": True, "seam_u": np.array([0.0, 1.0])}})
    assert M.seam_shear(net, c, st, T, N, np.full(len(st), 3.0)) is N
    c, st, T, N = _chain(221.0)
    net = SimpleNamespace(nodes={"j": {"boundary": False}, "seam": {"boundary": False}})
    assert M.seam_shear(net, c, st, T, N, np.full(len(st), 3.0)) is N
