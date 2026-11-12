"""pytest: routing graph generator (ADR 0150). Run: uv run --project tools/worldgen pytest tools/worldgen/navgraph/tests"""
import json
import os
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import build_route_graph as brg  # noqa: E402

REGION = "bialystok-industrial-c"
RDIR = os.path.join(brg.REPO, "Data", "Regions", REGION)


def edge(eid, a, b, geom, way, **attrs):
    return {"id": eid, "from": a, "to": b, "geometry": geom, "osm_way": way,
            "attrs": {k: {"v": v, "src": "osm", "conf": "high"} for k, v in attrs.items()}}


def synthetic():
    nodes = [{"id": "nA", "x": 100.0, "y": 100.0, "osm_node": 1}, {"id": "nB", "x": 200.0, "y": 100.0, "osm_node": 2},
             {"id": "nC", "x": 200.0, "y": 200.0, "osm_node": 3}, {"id": "nD", "x": 300.0, "y": 100.0, "boundary": True}]
    edges = [
        edge("w10:1-2", "nA", "nB", [[100, 100], [200, 100]], 10, highway="residential", name="Ulica A", oneway="no"),
        edge("w11:2-3", "nB", "nC", [[200, 100], [200, 200]], 11, highway="secondary", oneway="-1", maxspeed=40),
        edge("w12:2-D", "nB", "nD", [[200, 100], [300, 100]], 12, highway="service", access="private"),
        edge("w13:3-1", "nC", "nA", [[200, 200], [100, 100]], 13, highway="tertiary", junction="roundabout"),
        edge("w14:x", "nA", "nC", [[100, 100], [100, 200], [200, 200]], 14, highway="residential", hgv="no"),
    ]
    return {"nodes": nodes, "edges": edges}


def test_oneway_reverse_flags_and_names():
    t = brg.build(synthetic(), (100.0, 100.0), [])
    names = t["names"]
    e = {names[x["name"]] if x["name"] else f"e{i}": x for i, x in enumerate(t["edges"])}
    assert names[0] == "" and "Ulica A" in names
    rev = t["edges"][1]                          # w11 sorted second
    assert rev["flags"] & brg.F_ONEWAY
    assert rev["pts"][0] == (100.0, 100.0) and rev["pts"][-1] == (100.0, 0.0), "oneway=-1 geometry reversed (C -> B)"
    assert t["nodes"][rev["from"]][:2] == (100.0, 100.0)
    assert rev["maxspeed"] == 40 and rev["maxspeed_src"] == 1
    assert t["edges"][2]["flags"] & brg.F_RESTRICTED
    assert t["edges"][3]["flags"] & brg.F_ROUNDABOUT and t["edges"][3]["flags"] & brg.F_ONEWAY
    assert t["edges"][4]["flags"] & brg.F_NO_TRUCK
    assert abs(t["edges"][4]["length"] - 200.0) < 1e-6
    assert e["Ulica A"]["flags"] & brg.F_ONEWAY == 0
    assert t["nodes"][3][2] == 1 and t["nodes"][0][2] == 0   # boundary flag kept (nodes sorted by id: nA nB nC nD)


def test_restrictions_mapped_to_split_edges():
    rows = [{"id": 1, "restriction": "no_left_turn", "from_way": 10, "via_node": 2, "to_way": 11},
            {"id": 2, "restriction": "only_straight_on", "from_way": 10, "via_node": 99, "to_way": 12}]
    t = brg.build(synthetic(), (0.0, 0.0), rows)
    assert t["restrictions"] == [(0, 1, 1, 0)]
    assert t["unmapped_restrictions"] == [2]


def test_roundtrip_and_determinism():
    t = brg.build(synthetic(), (0.0, 0.0), [])
    a = brg.serialize(t)
    assert a == brg.serialize(brg.build(synthetic(), (0.0, 0.0), []))
    p = brg.parse(a)
    assert p["names"] == t["names"]
    assert len(p["edges"]) == 5 and p["edges"][1]["flags"] == t["edges"][1]["flags"]
    assert abs(p["edges"][4]["length"] - 200.0) < 1e-3


