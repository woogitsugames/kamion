"""pytest: OSM turn_restrictions.json generator and truck-aware restriction mapping (ADR 0150)."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import build_route_graph as brg  # noqa: E402

PBF = os.path.join(brg.REPO, "Data", "raw", "osm", "podlaskie-261108.osm.pbf")


def _edge(eid, a, b, geom, way, **attrs):
    return {"id": eid, "from": a, "to": b, "geometry": geom, "osm_way": way,
            "attrs": {k: {"v": v, "src": "osm", "conf": "high"} for k, v in attrs.items()}}


def _sample_graph():
    nodes = [
        {"id": "n1", "x": 0.0, "y": 0.0, "osm_node": 1},
        {"id": "n2", "x": 100.0, "y": 0.0, "osm_node": 2},
        {"id": "n3", "x": 100.0, "y": 100.0, "osm_node": 3},
        {"id": "n4", "x": 200.0, "y": 0.0, "osm_node": 4},
    ]
    edges = [
        _edge("w10:1-2", "n1", "n2", [[0, 0], [100, 0]], 10, highway="secondary"),
        _edge("w11:2-3", "n2", "n3", [[100, 0], [100, 100]], 11, highway="residential"),
        _edge("w12:2-4", "n2", "n4", [[100, 0], [200, 0]], 12, highway="secondary"),
    ]
    return {"nodes": nodes, "edges": edges}


def test_parse_osm_restriction_standard_and_hgv():
    std = brg.parse_osm_restriction_relation(
        100, {"type": "restriction", "restriction": "no_left_turn"},
        [("w", 10, "from"), ("n", 2, "via"), ("w", 11, "to")],
    )
    assert std == {
        "id": 100, "restriction": "no_left_turn", "hgv_only": False,
        "from_way": 10, "to_way": 11, "via_node": 2, "via_is_way": False,
    }

    hgv_only = brg.parse_osm_restriction_relation(
        101, {"type": "restriction", "restriction:hgv": "no_left_turn"},
        [("w", 10, "from"), ("n", 2, "via"), ("w", 11, "to")],
    )
    assert hgv_only["restriction"] == "no_left_turn" and hgv_only["hgv_only"] is True

    hgv_override = brg.parse_osm_restriction_relation(
        102, {"type": "restriction", "restriction": "only_straight_on", "restriction:hgv": "no_left_turn"},
        [("w", 10, "from"), ("n", 2, "via"), ("w", 11, "to")],
    )
    assert hgv_override["restriction"] == "no_left_turn"
    assert hgv_override["restriction_general"] == "only_straight_on"
    assert hgv_override["hgv_only"] is False

    type_hgv = brg.parse_osm_restriction_relation(
        103, {"type": "restriction:hgv", "restriction": "no_u_turn"},
        [("w", 10, "from"), ("n", 2, "via"), ("w", 10, "to")],
    )
    assert type_hgv["restriction"] == "no_u_turn" and type_hgv["hgv_only"] is True

    exempt = brg.parse_osm_restriction_relation(
        104, {"type": "restriction", "restriction": "no_left_turn", "except": "motorcar; hgv"},
        [("w", 10, "from"), ("n", 2, "via"), ("w", 11, "to")],
    )
    assert exempt["restriction"] == "" and exempt["hgv_exempt"] is True
    assert exempt["restriction_general"] == "no_left_turn"

    delivery_exempt = brg.parse_osm_restriction_relation(
        105, {"type": "restriction", "restriction": "only_right_turn", "except": "delivery"},
        [("w", 10, "from"), ("n", 2, "via"), ("w", 12, "to")],
    )
    assert delivery_exempt["restriction"] == "only_right_turn" and "hgv_exempt" not in delivery_exempt

    cond = brg.parse_osm_restriction_relation(
        106, {"type": "restriction", "restriction:conditional": "no_left_turn @ (Mo-Sa 07:00-16:00)"},
        [("w", 10, "from"), ("n", 2, "via"), ("w", 11, "to")],
    )
    assert cond["restriction"] == ""
    assert cond["restriction_conditional"] == "no_left_turn @ (Mo-Sa 07:00-16:00)"

    via_way = brg.parse_osm_restriction_relation(
        107, {"type": "restriction", "restriction": "no_u_turn"},
        [("w", 10, "from"), ("w", 99, "via"), ("w", 12, "to")],
    )
    assert via_way["via_node"] is None and via_way["via_is_way"] is True and via_way["via_ways"] == [99]

    assert brg.parse_osm_restriction_relation(108, {"type": "multipolygon"}, []) is None


def test_build_respects_hgv_exempt_and_multi_ways():
    g = _sample_graph()
    rows = [
        {"id": 1, "restriction": "", "hgv_exempt": True, "from_way": 10, "to_way": 11, "via_node": 2},
        {"id": 2, "restriction": "no_left_turn", "from_way": 10, "to_way": 11, "to_ways": [11, 12], "via_node": 2},
        {"id": 3, "restriction": "", "restriction_conditional": "no_left_turn @ (07:00-16:00)",
         "from_way": 10, "to_way": 11, "via_node": 2},
    ]
    t = brg.build(g, (0.0, 0.0), rows)
    assert t["restrictions"] == [(0, 1, 1, 0), (0, 1, 2, 0)]
    assert t["unmapped_restrictions"] == [3]


def test_filter_and_write_turn_restrictions_roundtrip(tmp_path):
    g = _sample_graph()
    r_in = brg.parse_osm_restriction_relation(
        200, {"type": "restriction", "restriction:hgv": "no_left_turn"},
        [("w", 10, "from"), ("n", 2, "via"), ("w", 11, "to")],
    )
    r_out = brg.parse_osm_restriction_relation(
        199, {"type": "restriction", "restriction": "no_u_turn"},
        [("w", 999, "from"), ("n", 9, "via"), ("w", 998, "to")],
    )
    out_file = tmp_path / "r1" / "turn_restrictions.json"
    rows = brg.refresh_restrictions(
        str(tmp_path / "r1"), g, out_path=str(out_file),
        preloaded=("test.osm.pbf", "deadbeef", [r_in, r_out]),
    )
    assert [r["id"] for r in rows] == [200]
    doc = json.loads(out_file.read_text(encoding="utf-8"))
    assert doc["schema"] == "truck-sim-pl/turn-restrictions/1"
    assert doc["source"] == "test.osm.pbf" and doc["source_sha256"] == "deadbeef"
    assert doc["restrictions"][0]["id"] == 200 and doc["restrictions"][0]["hgv_only"] is True
    t = brg.build(g, (0.0, 0.0), doc["restrictions"])
    assert t["restrictions"] == [(0, 1, 1, 0)] and t["unmapped_restrictions"] == []


@pytest.mark.skipif(not os.path.exists(PBF), reason="raw OSM extract not present")
def test_pbf_hgv_relation_and_region_c_byte_identical(tmp_path):
    all_rels = brg.read_pbf_restrictions(PBF)
    hgv = [r for r in all_rels if r["id"] == 20262734]
    assert len(hgv) == 1
    assert hgv[0]["restriction"] == "no_left_turn" and hgv[0]["hgv_only"] is True

    rc = brg.main(["--region", "bialystok-industrial-c", "--restrictions-only", "--restrictions-out-dir", str(tmp_path)])
    assert rc == 0
    gen = (tmp_path / "bialystok-industrial-c" / "turn_restrictions.json").read_bytes()
    ref = open(os.path.join(brg.REPO, "Data", "Regions", "bialystok-industrial-c", "turn_restrictions.json"), "rb").read()
    assert gen == ref
