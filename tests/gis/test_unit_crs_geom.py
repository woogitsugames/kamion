"""Unit tests (no Data/raw): CRS transforms, local frame, polyline offsetting/arcs, triangulation.

Run: uv run --project tools/worldgen pytest tests/gis -q -m unit
"""

import math

import numpy as np
import pytest
from pyproj import Transformer

from roads import network
from roads.geom import Polyline, cumlen, ear_clip, polyline_intersections, polygon_area, resample, seg_intersect

pytestmark = pytest.mark.unit

ORIGIN_2180 = (777995.0, 596223.0)   # region floating-origin anchor, EPSG:2180 metres


# ---------------------------------------------------------------- CRS / local frame

def test_epsg2180_axis_order_and_roundtrip():
    fwd = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)
    inv = Transformer.from_crs("EPSG:4326", "EPSG:2180", always_xy=True)
    x, y = ORIGIN_2180
    lon, lat = fwd.transform(x, y)
    assert 22.9 < lon < 23.3 and 53.0 < lat < 53.3   # Białystok tile
    xb, yb = inv.transform(lon, lat)
    assert math.hypot(xb - x, yb - y) < 1e-3           # sub-mm round trip


def _graph_at_origin():
    ox, oy = ORIGIN_2180
    nodes = [
        {"id": "n0", "x": ox, "y": oy},
        {"id": "n1", "x": ox + 10.0, "y": oy},          # 10 m east
        {"id": "n2", "x": ox, "y": oy + 10.0},          # 10 m north
    ]
    edge = {"id": "e1", "from": "n0", "to": "n1",
            "geometry": [[ox, oy], [ox + 10.0, oy]],
            "attrs": {"highway": {"v": "residential"}, "oneway": {"v": "no"}, "lanes": {"v": 2}}}
    return {"nodes": nodes, "edges": [edge]}


def test_local_frame_is_east_north_metres():
    """Local frame (ADR 0003): E = x - origin.x, N = y - origin.y, 1 unit = 1 m; engine X=east, Z=north."""
    net = network.load(_graph_at_origin(), ORIGIN_2180)
    ox, oy = ORIGIN_2180
    assert np.allclose(net.nodes["n0"]["xy"], [0.0, 0.0])
    assert np.allclose(net.nodes["n1"]["xy"], [10.0, 0.0], atol=1e-9)   # east  -> +X
    assert np.allclose(net.nodes["n2"]["xy"], [0.0, 10.0], atol=1e-9)   # north -> +Z
    # 1 unit = 1 m: local distance equals EPSG:2180 distance
    d_local = math.hypot(*(net.nodes["n1"]["xy"] - net.nodes["n2"]["xy"]))
    assert math.hypot(10.0, 10.0) == pytest.approx(d_local, abs=1e-9)
    g = net.chains[0].raw
    assert cumlen(g)[-1] == pytest.approx(10.0, abs=1e-9)


# ---------------------------------------------------------------- polyline offset / arcs

def test_offset_straight_polyline_exact_and_length_preserving():
    p = np.array([[0.0, 0.0], [100.0, 0.0]])
    line = Polyline(p)
    s = np.linspace(0, 100, 51)
    left = line.offset_point(s, 3.5)
    right = line.offset_point(s, -3.5)
    assert np.allclose(left[:, 0], s, atol=1e-9) and np.allclose(left[:, 1], 3.5, atol=1e-9)
    assert np.allclose(right[:, 1], -3.5, atol=1e-9)
    # parallel offset of a straight segment keeps its length
    off = line.offset_point(s, 3.5)
    assert cumlen(off)[-1] == pytest.approx(line.length, rel=1e-9)
    assert np.isfinite(off).all()


def test_offset_circular_arc_radius_and_symmetry():
    R = 50.0
    t = np.linspace(0, math.pi / 2, 64)
    arc = np.column_stack([R * np.cos(t), R * np.sin(t)])
    line = Polyline(arc)
    s = np.linspace(0, line.length, 40)
    inn = line.offset_point(s, 2.0)    # left of a CCW arc points toward the centre
    out = line.offset_point(s, -2.0)
    assert np.isfinite(out).all() and np.isfinite(inn).all()
    r_out = np.hypot(out[:, 0], out[:, 1])
    r_in = np.hypot(inn[:, 0], inn[:, 1])
    assert r_out == pytest.approx(np.full_like(r_out, R + 2.0), abs=2e-2)
    assert r_in == pytest.approx(np.full_like(r_in, R - 2.0), abs=2e-2)
    # symmetry: outward/inward offsets mirror about the centreline
    mid = line.offset_point(s, 0.0)
    assert np.hypot(*(out - mid).T) == pytest.approx(np.hypot(*(mid - inn).T), abs=1e-9)
    # offset arc length scales with the radius (length ratio preserved, no NaN)
    assert cumlen(out)[-1] == pytest.approx((R + 2.0) / R * line.length, rel=2e-2)
    # curvature of the arc is ~1/R (interior samples; np.gradient degrades at the endpoints)
    k = line.curvature(s)[2:-2]
    assert k == pytest.approx(np.full_like(k, 1.0 / R), rel=0.1)


