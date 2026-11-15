"""ADR 0206: region bialystok-kleeberga (second Białystok tile of the D64 route to Knyszyn, lattice -2,0)."""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
import regions  # noqa: E402

RID = "bialystok-kleeberga"
RDIR = REPO / "Data" / "Regions" / RID
PLAN = REPO / "docs" / "reports" / "map" / "dk65_route_plan.json"


def _graph(rid):
    return json.loads((REPO / "Data" / "Regions" / rid / "roads.graph.json").read_text(encoding="utf-8"))


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


def test_tile_is_the_west_lattice_neighbour_of_maczka_and_matches_the_plan():
    m, k = regions.get("bialystok-maczka"), regions.get(RID)
    assert k.bbox == (m.bbox[0] - regions.TILE_SIZE_M, m.bbox[1], m.bbox[0], m.bbox[3])
    assert k.origin == ((k.bbox[0] + k.bbox[2]) / 2, (k.bbox[1] + k.bbox[3]) / 2)
    assert k.teryt_powiat == "2061"
    tiles = json.loads(PLAN.read_text(encoding="utf-8"))["variants"]["A_old_road"]["tiles"]
    t = next(t for t in tiles if tuple(t["ij"]) == (-2, 0))
    assert tuple(t["bbox"]) == k.bbox


def test_seam_with_maczka_has_the_same_roads_on_both_sides():
    x = regions.get(RID).bbox[2]
    a, b = _boundary(RID, x), _boundary("bialystok-maczka", x)
    assert a == b and len(a) >= 4
    assert {r[1] for r in a if r[2] == "trunk"} == {249740774, 257355872}   # both carriageways of Gen. Maczka


def test_route_endpoints_sit_on_boundary_nodes_of_the_trunk():
    ep = json.loads((RDIR / "route_endpoints.json").read_text(encoding="utf-8"))
    g = _graph(RID)
    for key in ("start_epsg2180", "end_epsg2180"):
        x, y = ep[key]
        d = min(abs(n["x"] - x) + abs(n["y"] - y) for n in g["nodes"] if n.get("boundary"))
        assert d < 1.0, (key, d)


def test_overrides_are_explained_and_target_existing_ways():
    import yaml
    ov = yaml.safe_load((RDIR / "overrides.yaml").read_text(encoding="utf-8"))["overrides"] or []
    ways = {e["osm_way"] for e in _graph(RID)["edges"]}
    for o in ov:
        assert o["reason"].strip() and o["confidence"] and o["verify"]
        for w in o.get("target", {}).get("osm_way", []):
            assert w in ways, (o["id"], w)


def test_no_proposed_or_construction_way_is_drivable():
    hw = {e["attrs"]["highway"]["v"] for e in _graph(RID)["edges"]}
    assert not hw & {"proposed", "construction", "motorway", "motorway_link"}


def test_junction_checks_are_inside_the_tile():
    k = regions.get(RID)
    js = json.loads((RDIR / "junction_checks.authored.json").read_text(encoding="utf-8"))["junctions"]
    assert len(js) >= 8
    for j in js:
        x, y = j["center_2180"]
        assert k.bbox[0] <= x <= k.bbox[2] and k.bbox[1] <= y <= k.bbox[3]
