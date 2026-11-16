"""ADR 0279 "A-7 z T-1 - klasyfikacja zabudowy" (D33): one built-up / speed classification (built_up.Zone) for every
sign rule, on synthetic data only (no Data/raw, no region tiles).

  - obszar zabudowany = between D-42 and D-43 (Prawo o ruchu drogowym t.j. Dz.U. 2024 poz. 1251 art. 2 pkt 15): OSM
    city_limit / PL:D-42 / PL:D-43 where mapped, else the BDOT10k rule (Z1 pkt 5.2.48.1-2); NOT the generated kerb;
  - permitted speed without a B-33 = art. 20 (50 built-up, 20 strefa zamieszkania, 90 / 100 / 140 outside);
  - A-7 + T-1 150-300 m before the junction when the MINOR road (the one carrying the A-7) has v > 60 km/h
    (Dz.U. 2019 poz. 2311 zał. 1 pkt 2.2.8, s. 64, rys. 2.2.8.2)."""

from __future__ import annotations

from types import SimpleNamespace as NS

import numpy as np
import pytest
import shapely
from shapely.geometry import LineString

ORIGIN = (761611.0, 612607.0)     # Knyszyn tile origin: outside built_up_places.json (Białystok)
MINOR_L = 700.0


def _edge(eid, a, b, pts, hw, ms=None):
    ox, oy = ORIGIN
    at = {"highway": {"v": hw}, "oneway": {"v": "no"}, "lanes": {"v": 2}}
    if ms:
        at["maxspeed"] = {"v": ms, "src": "osm"}
    else:
        at["maxspeed"] = {"v": 50, "src": "default", "conf": "low"}     # as roads.graph.json without a tag
    return {"id": eid, "from": a, "to": b, "geometry": [[ox + px, oy + py] for px, py in pts], "attrs": at}


def _t_junction(main_speed=90, minor_speed=None, kerb_minor=True, stop=False):
    """T junction at the origin: primary east-west (OSM maxspeed main_speed), tertiary MINOR_L m to the south with no
    maxspeed tag (art. 20 default). kerb_minor: footways along the minor road -> the generator kerbs it (URBAN)."""
    from roads import network
    from roads.junctions import build_junctions
    from streetscape import furniture as FU
    ox, oy = ORIGIN
    g = {"nodes": [{"id": "n0", "x": ox, "y": oy}, {"id": "n1", "x": ox - 400.0, "y": oy},
                   {"id": "n2", "x": ox + 400.0, "y": oy}, {"id": "n3", "x": ox, "y": oy - MINOR_L}],
         "edges": [_edge("e1", "n0", "n1", [(0, 0), (-400, 0)], "primary", main_speed),
                   _edge("e2", "n0", "n2", [(0, 0), (400, 0)], "primary", main_speed),
                   _edge("e3", "n0", "n3", [(0, 0), (0, -MINOR_L)], "tertiary", minor_speed)]}
    net = network.load(g, ORIGIN)
    for c in net.chains:
        k = len(c.line.s)
        c.z, c.e = np.zeros(k), np.zeros(k)
    foot = [LineString([(x, -15.0), (x, -MINOR_L)]) for x in (-6.0, 6.0)] if kerb_minor else []
    ctx = [{"kind": "highway=stop", "e": 0.0, "n": -12.0, "osm_node": 7}] if stop else []
    network.assign_sides(net, foot, built_up=True, walkways=foot)
    juncs = build_junctions(net, ctx)
    network.assign_sides(net, foot, built_up=True, walkways=foot, trims=True)
    pl = FU.Placer(lambda e, n: np.zeros(np.shape(e)))
    rep, codes = {}, set()
    FU.junction_signs(pl, net, juncs, ctx, rep, codes)
    minor = next(c for c in net.chains if c.id.startswith("c:e3"))
    return net, juncs, pl, codes, minor


def _houses(x0, x1, y0, y1, rodzaj="jednorodzinna"):
    ox, oy = ORIGIN
    ring = [[ox + x0, oy + y0], [ox + x1, oy + y0], [ox + x1, oy + y1], [ox + x0, oy + y1], [ox + x0, oy + y0]]
    return {"geometry": {"type": "Polygon", "coordinates": [ring]}, "props": {"rodzaj": rodzaj}}


