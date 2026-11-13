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
    """The committed game file equals a fresh build exactly as main() writes it (carriageway axes M28 + reachability
    flags M27, at the file's own format version) - no hand edits.

    Integration r5: until the leader regenerates the .bytes, the committed file predates M27/M28, so the legacy
    variant (raw OSM axes, M27 bits masked) is accepted too; after regeneration only the full variant matches
    (remove the legacy branch then)."""
    graph, t_osm = _region()
    committed = open(os.path.join(brg.OUT_DIR, REGION + "_route.bytes"), "rb").read()
    (ver,) = struct.unpack_from("<H", committed, 4)
    assert ver in brg.SUPPORTED_VERSIONS
    rows = json.load(open(os.path.join(RDIR, "turn_restrictions.json"), encoding="utf-8"))["restrictions"]
    full = brg.build(graph, brg.read_origin(RDIR), rows, brg.load_carriageway_axes(REGION, graph))
    import copy
    legacy = copy.deepcopy(t_osm)
    legacy["nodes"] = [(e, n, f & ~brg.NF_OFF_REACH) for e, n, f in legacy["nodes"]]
    for e in legacy["edges"]:
        e["flags"] &= ~brg.F_OFF_REACH
    assert committed in (brg.serialize(full, version=ver), brg.serialize(legacy, version=ver))
    # The fresh build does carry the reachability marks (they are plain flag bits, kept in v1 and v2 alike).
    assert any(e["flags"] & brg.F_OFF_REACH for e in full["edges"])
    assert any(nd[2] & brg.NF_OFF_REACH for nd in full["nodes"])


def test_parse_osm_limit_values():
    pwt, plm = brg.parse_weight_t, brg.parse_length_m
    assert pwt("3.5") == 3.5 and pwt("3.5 t") == 3.5 and pwt("3.5t") == 3.5 and pwt("3,5 t") == 3.5
    assert pwt("3500 kg") == 3.5 and pwt("40") == 40.0
    assert pwt("none") is None and pwt("default") is None and pwt("national") is None and pwt("") is None
    assert pwt("abc") is None and pwt(None) is None
    assert plm("4") == 4.0 and plm("4.0 m") == 4.0 and plm("3.5") == 3.5
    assert abs(plm("12'6\"") - (12 * 0.3048 + 6 * 0.0254)) < 1e-9
    assert abs(plm("14'2\"") - (14 * 0.3048 + 2 * 0.0254)) < 1e-9
    assert plm("none") is None and plm("default") is None and plm("abc") is None and plm(None) is None


def test_limits_and_hgv_destination_in_build_roundtrip():
    edges = [
        edge("w20:1-2", "nA", "nB", [[100, 100], [200, 100]], 20, highway="residential",
             maxweight="7.5 t", maxaxleload="10", maxheight="3.5", maxlength="12'6\""),
        edge("w21:2-3", "nB", "nC", [[200, 100], [200, 200]], 21, highway="service", hgv="destination",
             maxweight="3.5", maxheight="default"),
        edge("w22:3-1", "nC", "nA", [[200, 200], [100, 100]], 22, highway="tertiary", maxheight="none"),
    ]
    g = {"nodes": synthetic()["nodes"], "edges": edges}
    t = brg.build(g, (100.0, 100.0), [])
    e0, e1, e2 = t["edges"]   # sorted by id: w20, w21, w22
    assert (e0["maxweight_c"], e0["maxaxleload_c"], e0["maxheight_cm"], e0["maxlength_cm"]) == (750, 1000, 350, 381)
    assert e0["flags"] & brg.F_HGV_DESTINATION == 0
    assert e1["flags"] & brg.F_HGV_DESTINATION
    assert (e1["maxweight_c"], e1["maxheight_cm"]) == (350, 0), "default = no limit"
    assert e2["maxheight_cm"] == 0, "none = no limit"
    # v2 round-trip keeps the limits; a v1 serialization drops them and parses back as zeros.
    p2 = brg.parse(brg.serialize(t))
    assert p2["version"] == 2 and p2["edges"][0]["maxweight_c"] == 750 and p2["edges"][1]["flags"] & brg.F_HGV_DESTINATION
    p1 = brg.parse(brg.serialize(t, version=brg.VERSION_V1))
    assert p1["version"] == 1 and all(e["maxweight_c"] == 0 and e["maxheight_cm"] == 0 for e in p1["edges"])
    assert p1["edges"][1]["flags"] & brg.F_HGV_DESTINATION, "the flag is a plain edge flag, kept in v1 too"


