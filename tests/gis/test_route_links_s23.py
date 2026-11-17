"""stream-gaps-s23: the streamed corridor Bialystok -> Knyszyn -> Tykocin is one chain of edge-adjacent tiles joined by
routes and route links (Data/Streaming/route_links.yaml -> Resources/WorldStreaming/route_links.json), every join is
closed to <= PORTAL_TOL_M, every corridor tile is in the d67-full build set (a tile missing from the build = closed seam),
and the built carriageway matches across the seams the links cross (chunk GLBs; skipped without Data/raw/derived)."""
import json
import sys
from collections import deque
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "worldgen" / "streaming"))
import route_links as RL  # noqa: E402
import tile_graph as TG  # noqa: E402

CORRIDOR = "bialystok-tykocin"
MUST = ["bialystok-industrial-c", "bialystok-knyszynska", "dk65-01", "dk65-11", "knyszyn-s", "knyszyn", "knyszyn-w",
        "dw671-tykocin-01"]


def _links():
    return json.loads(RL.OUT.read_text(encoding="utf-8"))


def _graph():
    return json.loads(TG.OUT.read_text(encoding="utf-8"))


def test_links_json_fresh():
    assert RL.OUT.read_text(encoding="utf-8") == RL.dumps(RL.build()), "run tools/worldgen/streaming/route_links.py"


def test_corridor_reaches_tykocin_tile_by_tile():
    c = next(c for c in _links()["corridors"] if c["id"] == CORRIDOR)
    tiles = c["tiles"]
    pos = [tiles.index(t) for t in MUST]
    assert pos == sorted(pos) and pos[0] == 0, tiles
    assert tiles[tiles.index("knyszyn") + 1:tiles.index("knyszyn") + 3] == ["knyszyn-w", "dw671-tykocin-01"]
    # tiles not yet in Data/Regions are listed, never skipped in the middle
    assert all(m not in {t["id"] for t in _graph()["tiles"]} for m in c["missing"])
    assert len(c["joins"]) == len(tiles) - 1


def test_every_join_is_an_edge_seam_and_closed():
    g = _graph()
    by = {t["id"]: t for t in g["tiles"]}
    c = next(c for c in _links()["corridors"] if c["id"] == CORRIDOR)
    for j in c["joins"]:
        assert len(j["side"]) == 1, j                       # N/E/S/W: the streamer opens edge seams only
        assert any(n["id"] == j["to"] and n["side"] == j["side"] for n in by[j["from"]]["neighbors"]), j
        assert j["gapM"] <= TG.PORTAL_TOL_M, j               # route exit / link end == next route entry / link start
        assert j["gapM"] <= RL.JOIN_TOL_M
        assert TG.on_seam([j["x"], j["y"]], by[j["from"]], j["side"]), j


def test_corridor_connected_in_tile_graph_bfs():
    g = _graph()
    adj = {t["id"]: [n["id"] for n in t["neighbors"] if len(n["side"]) == 1] for t in g["tiles"]}
    seen, q = {"bialystok-industrial-c"}, deque(["bialystok-industrial-c"])
    while q:
        for n in adj[q.popleft()]:
            if n not in seen:
                seen.add(n)
                q.append(n)
    assert "dw671-tykocin-01" in seen and "knyszyn-w" in seen
    # D81 / ADR 0278 tiles 5-7 (wygoda, bojary, mickiewicza) close the former gap: C -> wygoda (E) -> bojary (S) ->
    # mickiewicza (S) -> Dojlidy (S) are edge neighbours
    assert {"bialystok-wygoda", "bialystok-bojary", "bialystok-mickiewicza", "bialystok-dojlidy"} <= seen


