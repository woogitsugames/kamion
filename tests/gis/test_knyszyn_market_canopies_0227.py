"""Canopy geometry contract; photographs remain private, local references."""
import numpy as np
import pytest
from shapely.geometry import MultiPoint, Point, Polygon

from streetscape import knyszyn_market_0227 as market

ORIGIN = [761611., 612607.]
EAVES = [
    [[760787.,613341.7],[760794.,613342.4],[760800.7,613316.7],[760794.2,613315.]],
    [[760796.9,613301.9],[760803.8,613302.6],[760810.4,613276.],[760803.9,613274.7]],
    [[760803.8,613274.3],[760810.5,613275.1],[760817.3,613248.3],[760810.8,613247.]],
    [[760810.7,613246.8],[760817.4,613247.7],[760824.2,613221.4],[760817.7,613219.9]],
]


class Buffer:
    def __init__(self): self.parts = []
    def add(self, layer, mat, vertices, uv, triangles, src, UV1=None):
        self.parts.append((layer, mat, np.asarray(vertices), np.asarray(triangles), src))


def terrain(e, n): return np.zeros_like(e) + 125.


def overrides():
    return [{"kind": market.KIND, "canopies": [
        {"id": f"roof-{i}", "polygon_epsg2180": p, "solar_panels": i == 3}
        for i, p in enumerate(EAVES)]}]


def test_explicit_override_required_and_wrong_region_skipped():
    for region, data in (("knyszyn", []), ("other", overrides())):
        buf = Buffer()
        result = market.build(buf, region, ORIGIN, data, terrain, {})
        assert result["status"] == "skipped" and not buf.parts


def test_four_hipped_roofs_have_real_eaves_and_expected_solar_roof():
    buf = Buffer()
    result = market.build(buf, "knyszyn", ORIGIN, overrides(), terrain, {})
    assert result["status"] == "applied"
    assert len(result["canopies"]) == 4
    assert [o["solar_panels"] for o in result["canopies"]] == [False, False, False, True]
    assert all(26 < o["eave_length_m"] < 29 and 6 < o["eave_width_m"] < 8 for o in result["canopies"])
    roof_outlines = []
    for i in range(4):
        src = f"{market.ASSET_ID}:roof-{i}"
        for layer in market.LAYERS:
            roof = next(part for part in buf.parts if part[0] == layer and part[1] == "roof_metal_graphite" and part[4] == src)
            verts, triangles = roof[2], roof[3]
            assert len(triangles) == 6
            assert np.isclose(verts[:,2].min(), 125 + market.EAVE_M)
            assert np.isclose(verts[:,2].max(), 125 + market.EAVE_M + market.RIDGE_RISE_M)
            # All roof planes face upward and have positive area.
            normals = np.cross(verts[triangles[:,1]]-verts[triangles[:,0]],
                               verts[triangles[:,2]]-verts[triangles[:,0]])
            assert np.all(normals[:,2] > 0)
            expected = Polygon(np.asarray(EAVES[i])-np.asarray(ORIGIN)).minimum_rotated_rectangle
            assert expected.buffer(.001).covers(Polygon(verts[:4,:2]).convex_hull)
            if layer == "buildings":
                roof_outlines.append(Polygon(verts[:,:2]).convex_hull)
        assert any(p[0] == "collision" and p[4] == src for p in buf.parts)
        assert any(p[0] == "buildings_low" and p[1] == "glass" and p[4] == src for p in buf.parts) == (i == 3)
    for i, a in enumerate(roof_outlines):
        for b in roof_outlines[i+1:]:
            assert a.intersection(b).area < 1e-5


def test_collision_is_for_posts_and_low_has_no_extra_solar_modules():
    buf = Buffer()
    market.build(buf, "knyszyn", ORIGIN, overrides(), terrain, {})
    for i in range(4):
        src = f"{market.ASSET_ID}:roof-{i}"
        collision = next(p for p in buf.parts if p[0] == "collision" and p[4] == src)
        assert collision[1] == "collision_steel"
        assert np.isclose(collision[2][:,2].min(), 124.95)
        assert np.isclose(collision[2][:,2].max(), 125. + market.EAVE_M)
    low = next(p for p in buf.parts if p[0] == "buildings_low" and p[1] == "glass")
    high = next(p for p in buf.parts if p[0] == "buildings" and p[1] == "glass")
    assert len(low[3]) == 4 and len(high[3]) == 40


def test_posts_follow_local_ground_on_sloping_site():
    def sloped(e, n): return 125. + .02*np.asarray(e) + .01*np.asarray(n)
    buf = Buffer()
    market.build(buf, "knyszyn", ORIGIN, overrides(), sloped, {})
    collision = [p for p in buf.parts if p[0] == "collision"]
    for _, _, vertices, _, _ in collision:
        # Each box corner is within one post half-width of the sampled centre;
        # bottom vertices sit 5 cm below the local conformed surface.
        floor = sloped(vertices[:,0], vertices[:,1])
        near_ground = vertices[:,2] < floor
        assert near_ground.any()
        assert np.max(np.abs(vertices[near_ground,2] - (floor[near_ground]-.05))) < .01


def test_explicit_fences_leave_authored_gate_open():
    data = overrides()
    data[0]["fences"] = [
        {"id":"north", "points_epsg2180":[[760810.,613348.],[760816.8,613311.]]},
        {"id":"south", "points_epsg2180":[[760820.4,613304.],[760835.2,613222.]]},
    ]
    buf = Buffer()
    result = market.build(buf, "knyszyn", ORIGIN, data, terrain, {})
    assert [f["id"] for f in result["fences"]] == ["north", "south"]
    assert all(f["posts"] >= 2 and f["bays"] == f["posts"]-1 for f in result["fences"])
    gate_mid = (np.array([760816.8,613311.])+np.array([760820.4,613304.]))/2-np.array(ORIGIN)
    gate = Point(gate_mid).buffer(1.)
    for layer, mat, vertices, triangles, src in buf.parts:
        if ":fence:" not in src:
            continue
        assert mat in ("steel_painted", "collision_steel")
        # Test every primitive's horizontal footprint, including rails whose
        # endpoints alone could hide an accidental connection across a gate.
        for tri in triangles:
            footprint = MultiPoint(vertices[tri,:2]).convex_hull
            assert not footprint.intersects(gate)
    assert {p[0] for p in buf.parts if ":fence:" in p[4]} == {"buildings", "buildings_low", "collision"}


@pytest.mark.parametrize("change", ["missing", "duplicate", "bad_polygon", "nan_ground", "bad_solar", "bad_fence"])
def test_invalid_overrides_never_emit_partial_geometry(change):
    data = overrides()
    if change == "missing": data[0]["canopies"].pop()
    if change == "duplicate": data[0]["canopies"][1]["id"] = "roof-0"
    if change == "bad_polygon": data[0]["canopies"][2]["polygon_epsg2180"] = [[0,0]]
    if change == "bad_solar": data[0]["canopies"][2]["solar_panels"] = "true"
    if change == "bad_fence": data[0]["fences"] = [{"id":"closed", "points_epsg2180":[[1,1],[2,2],[1,1]]}]
    surf = (lambda e,n: np.full_like(e, np.nan)) if change == "nan_ground" else terrain
    buf = Buffer()
    with pytest.raises(ValueError): market.build(buf, "knyszyn", ORIGIN, data, surf, {})
    assert not buf.parts