def _node(i, e, n, tags):
    return {"osm_node": i, "tags": tags, "geometry": {"type": "Point", "coordinates": [ORIGIN[0] + e, ORIGIN[1] + n]}}


def _rule(net, juncs, pl, codes, src):
    from streetscape import built_up as BU
    rep = {}
    BU.rule_signs(pl, net, src, np.array(ORIGIN), juncs, rep, codes)
    return rep["built_up"]


# --------------------------------------------------------------------------------------------- speed (art. 20)
def test_default_speed_art20():
    from streetscape import built_up as BU

    def sec(hw, cls="G", oneway=False, lanes=2):
        return NS(highway=hw, cls=cls, oneway=oneway, lanes=lanes, maxspeed=50.0, maxspeed_src="default")
    assert BU.legal_speed(sec("tertiary", "Z"), True) == 50.0                       # ust. 1
    assert BU.legal_speed(sec("tertiary", "Z"), False) == 90.0                      # ust. 3 pkt 1 lit. d
    assert BU.legal_speed(sec("living_street", "D"), False) == 20.0                 # ust. 2 (strefa zamieszkania)
    assert BU.legal_speed(sec("living_street", "D"), True) == 20.0
    assert BU.legal_speed(sec("trunk", "GP", oneway=True, lanes=2), False) == 100.0  # lit. c
    assert BU.legal_speed(sec("trunk", "GP", oneway=True, lanes=2), True) == 50.0
    assert BU.legal_speed(sec("motorway", "A", oneway=True, lanes=2), False) == 140.0  # lit. a
    tagged = NS(highway="tertiary", cls="Z", oneway=False, lanes=2, maxspeed=70.0, maxspeed_src="osm")
    assert BU.legal_speed(tagged, True) == 70.0 and BU.legal_speed(tagged, False) == 70.0   # B-33 / OSM wins


# --------------------------------------------------------------------------------------------- A-7 + T-1
def test_a7_t1_outside_built_up_on_kerbed_minor_road():
    """The bug of #154: a kerbed minor road outside any D-42..D-43 counted as built-up (50 km/h) -> no A-7 + T-1.
    Now: no place there -> 90 km/h (art. 20 ust. 3 pkt 1 lit. d) -> A-7 + T-1 150-300 m before the junction."""
    from streetscape import built_up as BU
    net, juncs, pl, codes, minor = _t_junction()
    s_mid = minor.length / 2
    assert BU.kerbed(minor, s_mid), "test precondition: the generator kerbs the minor road"
    out = _rule(net, juncs, pl, codes, {"osm": {"nodes": [], "areas": []}, "bdot10k": {}})
    (adv,) = out["advance"]
    assert adv["plate"].startswith("T-1_") and adv["v_kmh"] == 90.0 and adv["kerbed"] is True
    trim = minor.t_a
    assert 150.0 <= adv["d_m"] - trim <= 300.0 + 10.0            # pkt 2.2.8: 150-300 m from the junction
    dist = int(adv["plate"].split("_")[1])
    assert dist % 10 == 0 and 150 <= dist <= 310                 # pkt 2.1.3: real distance, to 10 m
    assert out["placed"]["A-7"] == 1 and any(c.startswith("T-1_") for c in codes)
    # and the kerb alone does not make a built-up area: no D-42 / D-43 pair on the kerbed road
    assert out["boundaries"] == []


def test_a7_t1_stop_plate_with_b20():
    net, juncs, pl, codes, minor = _t_junction(stop=True)
    out = _rule(net, juncs, pl, codes, {"osm": {"nodes": [], "areas": []}, "bdot10k": {}})
    (adv,) = out["advance"]
    assert adv["code"] == "B-20" and adv["plate"].startswith("T-1S_")         # pkt 3.2.21: "Stop <m>"


def test_no_a7_t1_inside_built_up_area_bdot():
    """Houses along the whole minor road (BDOT10k OT_PTZB_A jednorodzinna): built-up -> 50 km/h -> no advance post."""
    net, juncs, pl, codes, minor = _t_junction()
    src = {"osm": {"nodes": [], "areas": []},
           "bdot10k": {"OT_PTZB_A": [_houses(10, 60, -MINOR_L, -20), _houses(-60, -10, -MINOR_L, -20)]}}
    out = _rule(net, juncs, pl, codes, src)
    assert out["advance"] == [] and out["advance_dropped"] == []
    assert "A-7" not in out["placed"]


