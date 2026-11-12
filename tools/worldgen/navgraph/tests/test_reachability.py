"""pytest: reachability (M27, ADR 0150) - strongly connected components of the directed routing graph and the
off-reach flags written into the KRTG file. Run: uv run --project tools/worldgen pytest tools/worldgen/navgraph/tests"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import build_route_graph as brg  # noqa: E402

REGION = "bialystok-industrial-c"
RDIR = os.path.join(brg.REPO, "Data", "Regions", REGION)


def edge(eid, a, b, geom, way, **attrs):
    return {"id": eid, "from": a, "to": b, "geometry": geom, "osm_way": way,
            "attrs": {k: {"v": v, "src": "osm", "conf": "high"} for k, v in attrs.items()}}


def scc_graph():
    """Main two-way square nA-nB-nC-nD-nA; one-way spur nB -> nE (own SCC); off-reach pair nF <-> nG (own SCC,
    connected to the square only 'outside the tile')."""
    nodes = [{"id": "nA", "x": 0.0, "y": 0.0}, {"id": "nB", "x": 100.0, "y": 0.0}, {"id": "nC", "x": 100.0, "y": 100.0},
             {"id": "nD", "x": 0.0, "y": 100.0}, {"id": "nE", "x": 200.0, "y": 0.0},
             {"id": "nF", "x": 500.0, "y": 0.0}, {"id": "nG", "x": 600.0, "y": 0.0}]
    edges = [
        edge("w1", "nA", "nB", [[0, 0], [100, 0]], 1, highway="residential", name="Dolna"),
        edge("w2", "nB", "nC", [[100, 0], [100, 100]], 2, highway="residential", name="Prawa"),
        edge("w3", "nC", "nD", [[100, 100], [0, 100]], 3, highway="residential", name="Gorna"),
        edge("w4", "nD", "nA", [[0, 100], [0, 0]], 4, highway="residential", name="Lewa"),
        edge("w5", "nB", "nE", [[100, 0], [200, 0]], 5, highway="service", name="Slepa", oneway="yes"),
        edge("w6", "nF", "nG", [[500, 0], [600, 0]], 6, highway="residential", name="Buska"),
        edge("w7", "nG", "nF", [[600, 0], [500, 0]], 7, highway="residential", name="Buska"),
    ]
    return {"nodes": nodes, "edges": edges}


def test_scc_directed_oneway_respected():
    t = brg.build(scc_graph(), (0.0, 0.0), [])
    comps, comp = brg.strongly_connected_components(len(t["nodes"]), t["edges"])
    sizes = [len(c) for c in comps]
    assert sizes[0] == 4                      # the two-way square is the main SCC
    assert sorted(sizes[1:]) == [1, 2]         # one-way spur nE alone; nF<->nG together
    # nB -> nE is one-way: nE cannot get back, so it is NOT in the main SCC despite the physical connection.
    assert comp[t["nodes"].index(next(n for n in t["nodes"] if n[:2] == (100.0, 0.0)))] == 0
    assert comp[4] == 2 and comp[5] == 1 and comp[6] == 1   # sizes [4, 2, 1]: square, nF<->nG, nE


def test_off_reach_flags_marked_and_roundtrip():
    t = brg.build(scc_graph(), (0.0, 0.0), [])
    r = t["reachability"]
    assert r["components"] == 3 and r["main_nodes"] == 4 and r["scc_off_nodes"] == 3
    # Integration r5: off-reach = not drivable to from the main SCC. The one-way spur nB -> nE is its own SCC but
    # reachable (a valid destination); only the pair nF <-> nG is off-reach.
    off_nodes = [i for i, nd in enumerate(t["nodes"]) if nd[2] & brg.NF_OFF_REACH]
    assert off_nodes == [5, 6] and r["off_nodes"] == 2
    off_edges = [e["osm_way"] for e in t["edges"] if e["flags"] & brg.F_OFF_REACH]
    assert off_edges == [6, 7]
    assert all(not (e["flags"] & brg.F_OFF_REACH) for e in t["edges"] if e["osm_way"] in (1, 2, 3, 4, 5))
    assert r["off_streets"] == ["Buska"]
    # flags survive the serialize/parse round-trip in both format versions (plain flag bits, no version change)
    for ver in brg.SUPPORTED_VERSIONS:
        p = brg.parse(brg.serialize(t, version=ver))
        assert ver == p["version"]
        assert [i for i, nd in enumerate(p["nodes"]) if nd[2] & brg.NF_OFF_REACH] == [5, 6]
        assert [bool(e["flags"] & brg.F_OFF_REACH) for e in p["edges"]] == [bool(e["flags"] & brg.F_OFF_REACH) for e in t["edges"]]


def test_one_way_entry_from_outside_is_not_off_reach_target_but_start_ok():
    """One-way entry nX -> nA from outside the tile: nX is not drivable to (off-reach node), the entry edge cannot be
    entered from the main component (off-reach edge) - but a one-way exit nB -> nE stays a valid destination."""
    g = scc_graph()
    g["nodes"].append({"id": "nX", "x": -100.0, "y": 0.0})
    g["edges"].append(edge("w8", "nX", "nA", [[-100, 0], [0, 0]], 8, highway="residential", name="Wjazd", oneway="yes"))
    t = brg.build(g, (0.0, 0.0), [])
    by_way = {e["osm_way"]: e for e in t["edges"]}
    assert by_way[8]["flags"] & brg.F_OFF_REACH
    assert not by_way[5]["flags"] & brg.F_OFF_REACH


def test_region_reachability_readonly():
    """The region graph in the repo (read-only): SCC counts and the off-reach street list for the report."""
    graph = json.load(open(os.path.join(RDIR, "roads.graph.json"), encoding="utf-8"))
    rows = json.load(open(os.path.join(RDIR, "turn_restrictions.json"), encoding="utf-8"))["restrictions"]
    t = brg.build(graph, brg.read_origin(RDIR), rows)
    r = t["reachability"]
    assert r["components"] == 64
    assert r["main_nodes"] == 411 and r["main_edges"] == 502
    assert r["scc_off_nodes"] == 139                      # outside the main SCC (PR #29 flagged all of them)
    assert r["off_nodes"] == 113 and r["off_edges"] == 115   # not drivable to from the main SCC
    # ADR 0150: the part connected only outside the 2 km tile (Olsztyńska / Buska) is off-reach.
    for street in ("Olsztyńska", "Buska", "Brzeska", "Białostoczek", "Sitarska"):
        assert street in r["off_streets"]
    # every flagged node really has no directed path from the main SCC
    assert sum(1 for nd in t["nodes"] if nd[2] & brg.NF_OFF_REACH) == 113
