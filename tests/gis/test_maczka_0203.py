"""ADR 0203: region bialystok-maczka (first Białystok tile of the D64 route to Knyszyn) and the route plan."""
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
import regions  # noqa: E402

RID = "bialystok-maczka"
RDIR = REPO / "Data" / "Regions" / RID
PLAN = REPO / "docs" / "reports" / "map" / "dk65_route_plan.json"


def _graph(rid):
    return json.loads((REPO / "Data" / "Regions" / rid / "roads.graph.json").read_text(encoding="utf-8"))


def test_tile_is_the_west_lattice_neighbour_of_c():
    c, m = regions.get("bialystok-industrial-c"), regions.get(RID)
    assert m.bbox == (c.bbox[0] - regions.TILE_SIZE_M, c.bbox[1], c.bbox[0], c.bbox[3])
    assert m.origin == ((m.bbox[0] + m.bbox[2]) / 2, (m.bbox[1] + m.bbox[3]) / 2)
    assert m.teryt_powiat == "2061"


def _boundary(rid, x):
    g = _graph(rid)
    nodes = {n["id"]: n for n in g["nodes"]}
    out = set()
    for e in g["edges"]:
        for k in ("from", "to"):
            n = nodes[e[k]]
            if n.get("boundary") and abs(n["x"] - x) < 0.01:
                a = e["attrs"]
                out.add((round(n["y"], 2), e["osm_way"], a["highway"]["v"], a["lanes"]["v"], a["oneway"]["v"]))
    return out


def test_seam_with_c_has_the_same_roads_on_both_sides():
    x = regions.get(RID).bbox[2]
    a, b = _boundary(RID, x), _boundary("bialystok-industrial-c", x)
    assert a == b and len(a) >= 4
    assert {r[1] for r in a if r[2] == "trunk"} == {23982184, 257367422}   # both carriageways of Gen. Maczka


def test_route_endpoints_sit_on_boundary_nodes_of_the_trunk():
    ep = json.loads((RDIR / "route_endpoints.json").read_text(encoding="utf-8"))
    g = _graph(RID)
    for key in ("start_epsg2180", "end_epsg2180"):
        x, y = ep[key]
        d = min(abs(n["x"] - x) + abs(n["y"] - y) for n in g["nodes"] if n.get("boundary"))
        assert d < 1.0, (key, d)


def test_lane_overrides_target_existing_ways():
    import yaml
    ov = yaml.safe_load((RDIR / "overrides.yaml").read_text(encoding="utf-8"))["overrides"]
    ways = {e["osm_way"] for e in _graph(RID)["edges"]}
    assert len(ov) >= 3
    for o in ov:
        assert o["reason"].strip() and o["confidence"] and o["verify"]
        for w in o.get("target", {}).get("osm_way", []):
            assert w in ways, (o["id"], w)


def test_route_plan_variants_and_tiles():
    p = json.loads(PLAN.read_text(encoding="utf-8"))
    a, b = p["variants"]["A_old_road"], p["variants"]["B_signed_dk65_via_s19"]
    assert not any(w["highway"].startswith("motorway") for w in a["ways"])       # D64: no expressway
    assert any(w["highway"] == "motorway" for w in b["ways"])
    assert 28.0 < a["length_km"] < 29.0 and a["length_km"] < b["length_km"]
    tiles = [tuple(t["ij"]) for t in a["tiles"]]
    assert tiles[:4] == [(0, 0), (-1, 0), (-2, 0), (-3, 0)] and tiles[-1] == (-8, 8) and len(tiles) == 17
    m = regions.get(RID)
    assert tuple(a["tiles"][1]["bbox"]) == m.bbox
    assert sum(t["route_m"] for t in a["tiles"]) == pytest.approx(a["length_km"] * 1000, abs=40)


def test_junction_checks_are_inside_the_tile():
    m = regions.get(RID)
    js = json.loads((RDIR / "junction_checks.authored.json").read_text(encoding="utf-8"))["junctions"]
    assert len(js) >= 7
    for j in js:
        x, y = j["center_2180"]
        assert m.bbox[0] <= x <= m.bbox[2] and m.bbox[1] <= y <= m.bbox[3]
