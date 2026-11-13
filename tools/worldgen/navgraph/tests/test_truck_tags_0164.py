"""pytest: truck-limit tags from OSM to KRTG v2 (ADR 0164).

Run: uv run --project tools/worldgen pytest tools/worldgen/navgraph/tests/test_truck_tags_0164.py
"""
import os
import sys

import pytest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
import build_route_graph as brg  # noqa: E402
import roadgraph  # noqa: E402

REGION = "bialystok-industrial-c"
RDIR = os.path.join(brg.REPO, "Data", "Regions", REGION)
ALL_TAGS = ("maxaxleload", "maxlength", "maxweight:hgv", "hgv:conditional", "maxgvweightrating:hgv")


def _graph(tags: dict):
    """Two-edge graph whose first edge carries roadgraph.edge_attrs(tags) (the real pipeline step)."""
    nodes = [{"id": "nA", "x": 100.0, "y": 100.0, "osm_node": 1}, {"id": "nB", "x": 200.0, "y": 100.0, "osm_node": 2},
             {"id": "nC", "x": 300.0, "y": 100.0, "osm_node": 3}]
    e0 = {"id": "w1:1-2", "from": "nA", "to": "nB", "geometry": [[100, 100], [200, 100]], "osm_way": 1,
          "attrs": roadgraph.edge_attrs({"highway": "secondary", **tags}, 100.0)}
    e1 = {"id": "w2:2-3", "from": "nB", "to": "nC", "geometry": [[200, 100], [300, 100]], "osm_way": 2,
          "attrs": roadgraph.edge_attrs({"highway": "secondary"}, 100.0)}
    return {"nodes": nodes, "edges": [e0, e1]}


def _krtg(tags: dict):
    t = brg.build(_graph(tags), (0.0, 0.0), [])
    return t, brg.parse(brg.serialize(t))


# ------------------------------------------------------------------ roadgraph pass-through

def test_truck_tags_are_extracted_and_kept_in_sync():
    import osm_extract
    for k in ALL_TAGS:
        assert k in roadgraph.TRUCK_LIMIT_TAGS and k in roadgraph.RAW_TAGS
        assert k in osm_extract.ROAD_TAGS, f"{k} would never be read from the PBF"
    assert set(roadgraph.RAW_TAGS) <= set(osm_extract.ROAD_TAGS)


@pytest.mark.parametrize("key,val", [("maxaxleload", "10"), ("maxlength", "12"), ("maxweight:hgv", "7.5"),
                                    ("hgv:conditional", "no @ (22:00-06:00)"), ("maxgvweightrating:hgv", "8")])
def test_roadgraph_keeps_tag_with_provenance(key, val):
    a = roadgraph.edge_attrs({"highway": "primary", key: val}, 50.0)
    assert a[key] == {"v": val, "src": "osm", "conf": "high"}
    assert key not in roadgraph.edge_attrs({"highway": "primary"}, 50.0), "absent tag stays absent, not defaulted"


# ------------------------------------------------------------------ unit normalisation (as M21) through the whole chain

@pytest.mark.parametrize("tags,want", [
    ({"maxaxleload": "10"}, dict(maxaxleload_c=1000)),
    ({"maxaxleload": "11,5 t"}, dict(maxaxleload_c=1150)),
    ({"maxaxleload": "10000 kg"}, dict(maxaxleload_c=1000)),
    ({"maxaxleload": "none"}, dict(maxaxleload_c=0)),
    ({"maxlength": "12"}, dict(maxlength_cm=1200)),
    ({"maxlength": "16.5 m"}, dict(maxlength_cm=1650)),
    ({"maxweight": "12", "maxweight:hgv": "7.5"}, dict(maxweight_c=750)),     # hgv-specific tag wins
    ({"maxweight": "12"}, dict(maxweight_c=1200)),
    ({"maxweight:hgv": "3500 kg"}, dict(maxweight_c=350)),
])
def test_tag_to_krtg_fields(tags, want):
    t, p = _krtg(tags)
    for k, v in want.items():
        assert t["edges"][0][k] == v and p["edges"][0][k] == v, (tags, k)
    assert all(p["edges"][1][k] == 0 for k in ("maxweight_c", "maxaxleload_c", "maxheight_cm", "maxlength_cm"))


def test_maxgvweightrating_is_carried_but_not_a_weight_limit():
    """maxgvweightrating:hgv is a vehicle rating (with hgv=no + 'none @ delivery' in Bialystok), not a road weight limit:
    kept in the graph for QA, never turned into maxweight (ADR 0164)."""
    assert "maxgvweightrating:hgv" in _graph({"maxgvweightrating:hgv": "8"})["edges"][0]["attrs"]
    t, _ = _krtg({"maxgvweightrating:hgv": "8"})
    assert t["edges"][0]["maxweight_c"] == 0


