"""ADR 0303: authored OSM tag fixes for the routing graph (Data/Overrides/osm_tag_fixes.yaml) - maxaxleload=10 from the
repealed Dz.U. 2017 poz. 878 is not a limit (art. 41 ust. 1 ustawy o drogach publicznych since 2021-03-13: 11.5 t)."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
import build_route_graph as brg  # noqa: E402

REPO = brg.REPO


def test_fix_file_lists_the_dk65_ways():
    fx = brg.load_tag_fixes()
    assert (27718745, "maxaxleload") in fx            # DK65 Knyszyn - Bialystok (dk65-07..11, knyszyn-s)
    assert (286989049, "maxaxleload") in fx           # DK65 Knyszyn - Monki
    assert fx[(27718745, "maxaxleload")] == ("10", None)


def test_fixed_attr_only_replaces_the_listed_value():
    fx = {(1, "maxaxleload"): ("10", None)}
    assert brg.fixed_attr(fx, {"osm_way": 1}, "maxaxleload", "10") is None
    assert brg.fixed_attr(fx, {"osm_way": 1}, "maxaxleload", "8") == "8"      # a newer, different value is kept
    assert brg.fixed_attr(fx, {"osm_way": 2}, "maxaxleload", "10") == "10"    # unlisted way
    assert brg.fixed_attr({}, {"osm_way": 1}, "maxaxleload", "10") == "10"


def test_corridor_route_graphs_have_no_10t_axle_limit():
    """The DK65 tiles of the Tykocin / Monki trips: no routing edge below the truck's 11.5 t axle load any more."""
    tiles = ["bialystok-knyszynska", "knyszyn-s", "knyszyn", "knyszyn-w"] + [f"dk65-{i:02d}" for i in range(1, 12)]
    for t in tiles:
        g = json.loads(open(os.path.join(REPO, "Data/Regions", t, "roads.graph.json"), encoding="utf-8").read())
        tab = brg.build(g, (0.0, 0.0), [])
        low = [e["id"] for e in tab["edges"] if 0 < e["maxaxleload_c"] < 1150]
        assert not low, (t, low[:5])
