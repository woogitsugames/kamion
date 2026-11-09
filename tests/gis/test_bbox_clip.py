"""Everything written for the region must lie inside its bbox (clip correctness)."""

import json

import shapely

from conftest import REGION_DIR

EPS = 1e-3


def inside(region, x, y):
    x0, y0, x1, y1 = region.bbox
    return x0 - EPS <= x <= x1 + EPS and y0 - EPS <= y <= y1 + EPS


def test_graph_nodes_and_vertices_inside(region, graph):
    assert graph["bbox"] == list(region.bbox)
    assert all(inside(region, n["x"], n["y"]) for n in graph["nodes"])
    for e in graph["edges"]:
        assert all(inside(region, x, y) for x, y in e["geometry"]), e["id"]


def test_boundary_nodes_lie_on_tile_edge(region, graph):
    x0, y0, x1, y1 = region.bbox
    b = [n for n in graph["nodes"] if n.get("boundary")]
    assert b, "expected roads crossing the tile edge"
    for n in b:
        d = min(abs(n["x"] - x0), abs(n["x"] - x1), abs(n["y"] - y0), abs(n["y"] - y1))
        assert d < 0.01, n


def test_edges_reference_existing_nodes_and_lengths(graph):
    ids = {n["id"] for n in graph["nodes"]}
    for e in graph["edges"]:
        assert e["from"] in ids and e["to"] in ids
        ln = shapely.LineString(e["geometry"]).length
        assert abs(ln - e["length_m"]) < 0.01
        assert e["length_m"] > 0


def test_every_attr_has_provenance(graph):
    for e in graph["edges"]:
        for k, a in e["attrs"].items():
            assert a["src"] in {"osm", "derived", "default", "bdot10k", "authored_override"}, (e["id"], k)
            assert a["conf"] in {"high", "medium", "low"}
        assert e["low_confidence"] == sorted(k for k, a in e["attrs"].items() if a["conf"] == "low")


def test_buildings_intersect_tile(region, buildings_fc):
    tile = shapely.box(*region.bbox)
    for f in buildings_fc["features"]:
        g = shapely.geometry.shape(f["geometry"])
        assert g.intersects(tile), f["id"]
        assert f["properties"]["height_m"] > 0
        assert f["properties"]["height_source"]


def test_terrain_meta_matches_bbox(region):
    t = json.loads((REGION_DIR / "terrain.json").read_text(encoding="utf-8"))
    assert t["bbox"] == list(region.bbox)
    assert t["samples"] == [int(region.width) + 1, int(region.height) + 1]
    assert t["missing_samples"] == 0