def test_removing_the_tag_removes_the_limit(monkeypatch):
    """Mutation guard: without the pass-through (pre-0164 behaviour) the 10 t axle limit vanishes. The first assert
    fails in that code; the second shows the check is sensitive."""
    assert _krtg({"maxaxleload": "10"})[1]["edges"][0]["maxaxleload_c"] == 1000
    monkeypatch.setattr(roadgraph, "TRUCK_LIMIT_TAGS", tuple(k for k in ALL_TAGS if k != "maxaxleload"))
    assert _krtg({"maxaxleload": "10"})[1]["edges"][0]["maxaxleload_c"] == 0


# ------------------------------------------------------------------ hgv:conditional

@pytest.mark.parametrize("val,want", [
    ("no @ (22:00-06:00)", [("no", 1320, 360)]),
    ("No @ 22:00-06:00", [("no", 1320, 360)]),
    ("no @ (22:00-06:00); destination @ (06:00-08:00)", [("no", 1320, 360), ("destination", 360, 480)]),
    ("no @ (Mo-Fr 22:00-06:00)", None),          # days: not parsed
    ("no @ (Nov-Mar)", None),
    ("yes @ (06:00-08:00)", None),
    ("no @ (25:00-06:00)", None),
    ("no @ (22:00-06:00); no @ (weight>7.5)", None),   # one bad item spoils the lot
    ("", None), (None, None),
])
def test_parse_hgv_conditional(val, want):
    assert brg.parse_hgv_conditional(val) == want


def test_hgv_conditional_flag_and_report():
    t, p = _krtg({"hgv:conditional": "no @ (22:00-06:00)"})
    assert t["edges"][0]["flags"] & brg.F_HGV_TIMED and p["edges"][0]["flags"] & brg.F_HGV_TIMED
    assert not t["edges"][0]["flags"] & brg.F_NO_TRUCK, "timed ban is informational, not a hard block"
    assert t["hgv_conditional_unparsed"] == []
    t, p = _krtg({"hgv:conditional": "no @ (Mo-Fr 22:00-06:00)"})
    assert not t["edges"][0]["flags"] & brg.F_HGV_TIMED
    assert t["hgv_conditional_unparsed"] == [("w1:1-2", "no @ (Mo-Fr 22:00-06:00)")]
    # the new bit leaves the other bits alone
    t, _ = _krtg({"hgv:conditional": "no @ (22:00-06:00)", "oneway": "yes"})
    assert t["edges"][0]["flags"] & ~brg.F_OFF_REACH == brg.F_ONEWAY | brg.F_HGV_TIMED   # synthetic graph is off-reach


def test_v1_format_still_parses_with_new_fields():
    t = brg.build(_graph({"hgv:conditional": "no @ (22:00-06:00)", "maxaxleload": "10"}), (0.0, 0.0), [])
    p1 = brg.parse(brg.serialize(t, version=1))
    assert p1["version"] == 1 and p1["edges"][0]["maxaxleload_c"] == 0 and p1["edges"][0]["flags"] & brg.F_HGV_TIMED


# ------------------------------------------------------------------ real data (needs Data/raw, skipped otherwise)

def _pbf():
    from fetch_osm import REPO_ROOT
    return os.path.join(REPO_ROOT, "Data", "raw", "osm", "podlaskie-261108.osm.pbf")


@pytest.mark.skipif(not os.path.exists(_pbf()), reason="raw OSM extract not present")
def test_real_osm_andersa_axle_load_reaches_krtg():
    """way 249640399 (Andersa, maxaxleload=11.5, G10) through osm_extract -> roadgraph.build -> KRTG."""
    import osm_extract
    import regions
    region = regions.get(REGION)
    layers = osm_extract.load_layers()
    graph = roadgraph.build(layers["roads"], layers["points"], region.bbox)
    es = [e for e in graph["edges"] if e.get("osm_way") == 249640399]
    assert es, "way 249640399 is in the tile"
    assert all(e["attrs"]["maxaxleload"]["v"] == "11.5" for e in es)
    tagged = [e for e in graph["edges"] if "maxaxleload" in e["attrs"]]
    assert len(tagged) >= 80, len(tagged)    # measured 89 on 2026-11-13 (ADR 0164)
    t = brg.build(graph, brg.read_origin(RDIR), [])
    by_id = {e["id"]: e for e in t["edges"]}
    assert all(by_id[e["id"]]["maxaxleload_c"] == 1150 for e in tagged if e["id"] in by_id)
