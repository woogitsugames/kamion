"""ADR 0237 addendum D38: implied sidewalks in the built-up area (opt-in per region) and the authored `cluster: separate`
node override (a parking aisle off a street is its own T, not an arm of the crossroads 23 m away).

Synthetic networks + the git data of knyszyn, bialystok-industrial-c and bialystok-dojlidy (no Data/raw needed)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from shapely.geometry import LineString, Polygon

from roads import junctions as J
from roads import network as NW
from roads import pipeline
from roads import standards as S
from streetscape import pavements as PVM

REPO = Path(__file__).resolve().parents[2]
SZKOLNA_X = np.array([761246.537 - 761611.0, 612053.206 - 612607.0])    # OSM node 1134846746, region-local
RULE = {"id": "r", "kind": "pavement_rules", "implied_sidewalks": True}


# ------------------------------------------------------------------------------------------------ tag rule
@pytest.mark.parametrize("tags,left,right", [
    (None, None, None),
    ({"sidewalk": "no"}, False, False),
    ({"sidewalk": "none"}, False, False),
    ({"sidewalk": "separate"}, False, False),          # the mapped footway is the sidewalk
    ({"sidewalk": "both"}, True, True),
    ({"sidewalk": "yes"}, True, True),
    ({"sidewalk": "left"}, True, False),
    ({"sidewalk": "right"}, False, True),
    ({"sidewalk:right": "no"}, None, False),
    ({"sidewalk:both": "no"}, False, False),
    ({"sidewalk": "both", "sidewalk:left": "no"}, False, True),     # the side key wins over the general one
])
def test_osm_sidewalk_tags(tags, left, right):
    assert PVM.osm_sidewalk(tags, "left") is left
    assert PVM.osm_sidewalk(tags, "right") is right


def test_eligible_streets_by_class_and_surface():
    r = PVM.implied_rules([RULE])
    for hw in ("residential", "tertiary", "secondary", "unclassified"):
        assert PVM.eligible(hw, "asphalt", r) and PVM.eligible(hw, None, r)
    for hw in ("service", "track", "path", "living_street", "primary", "footway"):
        assert not PVM.eligible(hw, "asphalt", r)
    for surf in ("unpaved", "ground", "gravel", "dirt"):
        assert not PVM.eligible("residential", surf, r)
    assert PVM.eligible("residential", "paving_stones", r)


def test_rule_is_opt_in():
    assert PVM.implied_rules([]) is None
    assert PVM.implied_rules([{"kind": "pavement_rules", "crossing_kerb_drops": True}]) is None
    assert PVM.implied_rules([RULE])["highways"] == PVM.IMPLIED_HIGHWAYS
    custom = PVM.implied_rules([{"kind": "pavement_rules", "implied_sidewalks": {"highways": ["primary"]}}])
    assert custom["highways"] == ("primary",) and custom["unpaved"] == PVM.IMPLIED_UNPAVED


def test_built_up_adapter_reads_residential_bdot_zabudowa_only():
    def f(rodzaj, x0):
        return {"props": {"rodzaj": rodzaj},
                "geometry": {"type": "Polygon", "coordinates": [[[x0, 0], [x0 + 10, 0], [x0 + 10, 10], [x0, 10], [x0, 0]]]}}
    src = {"bdot10k": {"OT_PTZB_A": [f("jednorodzinna", 1000.0), f("przemysłowo-składowa", 5000.0)]}}
    a = PVM.built_up_area(src, (0.0, 0.0))
    assert a.contains(LineString([(1005, 5), (1005, 5 + PVM.BUILT_UP_ROADSIDE_M - 1)]))
    assert not a.contains(LineString([(5005, 5), (5006, 5)]))
    assert PVM.built_up_area(None, (0.0, 0.0)).is_empty


# ------------------------------------------------------------------------------------------------ synthetic street
def _graph(highway="residential", surface="asphalt", extra=None, length=400.0):
    attrs = {"highway": {"v": highway}, "oneway": {"v": "no"}, "lanes": {"v": 2}, "maxspeed": {"v": 50},
             "surface": {"v": surface}, "width": {"v": 6.0}, **(extra or {})}
    return {"nodes": [{"id": "a", "x": 0.0, "y": 0.0}, {"id": "b", "x": 0.0, "y": length}],
            "edges": [{"id": "w1:a-b", "osm_way": 1, "from": "a", "to": "b", "attrs": attrs,
                       "geometry": [[0.0, 0.0], [0.0, length]]}]}


TOWN = Polygon([(-200, -50), (200, -50), (200, 250), (-200, 250)])     # built-up: first 250 m of the 400 m street


def _sides(graph, overrides=(RULE,), footways=(), area=TOWN):
    net = NW.load(graph, (0.0, 0.0), list(overrides))
    net.authored = list(overrides)
    net.built_up_area = area
    NW.assign_sides(net, list(footways))
    (c,) = net.chains
    return net, c


def _station(c, y):
    return int(np.argmin(np.abs(c.line.p[:, 1] - y)))


def test_town_street_gets_sidewalks_on_both_sides_inside_the_built_up_area_only():
    net, c = _sides(_graph())
    for sd in "LR":
        assert c.side[sd]["walk"][_station(c, 100)] and c.side[sd]["walk"][_station(c, 200)]
        assert not c.side[sd]["walk"][_station(c, 330)]
        i = _station(c, 100)
        assert c.side[sd]["raw"]["w"][i] == S.SIDEWALK_W and c.side[sd]["mat"][i] == 1
        assert c.side[sd]["kind"][i] == NW.URBAN
    assert net.implied_sidewalk_m == pytest.approx(2 * 260, abs=25)


def test_without_the_rule_nothing_changes():
    a = _sides(_graph(), overrides=())[1]
    b = _sides(_graph(), overrides=([{"id": "p", "kind": "pavement_rules", "crossing_kerb_drops": True}]))[1]
    for c in (a, b):
        assert not any(c.side[sd]["walk"].any() for sd in "LR")


@pytest.mark.parametrize("extra,left,right", [
    ({"sidewalk": {"v": "no"}}, False, False),
    ({"sidewalk": {"v": "separate"}}, False, False),
    ({"sidewalk:right": {"v": "no"}}, True, False),
    ({"sidewalk": {"v": "left"}}, True, False),
])
def test_osm_tags_win_over_the_rule(extra, left, right):
    # chain a -> b runs north: chain L = OSM left = west, R = east (the way is not reversed)
    _, c = _sides(_graph(extra=extra))
    i = _station(c, 100)
    assert bool(c.side["L"]["walk"][i]) is left and bool(c.side["R"]["walk"][i]) is right


def test_sidewalk_yes_outside_the_built_up_area():
    _, c = _sides(_graph(extra={"sidewalk": {"v": "both"}}))
    assert c.side["L"]["walk"][_station(c, 330)] and c.side["R"]["walk"][_station(c, 330)]


@pytest.mark.parametrize("highway,surface", [("service", "asphalt"), ("track", "asphalt"), ("path", "asphalt"),
                                             ("residential", "ground"), ("unclassified", "gravel"),
                                             ("residential", "dirt"), ("living_street", "paving_stones")])
def test_no_implied_sidewalk_on_minor_or_unpaved_ways(highway, surface):
    _, c = _sides(_graph(highway, surface))
    assert not any(c.side[sd]["walk"].any() for sd in "LR")


def test_a_mapped_path_set_back_from_the_kerb_is_the_sidewalk_of_that_side():
    path = LineString([(8.0, -50.0), (8.0, 300.0)])        # east, 5 m behind the kerb (carriageway edge at 3.0 m)
    _, c = _sides(_graph(), footways=[path])
    i = _station(c, 100)
    assert c.side["L"]["walk"][i] and not c.side["R"]["walk"][i]


# ------------------------------------------------------------------------------------------------ junction: minor tee
def _tee_graph():
    """Crossroads X at (0, 0) of a N-S street and an E-W street; 23 m north of it node T where a parking aisle leaves
    east for 13 m, then turns north (the geometry of Knyszyn Poludniowa x Szkolna, OSM node 7015352011)."""
    def e(eid, a, b, geom, hw="residential"):
        return {"id": eid, "osm_way": int(eid[1:].split(":")[0]), "from": a, "to": b, "geometry": geom,
                "attrs": {"highway": {"v": hw}, "oneway": {"v": "no"}, "lanes": {"v": 2}, "maxspeed": {"v": 50},
                          "surface": {"v": "asphalt"}, "width": {"v": 5.0}}}
    nodes = [{"id": k, "x": x, "y": y} for k, x, y in
             (("x", 0, 0), ("t", 9.6, 21.0), ("n", 85, 181), ("s", -66, -88), ("w", -152, 120), ("e", 64, -50),
              ("p", 46, 65))]
    edges = [e("w1:t-x", "t", "x", [[9.6, 21.0], [0, 0]]), e("w1:n-t", "n", "t", [[85, 181], [9.6, 21.0]]),
             e("w2:x-s", "x", "s", [[0, 0], [-66, -88]]), e("w3:w-x", "w", "x", [[-152, 120], [0, 0]]),
             e("w4:x-e", "x", "e", [[0, 0], [64, -50]]),
             e("w5:t-p", "t", "p", [[9.6, 21.0], [21.5, 14.9], [46, 65]], hw="service")]
    return {"nodes": nodes, "edges": edges}


def _juncs(overrides=()):
    net = NW.load(_tee_graph(), (0.0, 0.0), list(overrides))
    NW.assign_sides(net, [])
    return net, J.build_junctions(net, [])


SEPARATE = {"id": "sep", "target": {"node": "t"}, "set": {"cluster": "separate"}}


def test_minor_tee_is_detected():
    net, _ = _juncs()
    ends = J.chain_ends(net)
    assert J.minor_tee(net, "t", ends) and not J.minor_tee(net, "x", ends)


def test_without_the_override_the_parking_aisle_is_merged_into_the_crossroads():
    net, js = _juncs()
    (j,) = [j for j in js if "x" in j.nodes]
    assert set(j.nodes) == {"x", "t"}
    assert next(c for c in net.chains if {c.node_a, c.node_b} == {"x", "t"}).meta.get("absorbed")


def test_cluster_separate_keeps_a_t_junction_and_the_stub_between():
    net, js = _juncs([SEPARATE])
    jx = next(j for j in js if "x" in j.nodes)
    jt = next(j for j in js if "t" in j.nodes)
    assert jx is not jt and jx.nodes == ["x"] and jt.nodes == ["t"]
    stub = next(c for c in net.chains if {c.node_a, c.node_b} == {"x", "t"})
    assert not stub.meta.get("absorbed")                    # a crossing node on it is snapped (P-10, roads.markings)
    assert stub.t_a + stub.t_b < stub.length                # the two patches do not overlap
    assert not any(c.kind == "nose" for c in jx.corners + jt.corners)
    k = next(i for i, a in enumerate(jt.arms) if net.sec_list[int(a.chain.sec_idx[0])].highway == "service")
    assert jt.trims[k] < 13.0                               # trimmed before the bend of the aisle, not past it


def test_cluster_separate_on_a_real_junction_is_ignored_with_a_note():
    net, js = _juncs([{"id": "bad", "target": {"node": "x"}, "set": {"cluster": "separate"}}])
    j = next(j for j in js if "x" in j.nodes)
    assert set(j.nodes) == {"x", "t"}
    assert any("cluster: separate ignored" in n for n in j.notes)


# ------------------------------------------------------------------------------------------------ git data
def _region_net(region_id, authored=True):
    region = pipeline.load_region(region_id)
    origin = (region["origin"]["x"], region["origin"]["y"])
    ctx = json.loads((pipeline.REGIONS / region_id / "generated" / "osm_context.json").read_text(encoding="utf-8"))
    net, _g, overrides, _ = pipeline.build_network(region_id)
    net.region_id = region_id
    if authored:
        net.authored = overrides
    pts, foot = pipeline.ctx_local(ctx, origin)
    NW.assign_sides(net, foot)
    return net, pts, overrides


@pytest.mark.parametrize("region_id", ["bialystok-industrial-c", "bialystok-dojlidy"])
def test_city_regions_do_not_opt_in_and_keep_their_sides_and_junctions(region_id):
    net, pts, ov = _region_net(region_id)
    assert PVM.implied_rules(ov) is None
    assert not hasattr(net, "implied_sidewalk_m")
    assert not any(n.get("override", {}).get("cluster") for n in net.nodes.values())
    ref, _, _ = _region_net(region_id, authored=False)
    for c, r in zip(net.chains, ref.chains):
        for sd in "LR":
            assert np.array_equal(c.side[sd]["walk"], r.side[sd]["walk"]), (region_id, c.id, sd)


def test_knyszyn_opts_in_and_szkolna_poludniowa_get_sidewalks():
    net, pts, ov = _region_net("knyszyn")
    assert PVM.implied_rules(ov) is not None
    assert net.implied_sidewalk_m > 10_000                  # most town streets had no mapped sidewalk
    for c in net.chains:
        sec = net.sec_list[int(c.sec_idx[len(c.sec_idx) // 2])]
        way = int(sec.edge_id.split(":")[0].lstrip("w"))
        if way in (98071199, 98071222, 300806059, 1111506747):       # Szkolna / Poludniowa near the crossroads
            for i in range(len(c.line.s)):
                if 15.0 < float(np.hypot(*(c.line.p[i] - SZKOLNA_X))) < 60.0:     # the arms next to the crossroads
                    assert c.side["L"]["walk"][i] and c.side["R"]["walk"][i], (c.id, i)
        if sec.highway in ("service", "track") or sec.surface_osm in PVM.IMPLIED_UNPAVED:
            assert not c.meta.get("implied_sidewalk_m", {}).get("L") and not c.meta.get("implied_sidewalk_m", {}).get("R")


def test_knyszyn_szkolna_crossroads_is_four_arms_and_the_parking_tee_is_apart():
    net, pts, _ = _region_net("knyszyn")
    js = J.build_junctions(net, pts)
    jx = next(j for j in js if "n1134846746" in j.nodes)
    jt = next(j for j in js if "n7015352011" in j.nodes)
    assert jx is not jt and len(jx.arms) == 4 and len(jt.arms) == 3
    assert not any(c.kind == "nose" for c in jx.corners)
    assert "knyszyn-szkolna-parking-tee-d38" in {o["id"] for o in net.overrides_applied}


def test_knyszyn_szkolna_crossroads_gets_all_four_zebras():
    """OSM crossing:markings=zebra nodes 11514832006-009 (API 0.6, 2026-11-16) - before D38 two had no P-10."""
    from roads import markings as MK
    from roads import profile as P
    region = pipeline.load_region("knyszyn")
    o = (region["origin"]["x"], region["origin"]["y"])
    tm = json.loads((pipeline.REGIONS / "knyszyn" / "terrain.json").read_text(encoding="utf-8"))
    bb = tm["bbox"]
    hf = P.Heightfield(np.full((int(bb[3] - bb[1]) + 2, int(bb[2] - bb[0]) + 2), 120.0), bb, o)   # flat: plan only
    w = pipeline.build("knyszyn", hf=hf, collision=False)
    rep = {}
    MK.build_markings(w.buf, w.net, w.junctions, w.ctx["points"], rep)
    zebras = {11514832006, 11514832007, 11514832008, 11514832009}
    assert not zebras & set(rep.get("crossings_skipped", []))
    xy = {p["osm_node"]: np.array([p["e"], p["n"]]) for p in w.ctx["points"] if p["osm_node"] in zebras}
    placed = [c.line.p[c.idx(s)] for c in w.net.chains for s in c.meta.get("crossings", [])]
    for osm, q in xy.items():
        assert min(float(np.hypot(*(p - q))) for p in placed) < 3.0, osm
