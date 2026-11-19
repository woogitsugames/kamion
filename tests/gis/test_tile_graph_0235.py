"""ADR 0235: tile adjacency graph for additive streaming (tools/worldgen/streaming/tile_graph.py).

Runs on the region data in git only (region.yaml, route_endpoints.json), no Data/raw."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.worldgen.streaming import tile_graph as TG  # noqa: E402

D67 = ["bialystok-industrial-c", "bialystok-maczka", "bialystok-kleeberga", "bialystok-knyszynska"] + \
      [f"dk65-{i:02d}" for i in range(1, 12)] + ["knyszyn-s", "knyszyn"]
OPP = {"N": "S", "S": "N", "E": "W", "W": "E", "NE": "SW", "SW": "NE", "NW": "SE", "SE": "NW"}


def _graph():
    return TG.build()


def test_committed_graph_is_fresh():
    assert TG.OUT.exists(), "run tools/worldgen/streaming/tile_graph.py"
    assert TG.OUT.read_text(encoding="utf-8") == TG.dumps(_graph()), "tile_graph.json is stale: rerun the generator"


def test_every_region_is_a_2048_m_tile_with_a_centred_anchor():
    for t in _graph()["tiles"]:
        assert abs(t["xmax"] - t["xmin"] - 2048.0) < 0.01, t["id"]
        assert abs(t["ymax"] - t["ymin"] - 2048.0) < 0.01, t["id"]
        assert abs(t["anchorX"] - (t["xmin"] + t["xmax"]) / 2) < 0.01, t["id"]
        assert abs(t["anchorY"] - (t["ymin"] + t["ymax"]) / 2) < 0.01, t["id"]
        assert t["worldMemoryMB"] > 0
        assert t["worldMemoryHighMB"] > t["worldMemoryMB"], t["id"]   # ADR 0273: High content is heavier


def test_adjacency_is_symmetric_with_opposite_sides():
    g = _graph()
    by = {t["id"]: t for t in g["tiles"]}
    for t in g["tiles"]:
        for n in t["neighbors"]:
            back = [m for m in by[n["id"]]["neighbors"] if m["id"] == t["id"]]
            assert len(back) == 1, (t["id"], n["id"])
            assert back[0]["side"] == OPP[n["side"]]
            assert (len(n["side"]) == 1) == (n["seamM"] > 1.0)


def test_d67_corridor_is_one_chain_of_portals_on_shared_edges():
    g = _graph()
    chains = [c["tiles"] for c in g["corridors"]]
    assert D67 in chains, chains
    by = {t["id"]: t for t in g["tiles"]}
    for a, b in zip(D67, D67[1:]):
        p = [p for p in g["portals"] if p["from"] == a and p["to"] == b]
        assert len(p) == 1, (a, b)
        p = p[0]
        assert p["gapM"] <= TG.PORTAL_TOL_M
        assert TG.on_seam([p["x"], p["y"]], by[a], p["side"])
        assert any(n["id"] == b and n["side"] == p["side"] for n in by[a]["neighbors"])


def test_non_adjacent_regions_have_no_link():
    g = _graph()
    by = {t["id"]: t for t in g["tiles"]}
    # Dojlidy is 4 km south-east of C (ADR 0224 not_adjacent): never a neighbour of C. Since D81 (ADR 0278 tiles 5-7)
    # C touches Maczka (W) and wygoda (E); Dojlidy touches only mickiewicza (N), the ring tiles stay apart.
    assert [n["id"] for n in by["bialystok-dojlidy"]["neighbors"]] == ["bialystok-mickiewicza"]
    assert sorted(n["id"] for n in by["bialystok-industrial-c"]["neighbors"] if len(n["side"]) == 1) == \
        ["bialystok-maczka", "bialystok-wygoda"]
    assert "bialystok-dojlidy" not in {n["id"] for n in by["bialystok-industrial-c"]["neighbors"]}


def test_side_of_corner_and_overlap(tmp_path):
    a = {"id": "a", "xmin": 0.0, "ymin": 0.0, "xmax": 10.0, "ymax": 10.0}
    assert TG.side_of(a, {"id": "b", "xmin": 10.0, "ymin": 0.0, "xmax": 20.0, "ymax": 10.0}) == ("E", 10.0)
    assert TG.side_of(a, {"id": "c", "xmin": 10.0, "ymin": 10.0, "xmax": 20.0, "ymax": 20.0}) == ("NE", 0.0)
    assert TG.side_of(a, {"id": "d", "xmin": 30.0, "ymin": 0.0, "xmax": 40.0, "ymax": 10.0}) == (None, 0.0)
    try:
        TG.side_of(a, {"id": "e", "xmin": 5.0, "ymin": 5.0, "xmax": 15.0, "ymax": 15.0})
        raise AssertionError("overlap must raise")
    except ValueError:
        pass


def test_json_is_jsonutility_friendly():
    """JsonUtility reads arrays of objects and plain fields only: no dictionaries keyed by id, no nulls in tiles."""
    g = json.loads(TG.OUT.read_text(encoding="utf-8"))
    for t in g["tiles"]:
        for v in t.values():
            assert v is not None
            assert not isinstance(v, dict)