def test_offset_polyline_no_self_intersection_on_straight_and_arc():
    for p in (np.array([[0.0, 0.0], [60.0, 0.0]]),
              np.column_stack([50 * np.cos(np.linspace(0, 1.2, 40)), 50 * np.sin(np.linspace(0, 1.2, 40))])):
        line = Polyline(p)
        s = np.linspace(0, line.length, 80)
        off = line.offset_point(s, 3.0)
        self_x = _self_intersections(off)
        assert self_x == [], f"offset polyline self-intersects: {self_x[:3]}"


def _self_intersections(poly):
    """Non-adjacent self-intersections of a polyline (closed if first==last within 1e-6)."""
    n = len(poly)
    closed = n > 2 and math.hypot(*(poly[0] - poly[-1])) < 1e-6
    out = []
    for i in range(n - 1):
        for j in range(i + 2, n - 1):
            if closed and i == 0 and j == n - 2:
                continue
            r = seg_intersect(poly[i], poly[i + 1], poly[j], poly[j + 1])
            if r is not None:
                out.append((i, j, r[2]))
    return out


def test_seg_intersect_and_polyline_intersections():
    r = seg_intersect(np.array([0.0, 0.0]), np.array([4.0, 0.0]),
                      np.array([2.0, -1.0]), np.array([2.0, 1.0]))
    assert r is not None and np.allclose(r[2], [2.0, 0.0])
    assert seg_intersect(np.array([0.0, 0.0]), np.array([1.0, 0.0]),
                         np.array([0.0, 1.0]), np.array([1.0, 1.0])) is None  # parallel
    a = np.array([[0.0, 0.0], [10.0, 0.0]])
    b = np.array([[5.0, -5.0], [5.0, 5.0]])
    xs = polyline_intersections(a, b)
    assert len(xs) == 1 and np.allclose(xs[0][2], [5.0, 0.0])
    assert xs[0][0] == pytest.approx(5.0) and xs[0][1] == pytest.approx(5.0)
    # parallel polylines do not intersect
    assert polyline_intersections(a, a + np.array([0.0, 3.0])) == []


def test_resample_keeps_endpoints_and_spacing():
    p = np.array([[0.0, 0.0], [30.0, 0.0], [30.0, 40.0]])
    q = resample(p, 2.0)
    assert np.allclose(q[0], p[0]) and np.allclose(q[-1], p[-1])
    d = np.hypot(*np.diff(q, axis=0).T)
    assert (d <= 2.0 + 1e-9).all() and d.min() > 1.5


# ---------------------------------------------------------------- triangulation

@pytest.mark.parametrize("poly", [
    np.array([[0.0, 0.0], [4.0, 0.0], [4.0, 3.0], [0.0, 3.0]]),                       # rectangle
    np.array([[0.0, 0.0], [4.0, 0.0], [4.0, 1.0], [1.0, 1.0], [1.0, 3.0], [0.0, 3.0]]),  # L-shape
    np.array([[0.0, 0.0], [4.0, 0.0], [5.0, 2.0], [4.0, 4.0], [0.0, 4.0], [-1.0, 2.0]]),  # concave
])
def test_ear_clip_triangulates_simple_polygon(poly):
    tris = ear_clip(poly)
    assert len(tris) == len(poly) - 2
    area = 0.0
    for i0, i1, i2 in tris:
        a, b, c = poly[i0], poly[i1], poly[i2]
        cross = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        assert cross > 0, "triangle not CCW"
        area += 0.5 * cross
    assert area == pytest.approx(abs(polygon_area(poly)), rel=1e-9)   # full cover, no overlap
    assert ear_clip(poly) == tris                                     # deterministic


def test_polygon_area_sign_and_value():
    sq = np.array([[0.0, 0.0], [2.0, 0.0], [2.0, 2.0], [0.0, 2.0]])
    assert polygon_area(sq) == pytest.approx(4.0)
    assert polygon_area(sq[::-1]) == pytest.approx(-4.0)
