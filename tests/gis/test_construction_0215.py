"""ADR 0215 (owner decision D65 p.6): a carriageway that exists in OSM but is not open to traffic.

Authored override `set: {construction: true}` (schema: tools/worldgen/roads/closures.py) -> no horizontal markings,
no rule lamps, building-site surface (WORKING_VALUE), no edge in the routing graph. Synthetic geometry only (no
Data/raw).

ADR 0215 r2 (PR #80 verification, owner decision): dk65-05 itself no longer uses the flag - its new DK65 carriageway
is cut from the road graph (graph_filter.authored.json) and reproduced as a `construction_site` corridor, the mechanism
of dk65-06 (ADR 0214), so the site is continuous across the seam. The last tests read the committed dk65-05 region
data and guard that state; the `construction: true` schema stays available and is covered by the synthetic tests."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))

from navgraph import build_route_graph as brg  # noqa: E402
from roads import closures, markings, network  # noqa: E402
from roads.meshing import MeshBuf  # noqa: E402

ORIGIN = (767755.0, 602367.0)
NEW_DK65 = {1151531612, 1151531613, 1151531608}        # dk65-05: the new DK65 carriageways (primary, ref 65)


def _a(**kw):
    return {k: {"v": v, "src": "osm", "conf": "high"} for k, v in kw.items()}


def _graph():
    """Two separate 400 m roads: an open two-way secondary (way 10, split in two edges at n1) and, 60 m north of it,
    a one-way two-lane primary (way 20) that shares no node with it - the layout of the new DK65 carriageway in dk65-05."""
    ox, oy = ORIGIN

    def node(nid, e, n, **kw):
        return {"id": nid, "x": ox + e, "y": oy + n, **kw}

    def edge(eid, way, a, b, pts, **attrs):
        return {"id": eid, "osm_way": way, "from": a, "to": b, "geometry": [[ox + e, oy + n] for e, n in pts],
                "attrs": _a(**attrs)}

    nodes = [node("n0", -200, 0, boundary=True), node("n1", 0, 0, osm_node=1), node("n2", 200, 0, boundary=True),
             node("n3", -200, 60, boundary=True), node("n4", 200, 60, boundary=True)]
    old = dict(highway="secondary", oneway="no", lanes=2, maxspeed=90, surface="asphalt", name="Studzienna")
    edges = [edge("w10:0-1", 10, "n0", "n1", [(-200, 0), (0, 0)], **old),
             edge("w10:1-2", 10, "n1", "n2", [(0, 0), (200, 0)], **old),
             edge("w20:3-4", 20, "n3", "n4", [(-200, 60), (200, 60)], highway="primary", oneway="yes", lanes=2,
                  maxspeed=100, surface="asphalt", ref="65", **{"turn:lanes": "through|through;right"})]
    return {"nodes": nodes, "edges": edges}


def _ov(target=None, **st):
    return {"id": "new-carriageway-closed", "target": target or {"osm_way": [20]}, "set": {"construction": True, **st}}


def _net(overrides=None):
    net = network.load(_graph(), ORIGIN, overrides)
    for c in net.chains:                 # flat profile: the marking stage only needs heights to drape the paint
        c.z = np.zeros(len(c.line.s))
        c.e = np.zeros(len(c.line.s))
    return net


def _paint(net):
    buf, report = MeshBuf(), {}
    markings._build_markings(buf, net, [], [], report)
    return buf.parts, report


# ---------------------------------------------------------------------------------------------- schema / targets
def test_target_matching_by_way_and_by_edge():
    edges = _graph()["edges"]
    assert closures.construction_edge_ids(edges, [_ov()]) == {"w20:3-4"}
    assert closures.construction_edge_ids(edges, [_ov({"osm_way": 10})]) == {"w10:0-1", "w10:1-2"}
    assert closures.construction_edge_ids(edges, [_ov({"edge": "w10:1-2"})]) == {"w10:1-2"}
    assert closures.construction_edge_ids(edges, [_ov({"osm_way": [999]})]) == set()
    assert closures.construction_edge_ids(edges, []) == set()


def test_only_edge_overrides_with_a_true_flag_close_a_road():
    edges = _graph()["edges"]
    width_only = {"id": "w", "target": {"osm_way": [20]}, "set": {"width": 6.9}}
    off = {"id": "f", "target": {"osm_way": [20]}, "set": {"construction": False}}
    area = {"id": "a", "kind": "paved_area", "target": {"osm_way": [20]}, "set": {"construction": True}}
    assert closures.construction_edge_ids(edges, [width_only, off, area]) == set()


# ------------------------------------------------------------------------------------------------ road sections
def test_section_is_flagged_with_provenance_and_stripped():
    net = _net([_ov()])
    sec = net.sections["w20:3-4"]
    assert sec.construction is True
    assert sec.provenance["construction"] == "authored_override:new-carriageway-closed"
    assert sec.provenance["authored_override"] == "new-carriageway-closed"
    assert sec.provenance["no_lamps"] == "new-carriageway-closed"       # streetscape.furniture.lamps skips the chain
    assert sec.edge_lines == "none" and sec.turn_fwd is None and sec.turn_bwd is None
    assert sec.surface_mat == closures.CONSTRUCTION_SURFACE_MAT == "road_gravel"
    assert net.overrides_applied == [{"id": "new-carriageway-closed", "targets": ["w20:3-4"]}]
    assert net.overrides_stale == []
    for eid in ("w10:0-1", "w10:1-2"):                                  # the open road is untouched
        s = net.sections[eid]
        assert s.construction is False and s.surface_mat == "road_asphalt" and "construction" not in s.provenance


def test_default_is_open_and_geometry_is_unchanged():
    a, b = _net(), _net([_ov()])
    assert all(not s.construction for s in a.sec_list)
    assert a.sections["w20:3-4"].turn_fwd == ["through", "through;right"]
    for ca, cb in zip(a.chains, b.chains):                              # closing a road moves nothing
        assert ca.id == cb.id and np.array_equal(ca.line.p, cb.line.p) and np.array_equal(ca.hw, cb.hw)
    assert a.sections["w20:3-4"].width == b.sections["w20:3-4"].width


def test_explicit_surface_wins_over_the_working_value():
    sec = _net([_ov(surface="asphalt_new")]).sections["w20:3-4"]
    assert sec.construction and sec.surface_mat == "road_asphalt_new"


def test_unknown_way_is_reported_stale():
    net = _net([_ov({"osm_way": [999]})])
    assert net.overrides_stale == ["new-carriageway-closed"] and not any(s.construction for s in net.sec_list)


# ----------------------------------------------------------------------------------------------------- markings
def test_no_horizontal_markings_on_a_construction_carriageway():
    open_parts, _ = _paint(_net())
    closed_parts, report = _paint(_net([_ov()]))
    on = lambda parts, cid: [p for p in parts if p.src.endswith("@" + cid)]          # noqa: E731
    assert on(open_parts, "c:w20:3-4"), "the open primary carriageway is painted (lane line, arrows)"
    assert {p.src.split("@")[0] for p in on(open_parts, "c:w20:3-4")} >= {"lane", "P-8"}
    assert on(closed_parts, "c:w20:3-4") == []
    assert all(p.layer == "markings" for p in closed_parts)
    # the open road keeps exactly the paint it had
    key = lambda p: (p.src, len(p.T), round(float(p.V[:, :2].sum()), 3))             # noqa: E731
    assert sorted(map(key, on(open_parts, "c:w10:0-1"))) == sorted(map(key, on(closed_parts, "c:w10:0-1")))
    assert on(closed_parts, "c:w10:0-1")


def test_edge_lines_rule_returns_nothing_for_construction():
    net = _net([_ov()])
    sec = net.sections["w20:3-4"]
    sec.edge_lines = "both"                      # even if a later override asks for lines
    assert markings.unmarked(sec) and markings.edge_lines(sec, sec.width / 2, 1) == []
    assert not markings.unmarked(net.sections["w10:0-1"])


def test_crossing_node_on_a_construction_carriageway_is_not_painted():
    pts = [{"kind": "highway=crossing", "e": 0.0, "n": 60.0, "osm_node": 77},
           {"kind": "highway=crossing", "e": 100.0, "n": 0.0, "osm_node": 78}]
    buf, report = MeshBuf(), {}
    markings._build_markings(buf, _net([_ov()]), [], pts, report)
    zebra = {p.src.split("@")[1] for p in buf.parts if p.src.startswith("P-10")}
    assert zebra == {"c:w10:0-1"}


# ------------------------------------------------------------------------------------------------- routing graph
def test_routing_graph_has_no_construction_edge_and_no_orphan_node():
    g = _graph()
    full = brg.build(g, ORIGIN, [])
    t = brg.build(g, ORIGIN, [], closed_edges=closures.construction_edge_ids(g["edges"], [_ov()]))
    assert [e["id"] for e in full["edges"]] == ["w10:0-1", "w10:1-2", "w20:3-4"] and full["closed_edges"] == []
    assert [e["id"] for e in t["edges"]] == ["w10:0-1", "w10:1-2"] and t["closed_edges"] == ["w20:3-4"]
    assert len(full["nodes"]) == 5 and len(t["nodes"]) == 3            # n3, n4 only served the closed carriageway
    assert all(0 <= e["from"] < 3 and 0 <= e["to"] < 3 for e in t["edges"])
    assert t["reachability"]["off_edges"] == 0 and t["reachability"]["components"] == 1
    back = brg.parse(brg.serialize(t))                                  # the binary carries the reduced graph
    assert len(back["edges"]) == 2 and len(back["nodes"]) == 3


def test_closing_one_edge_keeps_shared_nodes():
    g = _graph()
    t = brg.build(g, ORIGIN, [], closed_edges={"w10:1-2"})
    assert [e["id"] for e in t["edges"]] == ["w10:0-1", "w20:3-4"]
    assert len(t["nodes"]) == 4                                         # n1 stays (still an end of w10:0-1), n2 goes


def test_build_is_deterministic_with_closures():
    g = _graph()
    a = brg.serialize(brg.build(g, ORIGIN, [], closed_edges={"w20:3-4"}))
    b = brg.serialize(brg.build(json.loads(json.dumps(g)), ORIGIN, [], closed_edges=["w20:3-4"]))
    assert a == b


# ------------------------------------------------------------------------------------- dk65-05 region data (in git)
@pytest.fixture(scope="module")
def dk65_05():
    d = REPO / "Data" / "Regions" / "dk65-05"
    g = json.loads((d / "roads.graph.json").read_text(encoding="utf-8"))
    ov = yaml.safe_load((d / "overrides.yaml").read_text(encoding="utf-8"))["overrides"]
    route = json.loads((d / "route_start.json").read_text(encoding="utf-8"))
    gf = json.loads((d / "graph_filter.authored.json").read_text(encoding="utf-8"))
    return g, ov, route, gf


def test_dk65_05_new_carriageway_is_not_in_the_road_graph(dk65_05):
    """r2: the three ways are dropped by the authored graph filter - no ribbon is built, nothing routes over them."""
    g, ov, route, gf = dk65_05
    assert set(gf["drop_osm_ways"]) == NEW_DK65 and "D65" in gf["reason"]
    assert not {e["osm_way"] for e in g["edges"]} & NEW_DK65
    assert not [e for e in g["edges"] if e["attrs"]["highway"]["v"] == "primary"], "every primary edge was the new DK65"
    assert route["edge"] and set(route["edge"]) <= {e["id"] for e in g["edges"]}, "control route (Ełcka / Studzienna) intact"
    origin = brg.read_origin(str(REPO / "Data" / "Regions" / "dk65-05"))
    assert not {e["osm_way"] for e in brg.build(g, origin, [])["edges"]} & NEW_DK65


def test_dk65_05_uses_one_site_mechanism(dk65_05):
    """No `construction: true` ribbon left in dk65-05 (it ended at the seam with dk65-06); the carriageway is a
    construction_site corridor with the three ways as `not_open` axes, 10 m half-width like the arm in dk65-06."""
    g, ov, _, _ = dk65_05
    assert not closures.construction_edge_ids(g["edges"], ov)
    assert not [o for o in ov if (o.get("set") or {}).get("construction")]
    sites = [o for o in ov if o.get("kind") == "construction_site"]
    assert len(sites) == 1
    axes = [a for a in sites[0]["axes"] if a["class"] == "not_open"]
    assert {a["osm_way"] for a in axes} == NEW_DK65 and all(a["half_width_m"] == 10.0 for a in axes)


def test_site_corridor_meets_dk65_06_at_the_seam(dk65_05):
    """Seam y = 603391 (dk65-05 north / dk65-06 south): every not-open axis of dk65-06 that reaches the seam has an
    axis of the same way in dk65-05 crossing the seam at the same x (+-0.1 m) with the same half-width."""
    _, ov, _, _ = dk65_05
    ov6 = yaml.safe_load((REPO / "Data" / "Regions" / "dk65-06" / "overrides.yaml").read_text(encoding="utf-8"))["overrides"]
    Y = 603391.0

    def crossings(ovs):
        out = {}
        for o in ovs:
            if o.get("kind") != "construction_site":
                continue
            for a in o["axes"]:
                if a["class"] != "not_open":
                    continue
                L = a["line_epsg2180"]
                for (x0, y0), (x1, y1) in zip(L, L[1:]):
                    if min(y0, y1) <= Y <= max(y0, y1) and y0 != y1:
                        out[a["osm_way"]] = (x0 + (x1 - x0) * (Y - y0) / (y1 - y0), a["half_width_m"])
        return out

    c5, c6 = crossings(ov), crossings(ov6)
    assert c6 and set(c6) == set(c5) == {1151531608, 1151531613}
    for w in c6:
        assert abs(c5[w][0] - c6[w][0]) <= 0.1 and c5[w][1] == c6[w][1], (w, c5[w], c6[w])
