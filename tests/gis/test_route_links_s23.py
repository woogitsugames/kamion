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
    # known gap (report, plan in docs): Dojlidy has no edge neighbour - 1 column east, 2 rows (4096 m) south of C
    assert "bialystok-dojlidy" not in seen


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
        # knyszyn: ADR 0285; s8-03: ADR 0288 (same path as the s8-03 route, lane shift onto the s8-04 route before the seam)
        assert L["replacesRoute"] in ("", "knyszyn", "s8-03"), L["id"]
        steps = [((L["e"][i + 1] - L["e"][i]) ** 2 + (L["n"][i + 1] - L["n"][i]) ** 2) ** 0.5 for i in range(len(L["e"]) - 1)]
        assert max(steps) < 2.6, L["id"]                   # no jump (blend never breaks the 2 m sampling)


def test_knyszyn_links_pass_the_roundabout_not_rynek():
    """The knyszyn control route ends at Rynek (a U-turn for the articulated vehicle); the corridor links leave DK65 at
    the roundabout DK65/DW671 (ADR 0204: entry node of the seam knyszyn-s | knyszyn)."""
    rs = json.loads((ROOT / "Data/Regions/knyszyn/route_start.json").read_text(encoding="utf-8"))
    for L in _links()["links"]:
        if L["tile"] != "knyszyn" or L["afterRoute"]:
            continue
        assert L["graphNodes"][0] == rs["graph_nodes"][0]
        assert rs["graph_nodes"][-1] not in L["graphNodes"], L["id"]     # never to Rynek
        g = json.loads((ROOT / "Data/Regions/knyszyn/roads.graph.json").read_text(encoding="utf-8"))
        ring = {e["from"] for e in g["edges"] if (e["attrs"].get("junction") or {}).get("v") == "roundabout"}
        assert any(n.rstrip("s") in ring or n in ring for n in L["graphNodes"]), L["id"]


def test_knyszyn_start_drives_on_from_rynek():
    """seams-fix-s23: a drive started in knyszyn (`-scene knyszyn`) has the control route to Rynek as its path; a link
    `after_route: knyszyn` per destination continues it from the route end WITHOUT turning round (the first edge is not
    the one the route came in on), through the roundabout, to the same seam point as the corridor link of that
    destination (so knyszyn-w-dw671 / the knyszyn-w route join it), with the head blended exactly onto the route end."""
    rs = json.loads((ROOT / "Data/Regions/knyszyn/route_start.json").read_text(encoding="utf-8"))
    reg = {t["id"]: t for t in _graph()["tiles"]}["knyszyn"]
    links = _links()["links"]
    after = {L["destination"]: L for L in links if L["afterRoute"] == "knyszyn"}
    assert set(after) == {"tykocin", "monki"}
    g = json.loads((ROOT / "Data/Regions/knyszyn/roads.graph.json").read_text(encoding="utf-8"))
    ring = {e["from"] for e in g["edges"] if (e["attrs"].get("junction") or {}).get("v") == "roundabout"}
    ex, ey = rs["points_en"][-1]
    for dest, L in after.items():
        assert L["tile"] == "knyszyn" and L["replacesRoute"] == ""
        assert L["graphNodes"][0] == rs["graph_nodes"][-1], L["id"]
        assert L["graphNodes"][1] != rs["graph_nodes"][-2], L["id"]           # no U-turn onto the arrival edge
        assert abs(L["e"][0] - ex) < 0.01 and abs(L["n"][0] - ey) < 0.01, L["id"]
        assert any(n.rstrip("s") in ring or n in ring for n in L["graphNodes"]), L["id"]
        twin = next(x for x in links if x["replacesRoute"] == "knyszyn" and x["destination"] == dest)
        assert abs(L["endX"] - twin["endX"]) < 0.05 and abs(L["endY"] - twin["endY"]) < 0.05, L["id"]
        # heading change at the join < 90 deg (it was 117 deg straight from the node before the corner was rounded)
        import math
        a = (ex - rs["points_en"][-2][0], ey - rs["points_en"][-2][1])
        b = (L["e"][1] - L["e"][0], L["n"][1] - L["n"][0])
        ang = math.degrees(math.acos((a[0] * b[0] + a[1] * b[1]) / math.hypot(*a) / math.hypot(*b)))
        assert ang < 90.0, (L["id"], ang)
    assert reg["anchorX"] and reg["anchorY"]


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


def test_after_route_start_rounded_on_one_way_arrival():
    """Codex review s24 (ADR 0289 'Recenzja s24'): the start corner of an `after_route` link is rounded with the arrival
    edge whether or not a way back exists. One-way arrival c -> u (no u -> c): the arrival edge is still returned;
    two-way: it is returned and the back edge removed; no came_from: nothing."""
    import networkx as nx
    one = nx.DiGraph()
    one.add_edge("c", "u", id="e_in", length=40.0)
    one.add_edge("u", "v", id="e_out", length=30.0)
    assert RL.arrival_edge(one, "u", "c") == ("e_in", 40.0)
    assert one.has_edge("c", "u") and not one.has_edge("u", "c")
    two = nx.DiGraph()
    two.add_edge("c", "u", id="e_in", length=40.0)
    two.add_edge("u", "c", id="e_back", length=40.0)
    two.add_edge("u", "v", id="e_out", length=30.0)
    assert RL.arrival_edge(two, "u", "c") == ("e_in", 40.0)
    assert not two.has_edge("u", "c")                       # no U-turn onto the arrival edge
    assert RL.arrival_edge(two, "u", None) is None
