"""CRS round-trip and datum checks (EPSG:2180 <-> WGS84, vertical EVRF2007)."""

import math

import pytest
from pyproj import CRS, Transformer


def test_roundtrip_2180_wgs84_sub_mm(region):
    fwd = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)
    inv = Transformer.from_crs("EPSG:4326", "EPSG:2180", always_xy=True)
    x0, y0, x1, y1 = region.bbox
    pts = [(x0, y0), (x1, y0), (x0, y1), (x1, y1), region.origin]
    for x, y in pts:
        lon, lat = fwd.transform(x, y)
        assert 22.9 < lon < 23.3 and 53.0 < lat < 53.3, "tile must be in Białystok"
        xb, yb = inv.transform(lon, lat)
        assert math.hypot(xb - x, yb - y) < 1e-3


def test_origin_is_tile_centre(region):
    x0, y0, x1, y1 = region.bbox
    assert region.origin == ((x0 + x1) / 2, (y0 + y1) / 2)
    assert region.width == region.height == 2048.0


def test_compound_crs_is_pl1992_plus_evrf2007():
    import regions
    c = CRS(regions.COMPOUND_CRS)
    assert c.is_compound
    h, v = c.sub_crs_list
    assert h.to_epsg() == 2180
    assert v.to_epsg() == 9651
    assert "EVRF2007" in v.name


def test_derive_tile_reproduces_registry(region):
    import regions
    # route bounds recorded in regions.py docstring (from analyze_candidates route C)
    bbox, origin = regions.derive_tile((777258.6, 595528.7, 778732.0, 596917.3))
    assert bbox == region.bbox and origin == region.origin


@pytest.mark.parametrize("x,y", [(777995.0, 596223.0), (776971.0, 597247.0)])
def test_heightmap_node_mapping(region, x, y):
    """Node (i, j) <-> (x, y) mapping documented in terrain.json is integer-exact."""
    x0, _, _, y1 = region.bbox
    i, j = x - x0, y1 - y
    assert i == int(i) and j == int(j)