def test_region_limit_tag_counts():
    """What truck-limit tags the region graph actually carries (read-only; report numbers for ADR 0150)."""
    graph, t = _region()
    want = ("maxweight", "maxweight:hgv", "maxaxleload", "maxheight", "maxlength", "hgv:conditional")
    counts = {k: 0 for k in want}
    hgv_vals, mh_vals = {}, {}
    for e in graph["edges"]:
        a = e.get("attrs", {})
        for k in want:
            if k in a:
                counts[k] += 1
        if "hgv" in a:
            hgv_vals[str(a["hgv"].get("v"))] = hgv_vals.get(str(a["hgv"].get("v")), 0) + 1
        if "maxheight" in a:
            mh_vals[str(a["maxheight"].get("v"))] = mh_vals.get(str(a["maxheight"].get("v")), 0) + 1
    assert len(graph["edges"]) == 646
    # ADR 0164: maxaxleload (11.5 t on 89 edges = the truck's own axle limit) appears once roads.graph.json is
    # regenerated with the pass-through; before that it is absent. Both states are valid, nothing else may differ.
    n_axle = counts.pop("maxaxleload")
    assert n_axle in (0, 89), n_axle
    assert counts == {"maxweight": 0, "maxweight:hgv": 0, "maxheight": 2, "maxlength": 0, "hgv:conditional": 0}
    assert hgv_vals == {"no": 6} and mh_vals == {"default": 2}
    # In the built graph: hgv=no (and access=no / emergency_access) -> F_NO_TRUCK, maxheight=default -> no limit
    # stored, no hgv=destination.
    def attrv(e, k):
        a = e.get("attrs", {}).get(k)
        return a.get("v") if isinstance(a, dict) else None
    expect_no_truck = sum(1 for e in graph["edges"]
                          if attrv(e, "access") == "no" or attrv(e, "hgv") == "no" or attrv(e, "service") == "emergency_access")
    assert sum(1 for e in t["edges"] if e["flags"] & brg.F_NO_TRUCK) == expect_no_truck
    assert sum(1 for e in t["edges"] if e["flags"] & brg.F_HGV_DESTINATION) == 0
    assert all(e["maxweight_c"] == 0 and e["maxheight_cm"] == 0 and e["maxlength_cm"] == 0 for e in t["edges"])
    axle = [e["maxaxleload_c"] for e in t["edges"] if e["maxaxleload_c"]]
    assert len(axle) == n_axle and set(axle) <= {1150}, "maxaxleload=11.5 == the truck's parameter: no route effect"


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
    # Two-way way with a plain turn:lanes: ambiguous (wiki Key:turn wants :forward / :backward there) - not split.
    assert by_way[1] == ([], [])
    # oneway=-1 reverses the geometry: the travel direction is the way's backward one (turn:lanes:backward);
    # the backward direction of a one-way edge is never driven.
    assert by_way[2] == ([1 | 4], [])
    assert by_way[2][0] == [brg.LANE_BITS["left"] | brg.LANE_BITS["through"]]
    # oneway=yes: forward only.
    assert by_way[3] == ([4], [])
    # Two-way plain lanes=3 is the TOTAL of both directions (wiki Key:lanes) - not split.
    assert by_way[4] == ([], [])


def test_lanes_only_from_osm_and_roundabout_one_way():
    nodes = [{"id": "nA", "x": 0.0, "y": 0.0, "osm_node": 1}, {"id": "nB", "x": 100.0, "y": 0.0, "osm_node": 2}]
    dflt = edge("w5", "nA", "nB", [[0, 0], [100, 0]], 5, highway="secondary", oneway="yes", lanes=2)
    dflt["attrs"]["lanes"]["src"] = "default"            # pipeline default, not OSM data
    edges = [
        dflt,
        edge("w6", "nA", "nB", [[0, 0], [100, 0]], 6, highway="secondary", junction="roundabout", lanes="2",
             **{"turn:lanes": "left;through|right"}),
        edge("w7", "nA", "nB", [[0, 0], [100, 0]], 7, highway="secondary", oneway="no",
             **{"lanes:forward": "2", "lanes:backward": "1"}),
    ]
    t = brg.build({"nodes": nodes, "edges": edges}, (0.0, 0.0), [])
    by_way = {e["osm_way"]: e["lanes"] for e in t["edges"]}
    assert by_way[5] == ([], []), "src=default lane count is ignored"
    assert by_way[6] == ([1 | 4, 16], []), "roundabout = one-way: no backward lanes"
    assert by_way[7] == ([0, 0], [0]), "lanes:forward / :backward give per-direction counts"


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
    assert p["version"] == 2 and len(p["lanes"]) == 2      # w2, w3 (w1 / w4 two-way plain tags: not split)
    assert p["lanes"][1] == ([1 | 4], [])
    assert p["lanes"][2] == ([4], [])
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
    # 174 edges carry the turn:lanes key (ADR 0150): 77 from OSM with values, 97 pipeline defaults (src=default,
    # value None); + 1 turn:lanes:forward -> 78 edges with directions. Lane counts only from OSM (192 lanes / 1
    # lanes:forward / 1 lanes:backward; 454 src=default ignored; plain lanes on two-way ways not split) -> 182 blocks.
    assert len(with_dir) == 78
    assert len(blocks) == 182
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
