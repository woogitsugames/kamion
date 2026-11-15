"""Contract tests for the opt-in church landmark; visual acceptance is separate."""
import json
from pathlib import Path

import numpy as np
from shapely.geometry import LineString, Polygon

from streetscape import buildings_mesh as BM
from streetscape import knyszyn_church_0227 as church


ROOT = Path(__file__).resolve().parents[2]


class Buffer:
    def __init__(self):
        self.parts = []

    def add(self, layer, mat, vertices, uv, triangles, src, UV1=None):
        self.parts.append((layer, mat, np.asarray(vertices), np.asarray(triangles), src))


def test_region_and_source_are_required():
    fc = {"features": [{"id": church.BUILDING_ID}]}
    assert church.hero_targets("knyszyn", fc) == {church.BUILDING_ID: church.ASSET_ID}
    assert church.hero_targets("knyszyn-w", fc) == {}
    assert church.hero_targets("knyszyn", {"features": []}) == {}


def test_real_footprint_builds_both_tiers_with_lod2_silhouette():
    fc = json.loads((ROOT / "Data/Regions/knyszyn/buildings.geojson").read_text(encoding="utf-8"))
    feature = next(f for f in fc["features"] if f["id"] == church.BUILDING_ID)
    fc = {"features": [feature]}
    blds = BM.load(fc, [761611, 612607], [], hero=church.hero_targets("knyszyn", fc))
    buf, report = Buffer(), {}
    result = church.build(buf, "knyszyn", blds, lambda e, n: np.zeros_like(e) + 127.25, report)
    assert result["status"] == "applied"
    assert result["height_lod2_m"] == feature["properties"]["height_lod2_2017_m"]
    assert {p[0] for p in buf.parts} == set(church.LAYERS)
    assert {p[1] for p in buf.parts if p[0] == "buildings"} == {"plaster_white", "roof_tiles_red", "glass"}
    assert {p[1] for p in buf.parts if p[0] == "buildings_low"} == {"plaster_white", "roof_tiles_red", "plinth_dark"}
    for layer, mat, vertices, triangles, src in buf.parts:
        assert np.isfinite(vertices).all()
        assert triangles.min() >= 0 and triangles.max() < len(vertices)
        assert src == church.ASSET_ID
    assert max(float(p[2][:, 2].max()) for p in buf.parts) == 127.25 + result["height_lod2_m"]


def test_without_hero_target_no_duplicate_generic_geometry():
    fc = json.loads((ROOT / "Data/Regions/knyszyn/buildings.geojson").read_text(encoding="utf-8"))
    fc["features"] = [f for f in fc["features"] if f["id"] == church.BUILDING_ID]
    blds = BM.load(fc, [761611, 612607], [])
    buf = Buffer()
    result = church.build(buf, "knyszyn", blds, lambda e, n: np.zeros_like(e), {})
    assert result["status"] == "skipped"
    assert not buf.parts


def test_nave_roof_is_clipped_to_real_footprint_and_wound_upward():
    fc = json.loads((ROOT / "Data/Regions/knyszyn/buildings.geojson").read_text(encoding="utf-8"))
    fc["features"] = [f for f in fc["features"] if f["id"] == church.BUILDING_ID]
    b = BM.load(fc, [761611, 612607], [])[0]
    poly = b["poly"]
    rect = np.asarray(poly.minimum_rotated_rectangle.exterior.coords, float)[:4]
    edges = np.roll(rect, -1, axis=0) - rect
    i = int(np.argmax(np.linalg.norm(edges, axis=1)))
    along = edges[i] / np.linalg.norm(edges[i])
    normal = np.array([-along[1], along[0]])
    length = float(np.linalg.norm(edges[i]))
    width = float(np.linalg.norm(edges[(i + 1) % 4]))
    center = np.asarray(poly.minimum_rotated_rectangle.centroid.coords[0], float)
    acc = BM.Acc()
    church._gable(acc, "buildings", poly, center, along, normal, length, width, 5.85, 14.24)
    buf = Buffer()
    acc.flush(buf, "test")
    roof = next(p for p in buf.parts if p[1] == "roof_tiles_red")
    vertices, triangles = roof[2], roof[3]
    assert np.isclose(max(vertices[:, 2]), 14.24)
    total = 0.0
    for t in triangles:
        v = vertices[t]
        projected = Polygon(v[:, :2])
        total += projected.area
        assert projected.difference(poly).area < 1e-7
        assert np.cross(v[1] - v[0], v[2] - v[0])[2] > 0
    assert abs(total - poly.area) < 1e-6


def test_nave_windows_follow_real_footprint_walls():
    fc = json.loads((ROOT / "Data/Regions/knyszyn/buildings.geojson").read_text(encoding="utf-8"))
    fc["features"] = [f for f in fc["features"] if f["id"] == church.BUILDING_ID]
    poly = BM.load(fc, [761611, 612607], [])[0]["poly"]
    rect = np.asarray(poly.minimum_rotated_rectangle.exterior.coords, float)[:4]
    edges = np.roll(rect, -1, axis=0) - rect
    i = int(np.argmax(np.linalg.norm(edges, axis=1)))
    along = edges[i] / np.linalg.norm(edges[i])
    if along[0] > 0:
        along = -along
    normal = np.array([-along[1], along[0]])
    length, width = float(np.linalg.norm(edges[i])), float(np.linalg.norm(edges[(i + 1) % 4]))
    center = np.asarray(poly.minimum_rotated_rectangle.centroid.coords[0], float)
    for side in (-1, 1):
        out = normal * side
        for t in (-.25, .02, .29):
            target = center + along * (length * t) + out * (width / 2 + .03)
            a, b, wall_out = church._wall_window(poly, target, out)
            # The whole opening, not just its centre, lies on one actual wall.
            assert LineString([a, b]).difference(poly.boundary.buffer(1e-7)).length < 1e-6
            assert np.isclose(np.linalg.norm(b - a), 1.5)
            assert np.dot(wall_out, out) > .5

