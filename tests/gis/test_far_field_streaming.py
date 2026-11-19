"""Far-field buildings must never stand in for the streamed driving corridor."""
import json
import math
from types import SimpleNamespace

import numpy as np
import pytest
from shapely.geometry import LineString, Point, Polygon, box

import regions
from streetscape import far_field as ff


@pytest.fixture
def reserved(tmp_path, monkeypatch):
    # Nonzero global origin catches a missing/wrong-sign local-frame translation.
    origin = (770000.0, 600000.0)
    registry = {
        "home": SimpleNamespace(bbox=(768976, 598976, 771024, 601024), origin=origin),
        "future": SimpleNamespace(bbox=(771024, 598976, 773072, 601024), origin=(772048, 600000)),
    }
    monkeypatch.setattr(regions, "REGIONS", registry)
    monkeypatch.setattr(ff, "REPO", tmp_path)
    route = tmp_path / "Data/Regions/home/route_start.json"
    route.parent.mkdir(parents=True)
    route.write_text(json.dumps({"points_en": [[-1000, 1000], [1000, 1000]]}))
    return ff.streaming_building_exclusion(*origin)[0], route, origin


def source(rect, typ="block", height=27):
    return dict(id="regression", rect=list(box(*rect).exterior.coords)[:4],
                typ=typ, h=height, area=1000, storeys=8)


def primitives(building, tier, exclusion=None):
    sectors = {name: ff.SectorBuilder(name) for name in ff.SECTORS}
    sky = ff.SectorBuilder(ff.SKYLINE, uv1_flag=ff.SKYLINE_FLAG_CLAMP)
    elev = ff.BorderElevation(1024, *([[135, 135]] * 4))
    ff._add_building(sectors, building, elev, 1024, tier, exclusion=exclusion, skyline=sky)
    return [p for sector in [*sectors.values(), sky] for p in sector.primitives()]


@pytest.mark.parametrize("tier", ["Low", "High"])
@pytest.mark.parametrize("typ", ["block", "office", "hall", "house"])
def test_future_tile_has_no_proxy_even_without_import_or_ready_state(reserved, tier, typ):
    exclusion, _, _ = reserved
    # Including tall buildings normally moved into the always-visible skyline.
    assert not primitives(source((1050, 0, 1120, 20), typ), tier, exclusion)


@pytest.mark.parametrize("rect", [
    (-30, 1190, 30, 1210),  # within 400 m of the real route
    (-30, 1390, 30, 1410),  # centroid outside, but footprint enters clearance
    (-30, 1399, 30, 1400),  # contact also excluded
])
def test_route_clearance_uses_whole_footprint(reserved, rect):
    exclusion, _, _ = reserved
    assert not ff.building_rectangle_outside_region(source(rect)["rect"], 1024, exclusion)


def test_clearance_includes_points_between_round_buffer_vertices(reserved):
    exclusion, _, _ = reserved
    angle = math.pi / 64
    point = Point(-1000 - 399.99 * math.cos(angle), 1000 + 399.99 * math.sin(angle))
    assert exclusion.covers(point), "inscribed buffer chords must not shrink the 400 m reservation"


def test_registry_text_hash_is_independent_of_checkout_line_endings(tmp_path):
    path = tmp_path / "regions.py"
    path.write_bytes(b"REGIONS = {\n}\n")
    lf = ff._sha256(path)
    path.write_bytes(b"REGIONS = {\r\n}\r\n")
    assert ff._sha256(path) == lf


@pytest.mark.parametrize("tier", ["Low", "High"])
def test_compression_cannot_move_external_building_into_route(reserved, tier):
    exclusion, _, _ = reserved
    building = source((-30, 1450, 30, 1470))
    assert not Polygon(building["rect"]).intersects(exclusion), "raw geometry is clear"
    assert not ff.building_rectangle_outside_region(building["rect"], 1024, exclusion)
    assert not primitives(building, tier, exclusion), "mesh path must repeat compressed check"


def test_compression_cannot_move_external_building_into_future_tile(reserved):
    exclusion, _, _ = reserved
    building = source((3300, 0, 3370, 20))
    assert not Polygon(building["rect"]).intersects(exclusion)
    assert not ff.building_rectangle_outside_region(building["rect"], 1024, exclusion)


def test_route_edit_changes_exclusion_without_gis_cache_rebuild(reserved):
    before, route, origin = reserved
    _, hashes_before = ff.streaming_building_exclusion(*origin)
    route.write_text(json.dumps({"points_en": [[-1000, -1000], [1000, -1000]]}))
    after, hashes_after = ff.streaming_building_exclusion(*origin)
    north = box(-30, 1190, 30, 1210)
    assert north.intersects(before) and not north.intersects(after)
    assert hashes_before != hashes_after