def _region():
    graph = json.load(open(os.path.join(RDIR, "roads.graph.json"), encoding="utf-8"))
    rows = json.load(open(os.path.join(RDIR, "turn_restrictions.json"), encoding="utf-8"))["restrictions"]
    return graph, brg.build(graph, brg.read_origin(RDIR), rows)


def test_region_file_is_reproducible():
    """The committed game file equals a fresh build (no hand edits), at its own format version (v1 until the
    leader regenerates the .bytes with the v2 generator)."""
    _, t = _region()
    committed = open(os.path.join(brg.OUT_DIR, REGION + "_route.bytes"), "rb").read()
    (ver,) = struct.unpack_from("<H", committed, 4)
    assert ver in brg.SUPPORTED_VERSIONS
    assert brg.serialize(t, version=ver) == committed


# ------------------------------------------------------------------ lanes (OSM Key:turn:lanes)

def test_parse_turn_lanes_values():
    L, SL, T, SR, R = 1, 2, 4, 8, 16
    ML, MR, REV = 32, 64, 128
    assert brg.parse_turn_lanes(None) is None
    assert brg.parse_turn_lanes("left|through|right") == [L, T, R]
    assert brg.parse_turn_lanes("left;through|through|right") == [L | T, T, R]
    assert brg.parse_turn_lanes("slight_left|slight_right") == [SL, SR]
    assert brg.parse_turn_lanes("merge_to_left|merge_to_right") == [ML, MR]
    assert brg.parse_turn_lanes("reverse") == [REV]
    assert brg.parse_turn_lanes("none") == [0]
    assert brg.parse_turn_lanes("") == [0]
    assert brg.parse_turn_lanes("left||right") == [L, 0, R]          # empty slot = no data
    assert brg.parse_turn_lanes("left;none|through") == [L, T]
    assert brg.parse_turn_lanes("left;bogus_token|right") == [L, R]  # unknown tokens ignored
    assert brg.parse_turn_lanes("left; through |right") == [L | T, R]  # whitespace tolerated


def lanes_graph():
    nodes = [{"id": "nA", "x": 0.0, "y": 0.0, "osm_node": 1}, {"id": "nB", "x": 100.0, "y": 0.0, "osm_node": 2}]
    edges = [
        edge("w1", "nA", "nB", [[0, 0], [100, 0]], 1, highway="secondary", oneway="no",
             **{"turn:lanes": "left|through|right"}),
        edge("w2", "nA", "nB", [[0, 0], [100, 0]], 2, highway="secondary", oneway="-1",
             **{"turn:lanes:forward": "through|right", "turn:lanes:backward": "left;through"}),
        edge("w3", "nA", "nB", [[0, 0], [100, 0]], 3, highway="secondary", oneway="yes",
             **{"turn:lanes": "through"}),
        edge("w4", "nA", "nB", [[0, 0], [100, 0]], 4, highway="secondary", oneway="no", lanes="3"),
    ]
    return {"nodes": nodes, "edges": edges}


def test_lanes_directions_and_oneway_reverse():
    t = brg.build(lanes_graph(), (0.0, 0.0), [])
    by_way = {e["osm_way"]: e["lanes"] for e in t["edges"]}
    # Two-way: turn:lanes applies to both stored directions.
    assert by_way[1] == ([1, 4, 16], [1, 4, 16])
    # oneway=-1 reverses the geometry: way-forward lanes land in the stored backward slot and vice versa;
    # the backward direction is never driven on a one-way edge.
    assert by_way[2] == ([1 | 4], [])
    assert by_way[2][0] == [brg.LANE_BITS["left"] | brg.LANE_BITS["through"]]
    # oneway=yes: forward only.
    assert by_way[3] == ([4], [])
    # lanes count only: masks 0 (direction unknown), both directions on a two-way edge.
    assert by_way[4] == ([0, 0, 0], [0, 0, 0])


