"""paved_apron re-surfaces generated carriageway analytically: area and heights are kept (ADR 0100)."""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "worldgen"))
from roads import aprons  # noqa: E402
from roads.meshing import MeshBuf  # noqa: E402


def _plate():
    buf = MeshBuf()
    xs, ys = np.meshgrid(np.linspace(0, 10, 6), np.linspace(0, 6, 4))
    V = np.column_stack([xs.ravel(), ys.ravel(), 100.0 + 0.02 * xs.ravel() + 0.03 * ys.ravel()])
    T = []
    for r in range(3):
        for c in range(5):
            a = r * 6 + c
            T += [(a, a + 1, a + 7), (a, a + 7, a + 6)]
    buf.add("road", "road_asphalt", V, V[:, :2], np.array(T), src="c:test")
    return buf


def _area(p):
    a = p.V[p.T][:, :, :2]
    u, v = a[:, 1] - a[:, 0], a[:, 2] - a[:, 0]
    return float(np.abs(u[:, 0] * v[:, 1] - u[:, 1] * v[:, 0]).sum() / 2)


def test_apron_splits_plate_and_keeps_surface():
    buf = _plate()
    rep, applied, stale = {}, [], []
    poly = [[3.3, 0.5], [7.7, 0.5], [6.1, 5.5], [3.3, 5.5]]
    aprons.apply(buf, [{"id": "a", "kind": "paved_apron", "surface": "sett", "polygon_en": poly}], rep, applied, stale)
    assert not stale and applied
    sett = [p for p in buf.parts if p.mat == "road_sett"]
    asph = [p for p in buf.parts if p.mat == "road_asphalt"]
    tot = sum(_area(p) for p in buf.parts)
    assert abs(tot - 60.0) < 1e-6
    want = 5.0 * ((7.7 - 3.3) + (6.1 - 3.3)) / 2      # trapezoid inside the plate
    assert abs(sum(_area(p) for p in sett) - want) < 1e-3
    for p in sett + asph:
        z = 100.0 + 0.02 * p.V[:, 0] + 0.03 * p.V[:, 1]
        assert np.allclose(p.V[:, 2], z, atol=1e-9)
    assert rep["paved_aprons"][0]["built"]


def test_apron_never_splits_the_plate_outline():
    """A polygon crossing the outline (= seams with neighbouring parts) moves those triangles whole: no new vertex
    on an outline edge (T-junction in the seam)."""
    buf = _plate()
    before = {tuple(np.round(v[:2], 6)) for v in buf.parts[0].V}
    rep, applied, stale = {}, [], []
    poly = [[3.3, -1.0], [7.7, -1.0], [6.1, 7.0], [3.3, 7.0]]
    aprons.apply(buf, [{"id": "a", "kind": "paved_apron", "polygon_en": poly}], rep, applied, stale)
    for p in buf.parts:
        for v in p.V:
            x, y = v[:2]
            if abs(y) < 1e-9 or abs(y - 6.0) < 1e-9 or abs(x) < 1e-9 or abs(x - 10.0) < 1e-9:
                assert tuple(np.round(v[:2], 6)) in before, (x, y)
    assert abs(sum(_area(p) for p in buf.parts) - 60.0) < 1e-6