@pytest.mark.parametrize("tier", ["Low", "High"])
@pytest.mark.parametrize("typ", ["block", "office", "hall", "house"])
def test_retained_buildings_have_roof_without_windows(reserved, tier, typ):
    exclusion, _, _ = reserved
    p, = primitives(source((-60, -1140, 0, -1110), typ, height=12), tier, exclusion)
    vertices, triangles, colors = (np.asarray(p[k]) for k in ("V", "T", "COL"))
    assert p["mat"] == "far_field_buildings"
    roof_faces = []
    for triangle in triangles:
        a, b, c = vertices[triangle]
        normal = np.cross(b - a, c - a)
        if normal[2] > 0.01:
            roof_faces.append(triangle)
    assert roof_faces, "Low must have actual roof triangles with upward winding"
    roof_vertices = np.unique(roof_faces)
    assert np.all(colors[roof_vertices, 3] == 0), "window shader never touches roofs"
    assert colors[roof_vertices, :3].mean() < 0.25, "subdued roof palette"
    if typ in ("office", "block"):
        windowed = colors[:, 3] >= 0.6
        assert windowed.any()
        assert vertices[windowed, 2].max() < vertices[:, 2].max(), "opaque roof fascia above windows"


def test_dk65_04_all_registered_routes_are_reserved():
    reg = regions.get("dk65-04")
    exclusion, inputs = ff.streaming_building_exclusion(*reg.origin)
    assert len(inputs) > 30, "test actual corridor inputs rather than a fixed C exit"
    route_paths = [key for key in inputs if key.endswith("route_start.json")]
    for key in route_paths:
        route = json.loads((ff.REPO / key).read_text(encoding="utf-8"))
        owner = regions.get(route["region"])
        dx, dy = np.asarray(owner.origin) - reg.origin
        line = LineString([(e + dx, n + dy) for e, n in route["points_en"]])
        # Slightly inside the buffer avoids roundoff from unioning coincident edges.
        assert line.buffer(ff.STREAMING_ROUTE_CLEARANCE_M - 0.01).difference(exclusion).area < 1e-5, key


def test_mesh_build_filters_cached_gis_and_apron_but_keeps_source_audit(reserved, monkeypatch, tmp_path):
    _, _, origin = reserved
    buildings = [source((1050, 0, 1120, 20)), source((-30, 1450, 30, 1470)),
                 source((-60, -1140, 0, -1110))]
    for index, building in enumerate(buildings):
        building.update(id=f"b{index}", height_source="fixture")
    gis = dict(buildings=buildings, forests=[], chimneys=[], pylons=[], power_lines=[],
               sources_sha256={}, powiaty=[], powiaty_missing=[], osm_lonlat_window=[],
               boundary_exclusions={}, lod1_height_audit={}, building_height_sources={"fixture": 3})
    monkeypatch.setattr(ff.pipeline, "REGIONS", tmp_path / "Data/Regions")
    monkeypatch.setattr(ff.pipeline, "load_region", lambda _: dict(origin=dict(x=origin[0], y=origin[1]),
                                                                  bbox=dict(width_m=2048)))
    monkeypatch.setattr(ff.BorderElevation, "from_region", lambda *a, **kw: ff.BorderElevation(1024, *([[135, 135]] * 4)))
    monkeypatch.setattr(ff, "extract_ring_gis", lambda *a, **kw: gis)
    monkeypatch.setattr(ff, "_corridor_treelines", lambda *a: [])
    monkeypatch.setattr(ff, "region_landmark_stacks", lambda *a: [])
    masks = []
    monkeypatch.setattr(ff, "build_apron_masks", lambda data, *a: masks.append(data) or {})
    qa = ff.build_far_field("home", out_root=tmp_path / "mesh")
    assert qa["streaming_building_policy"]["excluded_buildings"] == 2
    assert qa["streaming_building_policy"]["retained_buildings"] == 1
    assert [b["id"] for b in masks[0]["buildings"]] == ["b2"]
    assert qa["feature_counts"]["buildings"] == sum(qa["building_height_sources"].values()) == 3
    assert len(gis["buildings"]) == 3, "do not mutate the source GIS cache/audit"
    for tier in ("Low", "High"):
        assert qa["tiers"][tier]["total_triangles"] > 0
    manifest = json.loads((tmp_path / "Data/SourceManifests/home-far-field.manifest.json").read_text())
    assert manifest["streaming_building_policy"] == qa["streaming_building_policy"]


def test_palettes_use_real_tile_materials():
    assert ff.PALETTE_OFFICE == [tuple(ff.SM.M[name]["color"][:3]) for name in
                                ("plaster_light", "plaster_grey", "plaster_beige", "plaster_white", "brick_red")]
    assert ff.COL_ROOF_FLAT == tuple(ff.SM.M["roof_membrane"]["color"][:3])
