"""axis-driveway-s24 (critic build #10 pkt 7): driveway crossings of rural verges - square to the road over a filled
ditch, surface from the plot, no verge flora on them."""
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import shapely
from shapely.geometry import Polygon

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "worldgen"))
from roads import network as NW                 # noqa: E402
from roads.geom import Polyline                 # noqa: E402
from streetscape import plots as PLT            # noqa: E402


def _chain(length=200.0, hw=3.5, depth=0.6):
    n = int(length / 0.5) + 1
    line = Polyline(np.column_stack([np.linspace(0.0, length, n), np.zeros(n)]))
    side = {"kind": np.full(n, NW.RURAL), "h": np.full(n, depth), "w": np.zeros(n), "depth": np.full(n, 0.3),
            "mat": np.zeros(n, int)}
    return SimpleNamespace(id="c1", meta={}, line=line, t_a=0.0, t_b=0.0, length=float(line.length), bridge=np.zeros(n, bool),
                           idx=lambda s: int(np.clip(round(float(s) / 0.5), 0, n - 1)),
                           hw_at=lambda s: np.full(np.shape(s), hw) if np.ndim(s) else hw,
                           side={"L": dict(side), "R": dict(side)})


def _carriage(length=200.0, hw=3.5):
    return Polygon([(0, -hw), (length, -hw), (length, hw), (0, hw)])


def test_oblique_gate_crosses_the_ditch_square_to_the_road():
    c = _chain()
    net = SimpleNamespace(chains=[c])
    m = np.array([100.0, 3.5 + 9.0])                        # gate 9 m off the edge, normal 41 deg off the road normal
    a = np.radians(41.0)
    n = np.array([-np.sin(a), -np.cos(a)])
    acc, drop = PLT.gate_access(m, n, 3.5, net, _carriage())
    assert acc is not None and acc["ok"] and acc.get("cross") is not None
    pe, q = acc["cross"]
    edge = 3.5 + NW.side_profile(NW.RURAL, 0.6, 0.0, 0.3, 0)[-1][2]
    assert abs(pe[1] - edge) < 0.3                          # leaves the gate ray at the footprint edge
    assert abs(q[1] - 3.5) < 1e-6 and abs(q[0] - pe[0]) < 1e-6   # square to the carriageway edge
    assert abs(drop["s"] - pe[0]) < 1e-6                    # the ditch is filled where the crossing is
    s_ray = m[0] + n[0] * (9.0 / np.cos(a))
    assert abs(drop["s"] - s_ray) > 3.0                     # (not where the diagonal met the asphalt)


def test_square_gate_keeps_the_straight_crossing():
    c = _chain()
    acc, drop = PLT.gate_access(np.array([100.0, 12.0]), np.array([0.0, -1.0]), 3.5, SimpleNamespace(chains=[c]), _carriage())
    assert acc["ok"] and acc.get("cross") is None and abs(drop["s"] - 100.0) < 0.5


def test_drive_material_follows_the_plot_surface():
    assert PLT.drive_mat({"surface": "gravel"}) == PLT.DRIVE_GRAVEL_MAT
    assert PLT.drive_mat({"surface": "paving"}) == PLT.DRIVE_MAT
    assert PLT.drive_mat({}) == PLT.DRIVE_MAT
    from streetscape import materials as MT
    assert PLT.DRIVE_GRAVEL_MAT in MT.M and MT.M[PLT.DRIVE_GRAVEL_MAT].get("texture_set")


def test_crossing_edging_runs_along_the_sides_only():
    class B:
        def __init__(self):
            self.parts = []

        def add(self, layer, mat, V, UV, T, src=None, **kw):
            self.parts.append(SimpleNamespace(layer=layer, mat=mat, V=np.asarray(V), T=np.asarray(T)))
    poly = Polygon([(98.25, 3.52), (101.75, 3.52), (101.75, 8.0), (98.25, 8.0)])
    V = np.array([[x, y, 100.0] for x, y in poly.exterior.coords[:-1]])
    b = B()
    nt = PLT._crossing_edging(b, poly, V, np.zeros((0, 3), int), np.array([0.0, -1.0]), _carriage(), "t")
    assert nt > 0 and b.parts[0].mat == "curb_concrete"
    P = b.parts[0].V
    assert P[:, 1].min() >= 3.5 + PLT.CROSS_EDGE_ROAD_CLEAR_M - 0.8 - 1e-6      # never on the asphalt edge
    xs = np.unique(np.round(P[:, 0], 2))
    assert all(min(abs(x - 98.25), abs(x - 101.75)) <= 0.081 for x in xs)        # only along the two long sides
    assert shapely.Point(100.0, 3.6).within(poly)