def test_dojlidy_corridor_joins_closed_up_to_the_missing_tile():
    """D81: C -> wygoda -> bojary -> mickiewicza joined by routes / links; Ciolkowskiego continues through the 129 m
    stub of Dojlidy into bialystok-krywlany (ADR 0278 tile 4, not defined) - listed as missing, never skipped."""
    g = {t["id"]: t for t in _graph()["tiles"]}
    c = next(c for c in _links()["corridors"] if c["id"] == "bialystok-dojlidy-dk19")
    assert c["tiles"][:4] == ["bialystok-industrial-c", "bialystok-wygoda", "bialystok-bojary", "bialystok-mickiewicza"]
    assert c["missing"][:1] == ["bialystok-krywlany"]
    for j in c["joins"]:
        assert len(j["side"]) == 1 and j["gapM"] <= TG.PORTAL_TOL_M, j
        assert TG.on_seam([j["x"], j["y"]], g[j["from"]], j["side"]), j


def test_corridor_tiles_are_in_the_d67_full_build_set():
    cat = json.loads((ROOT / "game/Assets/_Project/Gameplay/Resources/Regions/region_catalog.json").read_text(encoding="utf-8"))
    full = next(s for s in cat["sets"] if s["name"] == "d67-full")["regions"]
    c = next(c for c in _links()["corridors"] if c["id"] == CORRIDOR)
    assert [t for t in c["tiles"] if t not in full] == []


def test_links_stay_in_their_tile_and_replace_only_knyszyn():
    g = {t["id"]: t for t in _graph()["tiles"]}
    for L in _links()["links"]:
        t = g[L["tile"]]
        for e, n in zip(L["e"], L["n"]):
            x, y = e + t["anchorX"], n + t["anchorY"]
            assert t["xmin"] - 3 <= x <= t["xmax"] + 3 and t["ymin"] - 3 <= y <= t["ymax"] + 3, (L["id"], x, y)
        assert len(L["e"]) == len(L["n"]) == len(L["maxspeedKmh"]) >= 2
        # knyszyn (Rynek dead end); C for the D81 trip to Dojlidy (C route runs west to Maczka)
        assert L["replacesRoute"] in ("", "knyszyn", "bialystok-industrial-c"), L["id"]
        steps = [((L["e"][i + 1] - L["e"][i]) ** 2 + (L["n"][i + 1] - L["n"][i]) ** 2) ** 0.5 for i in range(len(L["e"]) - 1)]
        assert max(steps) < 2.6, L["id"]                   # no jump (blend never breaks the 2 m sampling)


def test_knyszyn_links_pass_the_roundabout_not_rynek():
    """The knyszyn control route ends at Rynek (a U-turn for the articulated vehicle); the corridor links leave DK65 at
    the roundabout DK65/DW671 (ADR 0204: entry node of the seam knyszyn-s | knyszyn)."""
    rs = json.loads((ROOT / "Data/Regions/knyszyn/route_start.json").read_text(encoding="utf-8"))
    for L in _links()["links"]:
        if L["tile"] != "knyszyn":
            continue
        assert L["graphNodes"][0] == rs["graph_nodes"][0]
        assert rs["graph_nodes"][-1] not in L["graphNodes"], L["id"]     # never to Rynek
        g = json.loads((ROOT / "Data/Regions/knyszyn/roads.graph.json").read_text(encoding="utf-8"))
        ring = {e["from"] for e in g["edges"] if (e["attrs"].get("junction") or {}).get("v") == "roundabout"}
        assert any(n.rstrip("s") in ring or n in ring for n in L["graphNodes"]), L["id"]


# ---------------------------------------------------------------- built geometry across the link seams
@pytest.fixture(scope="module")
def seams():
    import link_seams
    res = link_seams.measure()
    if not all(r["built"] for r in res["seams"]):
        pytest.skip("chunk GLBs not on this machine (build_world not run)")
    return res["seams"]


def test_link_seams_route_and_height_continuous(seams):
    assert {(r["a"], r["b"]) for r in seams} >= {("knyszyn", "knyszyn-w"), ("knyszyn-w", "dw671-tykocin-01")}
    for r in seams:
        assert abs(r["delta_route_lat"]) <= 0.1, r          # autopilot polyline does not step sideways
        assert abs(r["delta"]["z_seam"]) <= 0.1, r          # asphalt axis height across the seam
        assert r["axis_kink_deg"] < 1.0, r
