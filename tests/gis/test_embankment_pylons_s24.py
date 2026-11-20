"""Drive review s24 #13 / #15: no Unity, full world build or raw data needed."""
from types import SimpleNamespace

import numpy as np
import pytest
import shapely

from roads import standards as S
from streetscape import far_field as FF
from terrain_mesh import conform as CF


def diagonal_road(angle=23.0, fill=True, grade=0.0):
    jj, ii = np.mgrid[:129, :129]
    hf = SimpleNamespace(x0=-64.0, y1=64.0,
                         z=np.full((129, 129), 96.0 if fill else 104.0))
    xy = np.column_stack([(ii - 64).ravel(), (64 - jj).ravel()])
    yaw = np.deg2rad(angle)
    along = np.array([np.cos(yaw), np.sin(yaw)])
    out = np.array([-along[1], along[0]])
    corners = [along * a + out * b for a, b in ((-150, -5.3), (150, -5.3), (150, 5.3), (-150, 5.3))]
    footprint = shapely.Polygon(corners)
    mask = shapely.intersects_xy(footprint, xy[:, 0], xy[:, 1]).reshape(hf.z.shape)
    road = np.where(mask, 100.0 + grade * (xy @ along).reshape(hf.z.shape), -np.inf)
    return hf, road, mask, footprint


@pytest.mark.parametrize("angle", [7.0, 23.0, 45.0, 83.0])
@pytest.mark.parametrize("fill", [True, False])
def test_diagonal_batter_matches_continuous_edge_and_limits_neighbour_step(angle, fill):
    hf, road, mask, footprint = diagonal_road(angle, fill)
    before, _ = CF.conform(hf, road, mask)
    z, d = CF.conform(hf, road, mask, footprint=footprint)
    z = CF.tidy(z, road, mask, d, smooth_slopes=False)
    jj, ii = np.indices(z.shape)
    exact = shapely.distance(shapely.points(hf.x0 + ii, hf.y1 - jj), footprint)
    run = np.maximum(0., exact - S.BERM_W) / S.EMBANKMENT_SLOPE
    expected = np.clip(hf.z, 99.97 - run, 99.97 + run)
    band = ~mask & (exact > 1.5) & (exact < 5.0)
    assert np.max(np.abs(before[band] - expected[band])) > 0.1  # regression really reproduced
    assert np.max(np.abs(z[band] - expected[band])) < 1e-10
    assert np.array_equal(z[mask], road[mask] - S.TERRAIN_UNDER_ROAD)
    assert np.isfinite(z).all() and np.isfinite(d).all()
    # Across a 1 m edge the designed 1:S slope cannot jump more than 1/S m.
    for axis in (0, 1):
        a = [slice(None), slice(None)]
        b = a.copy()
        a[axis], b[axis] = slice(None, -1), slice(1, None)
        pairs = band[tuple(a)] & band[tuple(b)]
        assert np.abs(np.diff(z, axis=axis))[pairs].max() <= 1.0 / S.EMBANKMENT_SLOPE + 1e-10


def test_graded_batter_is_finite_keeps_surface_and_distant_nmt():
    hf, road, mask, footprint = diagonal_road(grade=0.04)
    source = road.copy()
    z, d = CF.conform(hf, road, mask, footprint=footprint)
    assert np.array_equal(road, source)
    assert np.array_equal(z[mask], road[mask] - S.TERRAIN_UNDER_ROAD)
    assert np.array_equal(z[d > 20], hf.z[d > 20])
    assert np.isfinite(CF.tidy(z, road, mask, d, smooth_slopes=False)).all()


def test_empty_footprint_and_no_roads():
    hf, road, mask, _ = diagonal_road()
    a = CF.conform(hf, road, mask)
    b = CF.conform(hf, road, mask, footprint=shapely.Polygon())
    for x, y in zip(a, b):
        assert np.array_equal(x, y)
    z, d = CF.conform(hf, np.full_like(road, -np.inf), np.zeros_like(mask), footprint=shapely.Polygon())
    assert np.array_equal(z, hf.z) and not d.any()


def test_dk65_10_road_mesh_is_unchanged_by_final_conform():
    """Real committed road geometry; synthetic fill below it, no world build/NMT."""
    import hashlib
    from qa.check_piers_vs_roads import flat_world
    from streetscape.paved import road_footprint_polygon

    w = flat_world("dk65-10")
    parts = [p for p in w.buf.parts if p.layer == "road"]

    def digest():
        return hashlib.sha256(b"".join(p.V.tobytes() + p.T.tobytes() for p in parts)).hexdigest()

    original = digest()
    hf = SimpleNamespace(x0=-128., y1=128., z=np.zeros((257, 257)))
    road, mask = CF.rasterise(parts, hf)
    assert mask.any()
    hf.z[:] = road[mask].min() - 4.
    poly = road_footprint_polygon(parts)
    before, _ = CF.conform(hf, road, mask)
    z, d = CF.conform(hf, road, mask, footprint=poly)
    z = CF.tidy(z, road, mask, d, smooth_slopes=False)
    band = ~mask & (d > 2.) & (d < 5.)
    assert np.max(np.abs(before[band] - z[band])) > .1
    assert np.isfinite(z).all()
    assert digest() == original


def pylon_primitive(tier, yaw):
    elev = FF.BorderElevation(1024., [100., 100.], [100., 100.], [100., 100.], [100., 100.])
    sectors = {s: FF.SectorBuilder(s) for s in FF.SECTORS}
    FF._add_pylon(sectors, {"e": 1200., "n": 0., "h": 28.}, elev, 1024., tier, yaw=yaw)
    return sectors["far_east"].primitives()[0]


@pytest.mark.parametrize("tier", ["Low", "High"])
@pytest.mark.parametrize("yaw", [0., 0.4, np.pi / 4, np.pi / 2])
def test_pylon_has_open_lattice_and_crossarms_in_every_tier(tier, yaw):
    p = pylon_primitive(tier, yaw)
    v, t = p["V"], p["T"]
    assert np.isfinite(v).all()
    assert t.max() < len(v) < 65536
    assert 100 < len(t) <= 224  # bounded lightweight geometry, also with hundreds of towers
    assert set(p["COL"][:, 3]) == {0.0}
    assert p["mat"] == "far_field_buildings"
    # Look from both cardinal directions: solid fins filled the whole shaft;
    # lattice must have multiple sky holes in its lower 60% at every yaw.
    for horizontal in (0, 1):
        xy = v[:, [horizontal, 2]]
        tri = xy[t]
        a, b = tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]
        area2 = a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0]
        projection = shapely.union_all(shapely.polygons(tri[np.abs(area2) > 1e-10]))
        mid = (xy[:, 0].min() + xy[:, 0].max()) / 2
        z0, z1 = v[:, 2].min(), v[:, 2].max()
        shaft = shapely.box(mid - 1., z0 + 1., mid + 1., z0 + (z1 - z0) * 0.6)
        assert projection.intersection(shaft).area / shaft.area < 0.55
        assert len(shapely.get_parts(shaft.difference(projection))) >= 3
    # Arms extend much farther than the square foot in their local axis.
    arm_axis = np.array([-np.sin(yaw), np.cos(yaw)])
    local = v[:, :2] @ arm_axis
    assert np.ptp(local) > 8.0
    n = np.cross(v[t[:, 1]] - v[t[:, 0]], v[t[:, 2]] - v[t[:, 0]])
    assert (np.linalg.norm(n, axis=1) > 1e-10).all()
