"""ADR 0221: triangles that carry no shape (P-23 wheel outlines, 2 m samples on straight paved edges)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import shapely
from shapely import affinity
from shapely.geometry import Point

from roads.gores import _triangulate
from streetscape import cycleways as CY
from streetscape import paved as PV

REPO = Path(__file__).resolve().parents[2]


def _tris(g):
    return sum(len(_triangulate(p, 0.5)[1]) for p in getattr(g, "geoms", [g]))


@pytest.mark.parametrize("small", [True, False])
def test_p23_symbol_is_cheap_and_keeps_its_shape(small):
    d = CY.P23_SMALL if small else CY.P23
    g = CY.p23_glyph(small)
    assert _tris(g) <= 200                                    # was 479 / 483 with 128-gon wheels
    # the wheel outline stays within 4 mm of the true ellipse (32-gon: a * (1 - cos(pi / 32)) on the long axis)
    L, H, lw = d["len"], d["h"], d["line"]
    a = 0.19 * H * (L / (H / 1.75)) + lw / 2
    b = 0.19 * (H - lw) + lw / 2
    assert a * (1 - np.cos(np.pi / (4 * CY.P23_WHEEL_QUAD_SEGS))) < 0.004
    # painted area within 1 % of the 128-gon symbol
    ref = affinity.scale(Point(0, 0).buffer(1.0, 32), a, b, origin=(0, 0))
    now = affinity.scale(Point(0, 0).buffer(1.0, CY.P23_WHEEL_QUAD_SEGS), a, b, origin=(0, 0))
    ring = lambda e: e.difference(e.buffer(-lw)).area         # noqa: E731
    assert ring(now) == pytest.approx(ring(ref), rel=0.01)
    assert len(g.interiors) >= 2 and g.is_valid


def _straight(n=21, step=2.0):
    P = np.column_stack([np.arange(n) * step, np.zeros(n)])
    return P, np.full(n, 140.0), np.zeros(n - 1, bool)


def test_edge_keep_drops_samples_that_carry_no_shape():
    P, Z, skip = _straight()
    assert PV._edge_keep(P, Z, skip).tolist() == [0, 20]
    Z2 = Z + 0.01 * P[:, 0]                                    # constant grade: still a straight line
    assert PV._edge_keep(P, Z2, skip).tolist() == [0, 20]


def test_edge_keep_follows_the_ground_and_the_outline():
    P, Z, skip = _straight()
    Z = Z.copy()
    Z[10] += 0.02                                              # a 2 cm bump must stay
    assert 10 in PV._edge_keep(P, Z, skip).tolist()
    Z[10] = 140.0 + 0.003                                      # under the height tolerance
    assert PV._edge_keep(P, Z, skip).tolist() == [0, 20]
    # every kept polyline stays within the tolerances of the dense one (a vertical curve and a 5 m radius arc)
    s = np.linspace(0, 40, 21)
    Zc = 140.0 + 0.0004 * (s - 20) ** 2
    k = PV._edge_keep(P, Zc, skip)
    assert np.max(np.abs(np.interp(s, s[k], Zc[k]) - Zc)) <= PV.EDGE_TOL_Z_M + 1e-9 and len(k) < 21
    ang = np.linspace(0, np.pi / 2, 33)
    A = 5.0 * np.column_stack([np.cos(ang), np.sin(ang)])
    ka = PV._edge_keep(A, np.full(33, 140.0), np.zeros(32, bool))
    dense, kept = shapely.LineString(A), shapely.LineString(A[ka])
    assert dense.hausdorff_distance(kept) <= PV.EDGE_TOL_XY_M + 1e-9


def test_edge_keep_keeps_built_skipped_boundaries_and_closed_rings():
    P, Z, skip = _straight()
    skip = skip.copy()
    skip[5:9] = True                                           # dense segments 5..8 meet a road: no edging there
    k = PV._edge_keep(P, Z, skip).tolist()
    assert k == [0, 5, 9, 20] and skip[np.array(k[:-1])].tolist() == [False, True, False]
    sq = np.array([[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]], float)
    ring = np.concatenate([np.linspace(sq[i], sq[i + 1], 6)[:-1] for i in range(4)] + [sq[:1]])
    kr = PV._edge_keep(ring, np.full(len(ring), 140.0), np.zeros(len(ring) - 1, bool))
    assert sorted(map(tuple, ring[kr].tolist())) == sorted(map(tuple, sq.tolist()))


def test_edges_mesh_has_no_flat_run_of_2m_segments():
    """A 60 x 30 m block-paved yard on a plane: the edging is 4 sides x 3 faces x 2 triangles, not 6 per 2 m."""
    from roads.meshing import MeshBuf
    buf = MeshBuf()
    item = {"id": "t", "poly": shapely.box(0, 0, 60, 30), "mat": "yard_paving"}
    zgrid = np.full((64, 96), 140.0)
    hf = _plane_hf()
    PV._edges(buf, item, zgrid, hf)
    edge = [p for p in buf.parts if p.src.endswith(":edge")]
    # 4 sides + 2 dense neighbours at each of the 3 corners inside the ring (the normal turns there; the ring's own
    # start has one-sided normals) = 10 segments of 3 faces; was (30 + 15) * 2 segments = 540 triangles
    assert sum(len(p.T) for p in edge) == 10 * 3 * 2
    top = max(edge, key=lambda p: len(p.T)).V
    outer = top[np.isclose(top[:, 2], 140.0 + PV.S.EDGING_H)]
    d = shapely.distance(shapely.points(outer[:, :2]), shapely.box(0, 0, 60, 30).exterior)
    # full 8 cm edging width everywhere but at the 4 corner vertices themselves (bisector normal, as before ADR 0221)
    assert np.sum(np.isclose(d, PV.S.EDGING_W, atol=1e-6)) >= len(d) - 5 - np.sum(np.isclose(d, 0.0, atol=1e-6))
    assert {p.mat for p in edge} == {"curb_concrete"}
    V = np.concatenate([p.V for p in edge])
    assert V[:, 2].max() == pytest.approx(140.0 + PV.S.EDGING_H) and V[:, 2].min() == pytest.approx(140.0 - PV.S.PAVED_FLANGE)


def _plane_hf():
    """The height-field handle `paved.bilinear` reads (west edge x0, north edge y1; 1 m cells)."""
    from types import SimpleNamespace
    return SimpleNamespace(x0=-16.0, y1=48.0)


def test_region_c_frame_budget_has_margin():
    qa = json.loads((REPO / "Data/Regions/bialystok-industrial-c/generated/streetscape_qa.json").read_text(encoding="utf-8"))
    worst = max(qa["mesh_budget"]["frame_estimate"], key=lambda f: f["tris_high"])
    assert worst["tris_high"] <= 1_990_000, (worst["camera"], worst["tris_high"])
