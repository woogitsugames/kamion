"""Unit tests (no Data/raw): joining segments at junctions - synthetic T-junction built in memory.

Covers roads.network.load + roads.junctions.build_junctions on a 3-arm T (residential, 100 m arms):
corner kinds, kerb-return fillet arcs (radius, tangency to gutters), trims, patch boundary
(simple polygon, CCW), and determinism of the whole construction.

Run: uv run --project tools/worldgen pytest tests/gis -q -m unit
"""

import math

import numpy as np
import pytest

from roads import network
from roads import standards as S
from roads.geom import polygon_area
from roads.junctions import build_junctions, chain_ends

pytestmark = pytest.mark.unit

ORIGIN = (777995.0, 596223.0)


def _t_graph():
    ox, oy = ORIGIN
    nodes = [
        {"id": "n0", "x": ox, "y": oy},
        {"id": "n1", "x": ox - 100.0, "y": oy},
        {"id": "n2", "x": ox + 100.0, "y": oy},
        {"id": "n3", "x": ox, "y": oy - 100.0},
    ]

    def edge(eid, a, b, pts):
        return {"id": eid, "from": a, "to": b,
                "geometry": [[ox + px, oy + py] for px, py in pts],
                "attrs": {"highway": {"v": "residential"}, "oneway": {"v": "no"}, "lanes": {"v": 2}}}

    edges = [edge("e1", "n0", "n1", [(0, 0), (-100, 0)]),
             edge("e2", "n0", "n2", [(0, 0), (100, 0)]),
             edge("e3", "n0", "n3", [(0, 0), (0, -100)])]
    return {"nodes": nodes, "edges": edges}


@pytest.fixture(scope="module")
def t_net():
    return network.load(_t_graph(), ORIGIN)


@pytest.fixture(scope="module")
def t_junction(t_net):
    juncs = build_junctions(t_net)
    assert len(juncs) == 1
    return juncs[0]


def test_chain_ends_finds_the_degree3_node(t_net):
    ends = chain_ends(t_net)
    assert {n: len(v) for n, v in ends.items()} == {"n0": 3, "n1": 1, "n2": 1, "n3": 1}


def test_t_junction_has_three_arms_and_three_corners(t_net, t_junction):
    assert len(t_junction.arms) == 3
    assert len(t_junction.corners) == 3
    kinds = sorted(c.kind for c in t_junction.corners)
    assert kinds == ["fillet", "fillet", "straight"]   # two kerb returns + the straight-through corner


def test_fillet_arc_radius_tangency_and_no_nan(t_junction):
    fillets = [c for c in t_junction.corners if c.kind == "fillet"]
    assert len(fillets) == 2
    for c in fillets:
        assert c.R >= 0.75
        assert c.arc is not None and len(c.arc) >= 2
        assert np.isfinite(c.arc).all() and np.isfinite(c.center).all()
        # every arc point lies on the circle around the fillet centre
        r = np.hypot(*(c.arc - c.center).T)
        assert r == pytest.approx(np.full_like(r, c.R), abs=1e-6)
        # arc endpoints are the tangent points on the two arm gutters
        A, B = t_junction.arms[c.k], t_junction.arms[c.k1]
        assert np.allclose(c.arc[0], A.gutter(c.tau_k, +1), atol=1e-6)
        assert np.allclose(c.arc[-1], B.gutter(c.tau_k1, -1), atol=1e-6)


def test_trims_respect_minimum_and_cover_corners(t_junction):
    assert len(t_junction.trims) == 3
    for i, tau in t_junction.trims.items():
        assert tau >= S.JUNCTION_MIN_TRIM
        corner_taus = [max(c.tau_k, 0.0) if c.k == i else max(c.tau_k1, 0.0)
                       for c in t_junction.corners if i in (c.k, c.k1)]
        assert tau >= max(corner_taus) - 1e-9


def test_patch_boundary_is_simple_ccw_and_finite(t_junction):
    b = np.array([p for p, _ in t_junction.boundary])
    assert len(b) >= 3 and np.isfinite(b).all()
    assert polygon_area(b) > 0, "boundary must be CCW"
    # closed loop: no self-intersections between non-adjacent edges
    loop = np.vstack([b, b[0]])
    n = len(loop) - 1
    for i in range(n):
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue
            from roads.geom import seg_intersect
            r = seg_intersect(loop[i], loop[i + 1], loop[j], loop[j + 1])
            assert r is None, f"boundary self-intersection at edges {i}, {j}: {r[2] if r else ''}"


def test_junction_construction_is_deterministic():
    j1 = build_junctions(network.load(_t_graph(), ORIGIN))[0]
    j2 = build_junctions(network.load(_t_graph(), ORIGIN))[0]
    assert j1.trims == j2.trims
    assert len(j1.boundary) == len(j2.boundary)
    assert all(np.array_equal(p1, p2) and t1 == t2 for (p1, t1), (p2, t2) in zip(j1.boundary, j2.boundary))
    for c1, c2 in zip(j1.corners, j2.corners):
        assert c1.kind == c2.kind and c1.R == c2.R and c1.tau_k == c2.tau_k and c1.tau_k1 == c2.tau_k1
        if c1.arc is None:
            assert c2.arc is None
        else:
            assert np.array_equal(c1.arc, c2.arc)


def test_arm_chain_trims_are_set(t_net, t_junction):
    for i, a in enumerate(t_junction.arms):
        t = t_junction.trims[i]
        assert (a.end == "a" and a.chain.t_a >= t - 1e-9) or (a.end == "b" and a.chain.t_b >= t - 1e-9)
