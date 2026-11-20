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
        # lane point of the oblique Piastowska crossing lies ~2.2 m off the seam line; joined within JOIN_TOL_M
        assert TG.on_seam([j["x"], j["y"]], g[j["from"]], j["side"], eps=RL.JOIN_TOL_M), j


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
        # bialystok-knyszynska: ADR 0292 (destination s8: Kleeberga straight on south instead of the rondo Kresowian exit)
        # C / wygoda: D81 trip to Dojlidy (ADR 0290); tykocin: ADR 0303 (destination tykocin: the trip ends on the Rynek, the control route runs on to the tile edge)
        assert L["replacesRoute"] in ("", "knyszyn", "s8-03", "bialystok-knyszynska", "tykocin",
                                   "bialystok-industrial-c", "bialystok-wygoda"), L["id"]
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


# ---------------------------------------------------------------- swept path of the truck along every link (hard gate)
def _swept():
    sys.path.insert(0, str(ROOT / "tools" / "worldgen" / "qa"))
    import link_swept_check as SW
    return SW


def test_links_keep_tyres_on_hard_surface():
    """knyszyn-r24 (ADR 0289 'Recenzja s24', Codex P1): tractor + 13.6 m semitrailer following each link exactly
    (kinematic swept path, qa/link_swept_check.py) has 0 tyre edge points off the built hard surface (asphalt, kerbs,
    paving, apron; not grass / verge / roundabout island). Links of tiles not built on this machine are skipped."""
    SW = _swept()
    checked = 0
    for L in _links()["links"]:
        if not SW.built(L["tile"]):
            continue
        r = SW.check(L["id"])
        assert r["tyre_points"] > 100, L["id"]
        assert r["off_hard"] == 0, (L["id"], r["off_hard"], r["first_off"])
        checked += 1
    if not checked:
        pytest.skip("no link tile built on this machine (build_world not run)")


def test_monki_corner_needs_no_swing_after_d94():
    """D94 / ADR 0306: with the truck kerb returns and 16 m corners of the compact roundabout the Monki link keeps its
    tyres on the hard surface without the authored swing of knyszyn-r24 (the swing was removed from route_links.yaml)."""
    SW = _swept()
    if not SW.built("knyszyn"):
        pytest.skip("knyszyn not built on this machine")
    import yaml
    cfg = yaml.safe_load(RL.SRC.read_text(encoding="utf-8"))
    L = next(x for x in cfg["links"] if x["id"] == "knyszyn-rynek-to-dk65-w")
    assert not L.get("swing"), "D94 geometry: no authored swing needed"
    r = SW.check("knyszyn-rynek-to-dk65-w")
    assert r["off_hard"] == 0, r


def test_tykocin_trip_ends_on_the_rynek_0303():
    """ADR 0303: the trip `tykocin` ends on the south side of the Rynek (link stop), not on the south tile edge; the GPS
    goal (nav_trips.json) is the same point; the stop lies in the 47 m of kerb between the driveways at OSM nodes
    13718175880 / 13718175884 with the whole 16.5 m combination behind it on the straight; and the control route of the
    tile (cameras / QA) stays on DW671 (no service way, ADR 0300 kerb at s 1902)."""
    L = next(x for x in _links()["links"] if x["id"] == "tykocin-dw671-to-rynek")
    assert L["replacesRoute"] == "tykocin" and L["destination"] == "tykocin"
    t = {g["id"]: g for g in _graph()["tiles"]}["tykocin"]
    ex, ey = L["endX"], L["endY"]
    assert abs(ex - 751818.0) < 1.5 and abs(ey - 600215.0) < 1.5, (ex, ey)
    assert 751806.8 < ex - 0 and ex + 16.5 < 751854.1, "combination between the two driveways"
    # last 20 m heading west (straight): the trailer stands on the straight, not in the corner
    de, dn = L["e"][-1] - L["e"][-11], L["n"][-1] - L["n"][-11]
    assert de < -19.0 and abs(dn) < 3.0, (de, dn)
    trips = json.loads((ROOT / "game/Assets/_Project/Gameplay/Resources/Nav/nav_trips.json").read_text(encoding="utf-8"))
    ty = next(x for x in trips["trips"] if x["id"] == "tykocin")
    assert ty["goalTile"] == "tykocin" and abs(ty["goalX"] - ex) < 0.01 and abs(ty["goalY"] - ey) < 0.01
    g = json.loads((ROOT / "Data/Regions/tykocin/roads.graph.json").read_text(encoding="utf-8"))
    hw = {e["id"]: e["attrs"]["highway"]["v"] for e in g["edges"]}
    rs = json.loads((ROOT / "Data/Regions/tykocin/route_start.json").read_text(encoding="utf-8"))
    assert all(hw[e] == "secondary" for e in rs["edge"]), sorted({e for e in rs["edge"] if hw[e] != "secondary"})
    assert t["anchorX"] < ex < t["xmax"]


def test_parallel_edges_keep_the_shorter_0303():
    """ADR 0303: roadgraph.to_digraph keeps the shorter of two ways between the same node pair (dw671-tykocin-03: the
    46 m DW671 edge, not the 124 m service loop 553605081 beside it)."""
    import roadgraph
    nodes = [{"id": "a", "x": 0.0, "y": 0.0}, {"id": "b", "x": 46.0, "y": 0.0}]
    mk = lambda i, L: {"id": i, "from": "a", "to": "b", "length_m": L, "attrs": {"oneway": {"v": "no"}}}
    for order in ([mk("dw", 46.0), mk("svc", 124.0)], [mk("svc", 124.0), mk("dw", 46.0)]):
        g = roadgraph.to_digraph({"nodes": nodes, "edges": order})
        assert g["a"]["b"]["id"] == "dw" and g["b"]["a"]["id"] == "dw"
    rs = json.loads((ROOT / "Data/Regions/dw671-tykocin-03/route_start.json").read_text(encoding="utf-8"))
    assert not any(e.startswith("w553605081:") for e in rs["edge"])
