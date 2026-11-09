"""The start route (Kwadrat Park gate -> DK8/DK19 at Al. Tysiąclecia) must be drivable in the tile graph."""

import json
import math

import networkx as nx

from conftest import REPO

# Endpoints recorded by the D4 analysis (docs/reports/map/candidates.json, candidate C).
CAND = json.loads((REPO / "docs" / "reports" / "map" / "candidates.json").read_text(encoding="utf-8"))
ROUTE = next(c for c in CAND["candidates"] if c["id"] == "C_andersa_putry")["route"]


def nearest(graph, xy):
    return min(graph["nodes"], key=lambda n: math.hypot(n["x"] - xy[0], n["y"] - xy[1]))


def test_route_endpoints_snap(graph):
    for xy in (ROUTE["start_epsg2180"], ROUTE["end_epsg2180"]):
        n = nearest(graph, xy)
        assert math.hypot(n["x"] - xy[0], n["y"] - xy[1]) < 1.0


def test_route_is_connected_respecting_oneway(graph):
    import roadgraph
    g = roadgraph.to_digraph(graph)
    s = nearest(graph, ROUTE["start_epsg2180"])["id"]
    t = nearest(graph, ROUTE["end_epsg2180"])["id"]
    assert nx.has_path(g, s, t)
    path = nx.shortest_path(g, s, t, weight="length")
    length = sum(g[a][b]["length"] for a, b in zip(path, path[1:]))
    # D4 analysis measured 2401 m on the unclipped OSM graph
    assert abs(length - ROUTE["length_m"]) < 25
    edges = {e["id"]: e for e in graph["edges"]}
    used = [edges[g[a][b]["id"]] for a, b in zip(path, path[1:])]
    assert used[0]["attrs"]["highway"]["v"] == "service"       # depot access road
    assert used[-1]["attrs"]["highway"]["v"] == "trunk"        # DK exit
    names = {e["attrs"].get("name", {}).get("v") for e in used}
    assert "Generała Władysława Andersa" in names
    assert "Aleja Tysiąclecia Państwa Polskiego" in names
    refs = {e["attrs"].get("ref", {}).get("v") for e in used} - {None}
    assert any("8" in r.split(";") or "19" in r.split(";") for r in refs)


def test_route_back_to_depot_exists(graph):
    """Truck must also be able to come back (no one-way trap)."""
    import roadgraph
    g = roadgraph.to_digraph(graph)
    s = nearest(graph, ROUTE["start_epsg2180"])["id"]
    t = nearest(graph, ROUTE["end_epsg2180"])["id"]
    assert nx.has_path(g, t, s)
