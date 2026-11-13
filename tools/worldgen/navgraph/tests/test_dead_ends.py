"""pytest: ADR 0169 - one-way parts of the routing graph with no way back into the main component ("traps" at the
region edge). Run: uv run --project tools/worldgen pytest tools/worldgen/navgraph/tests/test_dead_ends.py"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
import build_route_graph as brg  # noqa: E402
import dead_ends  # noqa: E402
from test_reachability import edge, scc_graph, REGION  # noqa: E402


def test_one_way_spur_is_a_trap_two_way_dead_end_is_not():
    g = scc_graph()   # square + one-way spur nB -> nE (5) + detached pair (6, 7)
    g["nodes"].append({"id": "nH", "x": 0.0, "y": 200.0})
    g["edges"].append(edge("w9", "nD", "nH", [[0, 100], [0, 200]], 9, highway="service", name="Dojazd"))   # two-way dead end
    t = brg.build(g, (0.0, 0.0), [])
    r = dead_ends.analyze(t)
    assert [t["edges"][i]["osm_way"] for i in r["trap_edge_index"]] == [5]
    assert r["trap_nodes"] == 1 and r["trap_edges_two_way"] == 0
    assert r["points_of_no_return"] == [{"street": "Slepa", "e": 100.0, "n": 0.0}]
    assert r["trap_edges_flagged_off_reach"] == 0   # reachable: M27 does not flag it, the pin may be set there


def test_region_traps_readonly():
    """The committed route file (read-only): the measured state of ADR 0169, 2026-11-13. A change here means the
    graph or the tile changed - re-run dead_ends.py and update the ADR numbers, do not just edit the test."""
    path = os.path.join(brg.REPO, "game", "Assets", "_Project", "UI", "Resources", "CabDisplay", "Nav", REGION + "_route.bytes")
    r = dead_ends.analyze(brg.parse(open(path, "rb").read()))
    assert r["off_reach_nodes"] == 113 and r["entry_only_nodes"] == 22
    assert r["trap_nodes"] == 26 and r["trap_edges"] == 30
    assert 2700.0 < r["trap_edges_length_m"] < 2760.0
    assert len(r["points_of_no_return"]) == 9
    for street in ("Generała Władysława Andersa", "Generała Stanisława Maczka", "Aleja Tysiąclecia Państwa Polskiego"):
        assert street in r["trap_by_street"]
