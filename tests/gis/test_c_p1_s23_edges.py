"""c-p1-s23 (REVIEW-2026-11-14-s20-gate3-phone P1-1 / P1-2 / P2-10) on synthetic data, no Data/raw:
- back-of-sidewalk flange over open ground -> edging BACK_EDGE_FACE_M + grass batter (":vg", merged into the terrain);
  kept where a hard footprint lies beyond the edge;
- walled-ramp mask: ground beside a walled run is excluded from clamp_under_decks, ground beside a span is not;
- ramp wall courses: v = absolute height (level courses on a sloping foot)."""
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))

from roads import meshing as M  # noqa: E402
from roads import standards as S  # noqa: E402
from terrain_mesh import conform as CF  # noqa: E402


def _hf(n=41, x0=-20.0, y1=20.0, z=100.0):
    return SimpleNamespace(z=np.full((n, n), z), x0=x0, y1=y1)


def _flange(buf, x0, x1, y, top, depth, out=(0.0, 1.0), stations=6):
    """vertical flange along E at N = y, facing +N (outward), rows [top, bottom] per station like _emit_strip."""
    xs = np.linspace(x0, x1, stations)
    rows = [[[x, y, top], [x, y, top - depth]] for x in xs]
    V = np.array(rows).reshape(-1, 3)
    T = M.grid_tris(stations, 2)
    buf.add("road", "curb_concrete", V, V[:, :2].copy(), T, src="w1:L")
    buf.parts[-1].back_out = np.tile(np.asarray(out, float), (stations, 1))
    return buf.parts[-1]


def test_back_flange_over_open_ground_becomes_edging_and_batter():
    buf = M.MeshBuf()
    p = _flange(buf, -5, 5, 0.0, 100.30, S.FLANGE_DEPTH)
    hard = np.zeros((41, 41), bool)
    rep = M.back_flange_batter(buf, hard, _hf())
    assert rep["parts"] == 1 and rep["stations_battered"] == 6
    # concrete face cut to the edging
    face = p.V[0::2, 2] - p.V[1::2, 2]
    assert np.allclose(face, M.BACK_EDGE_FACE_M)
    g = [q for q in buf.parts if q.src.endswith(":vg")]
    assert len(g) == 1 and g[0].mat == "verge_grass" and not g[0].footprint
    Vg = g[0].V
    # batter foot is the old flange foot, run = (depth - edging) * VERGE_SKIRT_SLOPE outward (+N)
    assert np.allclose(Vg[1::2, 2], 100.30 - S.FLANGE_DEPTH)
    assert np.allclose(Vg[1::2, 1], (S.FLANGE_DEPTH - M.BACK_EDGE_FACE_M) * S.VERGE_SKIRT_SLOPE)
    assert np.allclose(Vg[0::2, 2], 100.30 - M.BACK_EDGE_FACE_M)
    # faces up-and-outward (normal z > 0, normal N > 0): same winding as the outward flange
    a, b, c = (Vg[g[0].T[:, k]] for k in range(3))
    nrm = np.cross(b - a, c - a)
    flange_n = np.cross(*(p.V[p.T[0, k]] - p.V[p.T[0, 0]] for k in (1, 2)))
    assert np.all(np.sign(nrm[:, 1]) == np.sign(flange_n[1])) and np.all(np.abs(nrm[:, 2]) > 0)


def test_back_flange_next_to_hard_footprint_is_kept():
    buf = M.MeshBuf()
    p = _flange(buf, -5, 5, 0.0, 100.30, S.FLANGE_DEPTH)
    hard = np.zeros((41, 41), bool)
    hard[: 20 - 0, :] = True          # rows j < 20 = N > 0 (y1 - j): a paving beyond the edge
    hard[19, :] = True
    V0 = p.V.copy()
    rep = M.back_flange_batter(buf, hard, _hf())
    assert rep["stations_battered"] == 0
    assert np.array_equal(p.V, V0) and not any(q.src.endswith(":vg") for q in buf.parts)


def test_untagged_flange_untouched():
    buf = M.MeshBuf()
    xs = np.linspace(-5, 5, 4)
    V = np.array([[[x, 0, 100.3], [x, 0, 99.8]] for x in xs]).reshape(-1, 3)
    buf.add("road", "curb_concrete", V, V[:, :2].copy(), M.grid_tris(4, 2), src="kerb")
    rep = M.back_flange_batter(buf, np.zeros((41, 41), bool), _hf())
    assert rep["parts"] == 0 and len(buf.parts) == 1


def test_walled_mask_spares_ground_from_deck_clamp():
    from roads.build_world import walled_ramp_mask
    s = np.arange(0.0, 31.0, 1.0)
    P = np.column_stack([s - 15.0, np.zeros_like(s)])
    walled = s <= 15.0
    bridge = np.ones_like(s, bool)                       # walled stations are bridge stations (mark_walled_ramps)

    def frame(ss):
        return np.tile([1.0, 0.0], (len(ss), 1)), np.tile([0.0, 1.0], (len(ss), 1))
    line = SimpleNamespace(s=s, p=P, frame=frame)
    c = SimpleNamespace(meta={"walled": walled}, bridge=bridge, line=line, hw=np.full(len(s), 3.5))
    hf = _hf()
    m = walled_ramp_mask(SimpleNamespace(chains=[c]), hf)
    j0 = int(round(hf.y1 - 0.0))
    # beside the walled run (E -10, N 5.5+1 = edge + 1 node) excluded from the clamp, beside the span (E +10) not
    assert m[int(round(hf.y1 - 6.0)), int(round(-10 - hf.x0))]
    assert not m[int(round(hf.y1 - 6.0)), int(round(10 - hf.x0))]
    assert m[j0, int(round(-10 - hf.x0))]
    # clamp: deck at 101.0 all along, ground at 100.8 beside it -> pit dug only beside the span
    deck = np.full(hf.z.shape, -np.inf)
    deck_mask = np.zeros(hf.z.shape, bool)
    deck_mask[j0 - 5: j0 + 6, :] = True
    deck[deck_mask] = 101.0
    z = np.full(hf.z.shape, 100.8)
    out = CF.clamp_under_decks(z, deck, deck_mask, 0.6, m)
    jb = j0 - 6                                          # first row beside the deck edge
    assert out[jb, int(round(-10 - hf.x0))] == 100.8     # walled: untouched
    assert out[jb, int(round(10 - hf.x0))] < 100.2       # span: cleared below the soffit


def test_ramp_wall_courses_level():
    buf = M.MeshBuf()
    A = np.array([[0, 0, 100.0], [5, 0, 99.0], [10, 0, 100.5]])      # foot follows a dipping ground
    B = np.array([[0, 0, 103.0], [5, 0, 103.5], [10, 0, 104.0]])
    M._strip(buf, "bridge", "ramp_wall_blocks", A, B, "x:ramp_wall", both=False, v_abs=True)
    p = buf.parts[-1]
    # v - z is constant over all vertices -> courses level
    d = p.UV[:, 1] - p.V[:, 2]
    assert np.allclose(d, d[0])
    M._strip(buf, "bridge", "ramp_wall_blocks", A, B, "x:ramp_wall", both=False)
    q = buf.parts[-1]
    assert np.allclose(q.UV[:3, 1], 0.0)                 # default unchanged (v from the foot)