def test_no_a7_t1_inside_osm_city_limit():
    """No BDOT data, an OSM city_limit (D-42) on the minor road 500 m from the junction facing traffic towards it:
    the junction lies between the D-42 and the (implicit) D-43 -> built-up -> no A-7 + T-1. The same sign facing
    away (traffic leaving towards the far end) puts the junction outside -> A-7 + T-1."""
    from streetscape import built_up as BU
    for direction, want in (("backward", 0), ("forward", 1)):
        net, juncs, pl, codes, minor = _t_junction()
        # chain c:e3 runs from the junction (s = 0) south; "backward" = travel north = towards the junction
        nodes = [_node(11, 0.0, -500.0, {"traffic_sign": "city_limit", "name": "X", "direction": direction})]
        src = {"osm": {"nodes": nodes, "areas": []}, "bdot10k": {}}
        out = _rule(net, juncs, pl, codes, src)
        assert len(out["advance"]) == want, (direction, out)
        z = BU.zone_for(net, src, np.array(ORIGIN))
        assert z.at(minor, 100.0) is (want == 0) and z.at(minor, 650.0) is (want == 1)
        assert out["boundaries"] == []                       # OSM wins: no rule D-42 / D-43 next to it


def test_a7_t1_uses_minor_road_speed_not_major():
    """pkt 2.2.8: the A-7 stands on the MINOR road; "na drogach o dopuszczalnej prędkości powyżej 60 km/h" is the
    road the sign is on (rys. 2.2.8.2: advance posts on the minor road only). Major 50 / minor 90 -> advance;
    major 90 / minor 50 (OSM) -> none."""
    net, juncs, pl, codes, _ = _t_junction(main_speed=50, minor_speed=None)
    out = _rule(net, juncs, pl, codes, {"osm": {"nodes": [], "areas": []}, "bdot10k": {}})
    assert len(out["advance"]) == 1 and out["advance"][0]["v_kmh"] == 90.0
    net, juncs, pl, codes, _ = _t_junction(main_speed=90, minor_speed=50)
    out = _rule(net, juncs, pl, codes, {"osm": {"nodes": [], "areas": []}, "bdot10k": {}})
    assert out["advance"] == []


# --------------------------------------------------------------------------------------------- consistency
def _straight(length=1500.0, kerbed=True):
    from roads import network
    ox, oy = ORIGIN
    attrs = {"highway": {"v": "secondary"}, "oneway": {"v": "no"}, "lanes": {"v": 2},
             "maxspeed": {"v": 50, "src": "default"}}
    g = {"nodes": [{"id": "a", "x": ox, "y": oy}, {"id": "b", "x": ox + length, "y": oy}],
         "edges": [{"id": "e", "from": "a", "to": "b", "geometry": [[ox, oy], [ox + length, oy]], "attrs": attrs}]}
    net = network.load(g, ORIGIN)
    for c in net.chains:
        k = len(c.line.s)
        c.z, c.e = np.zeros(k), np.zeros(k)
    foot = [LineString([(0, y), (length, y)]) for y in (-8.0, 8.0)] if kerbed else []
    network.assign_sides(net, foot, built_up=kerbed, walkways=foot)
    return net


def test_kerb_is_not_built_up_and_d42_pair_still_from_bdot():
    """D-42 / D-43 rule unchanged where BDOT says so; a kerbed road through fields is no longer a 'place'."""
    from streetscape import built_up as BU
    o = np.array(ORIGIN)
    net = _straight()
    c = net.chains[0]
    assert BU.kerbed(c, 700.0)
    z = BU.zone_for(net, {"osm": {"nodes": [], "areas": []}, "bdot10k": {}}, o)
    assert z.runs(c) == [(False, 0.0, c.length)] and z.speed(c, 700.0) == 90.0
    net = _straight()
    src = {"osm": {"nodes": [], "areas": []}, "bdot10k": {"OT_PTZB_A": [_houses(0, 500, 20, 60)]}}
    z = BU.zone_for(net, src, o)
    (b,) = BU.boundaries(net, z)
    assert b[1] == pytest.approx(500 + BU.ROADSIDE_M, abs=BU.STEP_M) and b[2] == -1
    assert z.at(net.chains[0], 200.0) and not z.at(net.chains[0], 1200.0)
    assert z.speed(net.chains[0], 200.0) == 50.0 and z.speed(net.chains[0], 1200.0) == 90.0