def test_lanes_forward_backward_without_reverse():
    nodes = [{"id": "nA", "x": 0.0, "y": 0.0, "osm_node": 1}, {"id": "nB", "x": 100.0, "y": 0.0, "osm_node": 2}]
    edges = [edge("w9", "nA", "nB", [[0, 0], [100, 0]], 9, highway="secondary", oneway="no",
                  **{"turn:lanes:forward": "through", "turn:lanes:backward": "left|right",
                     "lanes:forward": "1", "lanes:backward": "2"})]
    t = brg.build({"nodes": nodes, "edges": edges}, (0.0, 0.0), [])
    assert t["edges"][0]["lanes"] == ([4], [1, 16])


def test_serialize_v2_lanes_roundtrip_and_v1_compat():
    t = brg.build(lanes_graph(), (0.0, 0.0), [])
    v2 = brg.serialize(t)                      # default = VERSION 2
    assert struct.unpack_from("<H", v2, 4)[0] == 2
    p = brg.parse(v2)
    assert p["version"] == 2 and len(p["lanes"]) == 4
    assert p["lanes"][0] == ([1, 4, 16], [1, 4, 16])
    assert p["lanes"][1] == ([1 | 4], [])
    assert brg.serialize(brg.parse(v2)) == v2  # deterministic
    v1 = brg.serialize(t, version=1)
    assert struct.unpack_from("<H", v1, 4)[0] == 1
    p1 = brg.parse(v1)
    assert p1["version"] == 1 and p1["lanes"] == {}
    try:
        bad = bytearray(v2)
        struct.pack_into("<H", bad, 4, 3)
        brg.parse(bytes(bad))
        assert False, "version 3 must be rejected"
    except ValueError:
        pass


def test_region_lanes():
    graph, t = _region()
    blocks = {i for i, e in enumerate(t["edges"]) if e["lanes"][0] or e["lanes"][1]}
    with_dir = {i for i, e in enumerate(t["edges"]) if any(e["lanes"][0]) or any(e["lanes"][1])}
    # 174 edges of the region carry the turn:lanes key (ADR 0150), 78 of them with actual direction values
    # (77 turn:lanes + 1 turn:lanes:forward); all 646 carry a lane count.
    assert len(with_dir) == 78
    assert len(blocks) == 646
    # A known value survives into the v2 build: al. Tysiaclecia way 236107504 has left|through|right.
    i = next(i for i, e in enumerate(t["edges"]) if e["osm_way"] == 236107504)
    assert t["edges"][i]["lanes"][0] == [1, 4, 16]


def test_region_graph_sane():
    graph, t = _region()
    assert len(t["edges"]) == len(graph["edges"])
    assert all(e["length"] > 0 for e in t["edges"])
    oneway = [e for e in t["edges"] if e["flags"] & brg.F_ONEWAY]
    assert len(oneway) >= 277
    # Every OSM restriction relation in the file maps onto the split edges.
    assert not t["unmapped_restrictions"]
    assert len(t["restrictions"]) >= 7
    # Geometry endpoints sit on their nodes (after the oneway=-1 reversal).
    for e in t["edges"]:
        a, b = t["nodes"][e["from"]], t["nodes"][e["to"]]
        assert abs(e["pts"][0][0] - a[0]) < 0.01 and abs(e["pts"][0][1] - a[1]) < 0.01
        assert abs(e["pts"][-1][0] - b[0]) < 0.01 and abs(e["pts"][-1][1] - b[1]) < 0.01
    # Known streets of the region are named in the routing graph.
    for street in ("Generała Władysława Andersa", "Aleja Tysiąclecia Państwa Polskiego", "Sokólska"):
        assert street in t["names"]