def test_industrial_inside_place_built_up_outskirts_not():
    """pkt 5.2.48.2: the boundary follows residential buildings, not industrial outskirts. Industrial land BETWEEN
    houses stays built-up (same place); industrial land at the end of the place is outside; an industrial estate on
    its own is no place."""
    from streetscape import built_up as BU
    o = np.array(ORIGIN)
    ind = "przemysłowo-składowa"
    net = _straight(2000.0, kerbed=False)
    c = net.chains[0]
    src = {"osm": {"nodes": [], "areas": []},
           "bdot10k": {"OT_PTZB_A": [_houses(0, 400, 20, 60), _houses(400, 900, 20, 60, ind),
                                     _houses(900, 1200, 20, 60), _houses(1200, 1700, 20, 60, ind)]}}
    z = BU.zone_for(net, src, o)
    assert z.at(c, 650.0)                                   # industrial between houses: inside the place
    assert not z.at(c, 1500.0)                              # industrial outskirts: outside
    (b,) = BU.boundaries(net, z)
    assert b[1] == pytest.approx(1200 + BU.ROADSIDE_M, abs=BU.STEP_M)
    net = _straight(2000.0, kerbed=False)
    src = {"osm": {"nodes": [], "areas": []}, "bdot10k": {"OT_PTZB_A": [_houses(400, 900, 20, 60, ind)]}}
    z = BU.zone_for(net, src, o)
    assert not z.at(net.chains[0], 650.0) and BU.boundaries(net, z) == []


def test_a8_follows_the_same_classification():
    """A-8 (Dz.U. 2026 poz. 132) asks the same Zone: a kerbed roundabout entry outside any place gets the A-8."""
    from streetscape import built_up as BU
    sec = NS(highway="tertiary", cls="Z", oneway=False, lanes=2, maxspeed=50.0, maxspeed_src="default")
    net = _straight()
    z = BU.zone_for(net, {"osm": {"nodes": [], "areas": []}, "bdot10k": {}}, np.array(ORIGIN))
    bu = z.at(net.chains[0], 700.0)
    assert bu is False and BU.needs_a8(bu, sec, has_e1=False)[0] is True
    assert BU.needs_a8(True, sec, has_e1=False)[0] is False


def test_zone_is_cached_and_shared():
    from streetscape import built_up as BU
    net = _straight()
    src = {"osm": {"nodes": [], "areas": []}, "bdot10k": {}}
    assert BU.zone_for(net, src, np.array(ORIGIN)) is BU.zone_for(net, src, np.array(ORIGIN))


def test_city_polygon_is_one_built_up_area():
    """A tile inside Białystok (built_up_places.json, OSM admin relation 1429268): the BDOT rule must not cut the city
    into places (forest / industrial land > 300 m) - no rule D-42 / D-43, 50 km/h, no A-7 + T-1."""
    from streetscape import built_up as BU
    o = np.array((777995.0, 596223.0))                      # origin of bialystok-industrial-c
    assert BU.places(o).contains(shapely.Point(0.0, 0.0))
    assert not BU.places(np.array(ORIGIN)).contains(shapely.Point(0.0, 0.0))     # Knyszyn: outside
    from roads import network
    attrs = {"highway": {"v": "secondary"}, "oneway": {"v": "no"}, "lanes": {"v": 2},
             "maxspeed": {"v": 50, "src": "default"}}
    g = {"nodes": [{"id": "a", "x": o[0], "y": o[1]}, {"id": "b", "x": o[0] + 1500.0, "y": o[1]}],
         "edges": [{"id": "e", "from": "a", "to": "b", "geometry": [[o[0], o[1]], [o[0] + 1500.0, o[1]]],
                    "attrs": attrs}]}
    net = network.load(g, tuple(o))
    for c in net.chains:
        k = len(c.line.s)
        c.z, c.e = np.zeros(k), np.zeros(k)
    network.assign_sides(net, [], built_up=False)
    src = {"osm": {"nodes": [], "areas": []}, "bdot10k": {"OT_PTZB_A": []}}
    z = BU.zone_for(net, src, o)
    c = net.chains[0]
    assert z.runs(c) == [(True, 0.0, c.length)] and z.speed(c, 700.0) == 50.0
    assert BU.boundaries(net, z) == []
