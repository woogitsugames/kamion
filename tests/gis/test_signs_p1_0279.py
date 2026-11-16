"""ADR 0279 "P1 - wdrożenie" (D25): fixes of the P1 findings of the sign audit, on synthetic data only (no Data/raw,
no region tiles). One block per audit point:
  (1) level-crossing devices >= 5 m from the outer rail (Dz.U. 2025 poz. 1105 § 77 ust. 2 pkt 1, § 54 ust. 1;
      Dz.U. 2019 poz. 2311 zał. 1 pkt 2.2.11),
  (2) P-14 2 m / 8 m before the signal head of a signalised approach (zał. 2 pkt 4.2.5),
  (3) P-12 with B-20 (zał. 1 pkt 3.2.21, zał. 2 pkt 4.2.3),
  (4) OSM traffic_sign=maxspeed, B-5, B-18 read (signs_route),
  (5) D-42 / D-43, A-7 + T-1 before the junction, A-8 before a roundabout."""

from __future__ import annotations

import math

import numpy as np
import pytest
import shapely
from shapely.geometry import LineString

from streetscape import rail as RL
from streetscape import rail_approach as RA


# ------------------------------------------------------------------------------------------------ (1) rail devices
def _plan(barrier=None, light=False, tracks=1, skew=0.0, road_w=7.0):
    tags = {"railway": "rail", **({"tracks": str(tracks)} if tracks > 1 else {})}
    ntags = {"railway": "level_crossing", **({"crossing:barrier": barrier} if barrier else {}),
             **({"crossing:light": "yes"} if light else {})}
    src = {"osm": {"ways": [{"osm_way": 10, "part": 0, "tags": tags, "coords": [[0.0, 500.0], [1000.0, 500.0]]}],
                   "nodes": [{"osm_node": 1, "tags": ntags, "xy": [500.0, 500.0]}]}}
    dx = 500.0 * math.tan(math.radians(skew))
    road = LineString([(500.0 - dx, 0.0), (500.0 + dx, 1000.0)])
    return RL.Plan(src, (0.0, 0.0), shapely.box(0, 0, 1000, 1000), road.buffer(road_w / 2, cap_style=2), [road])


def _flat(e, n):
    return np.full(np.shape(e), 100.0) + 0.0 * np.asarray(n)


def _outer_rail_n(p):
    """|n - 500| of the outer edge of the outer rail head of the east-west track."""
    t = p.tracks[0]
    return max(abs(r) for r in t.rail_lats()) + RL.RAIL_HEAD_W / 2


@pytest.mark.parametrize("skew", [0.0, 25.0, -40.0])
@pytest.mark.parametrize("tracks,barrier,light", [(1, None, False), (2, None, True), (1, "half", True),
                                                  (2, "double_half", True), (1, "full", True)])
def test_rail_devices_5m_from_outer_rail(skew, tracks, barrier, light):
    p = _plan(barrier=barrier, light=light, tracks=tracks, skew=skew)
    c = p.crossings[0]
    mk = p.markers(0, c, _flat)
    rail = _outer_rail_n(p)
    posts = [m for m in mk if m["kind"] in ("sign", "light", "bell")]
    assert posts
    for m in posts:
        # 1105 § 77 ust. 2 pkt 1 (signal) / 2311 zał. 1 pkt 2.2.11 (G-3 / G-4): perpendicular distance to the rail
        assert abs(m["n"] - 500.0) - rail >= RL.DEVICE_MIN_FROM_OUTER_RAIL_M - 1e-2, m
    for m in mk:
        if m["kind"] != "barrier":
            continue
        # 1105 § 54 ust. 1: every point of the boom >= 5 m from the outer track axis, measured along the road axis
        h = math.radians(m["heading_deg"])
        bdir = np.array([math.sin(h), math.cos(h)])
        axis = max(abs(o) for o in p.tracks[0].offsets)
        for t in (0.0, m["boom_len_m"]):
            q = np.array([m["e"], m["n"]]) + bdir * t
            assert (abs(q[1] - 500.0) - axis) / c["sin"] >= RL.BARRIER_MIN_FROM_TRACK_AXIS_M - 1e-2, (m, t)
    if barrier:
        # § 77 ust. 1: the signal stands directly before (upstream of) the barrier
        st = RL.device_stations(c)
        for a in (1, -1):
            assert st[(a, "R")] >= st[(a, "barrier")] + RL.SIGNAL_BEHIND_BARRIER_M - 1e-9


def test_rail_square_crossing_numbers():
    """Square single-track crossing without barriers: G-3 exactly 5 m from the rail (was ~3.6 m), P-14 of the
    approach 2.0 m before the device line (zał. 2 pkt 4.2.5), the A-10 rule keeps its 5 m clear of the devices."""
    p = _plan()
    c = p.crossings[0]
    sign = [m for m in p.markers(0, c, _flat) if m["kind"] == "sign"]
    rail = _outer_rail_n(p)
    assert {round(abs(m["n"] - 500.0) - rail, 2) for m in sign} == {5.0}
    old = c["half_track"] / c["sin"] + RL.SIGN_SETBACK - rail
    assert old == pytest.approx(3.55, abs=0.05)                 # audit: "gen. ≈ 3,6 m"
    assert RA.device_line_m(c) == pytest.approx(rail + 5.0)
    r = RA.rule(c, 90.0, 500.0)
    assert r["dist_m"] == 150.0                                 # A-10 150 m (unchanged, 2310 § 3 ust. 2)


# ------------------------------------------------------------------------------------------------ (2) + (3) markings
ORIGIN = (777995.0, 596223.0)


def _junction_net(main="secondary", main_lanes=2, minor="residential", four=False):
    """Synthetic T (or X) junction at the local origin: east-west main road, minor road to the south (and north)."""
    from roads import network
    ox, oy = ORIGIN
    nodes = [{"id": "n0", "x": ox, "y": oy}, {"id": "n1", "x": ox - 120.0, "y": oy},
             {"id": "n2", "x": ox + 120.0, "y": oy}, {"id": "n3", "x": ox, "y": oy - 120.0}]

    def edge(eid, a, b, pts, hw, lanes):
        return {"id": eid, "from": a, "to": b, "geometry": [[ox + px, oy + py] for px, py in pts],
                "attrs": {"highway": {"v": hw}, "oneway": {"v": "no"}, "lanes": {"v": lanes}}}
    edges = [edge("e1", "n0", "n1", [(0, 0), (-120, 0)], main, main_lanes),
             edge("e2", "n0", "n2", [(0, 0), (120, 0)], main, main_lanes),
             edge("e3", "n0", "n3", [(0, 0), (0, -120)], minor, 2)]
    if four:
        nodes.append({"id": "n4", "x": ox, "y": oy + 120.0})
        edges.append(edge("e4", "n0", "n4", [(0, 0), (0, 120)], minor, 2))
    return network.load({"nodes": nodes, "edges": edges}, ORIGIN)


def _mark(net, ctx):
    from roads.junctions import build_junctions
    from roads.markings import build_markings
    from roads.meshing import MeshBuf
    juncs = build_junctions(net, ctx)
    for c in net.chains:                                   # flat road (the profile stage is not needed here)
        n = len(c.line.s)
        c.z, c.e = np.zeros(n), np.zeros(n)
    buf = MeshBuf()
    rep = {}
    build_markings(buf, net, juncs, ctx, rep)
    return juncs, buf, rep


def _parts(buf, kind):
    return [p for p in buf.parts if p.layer == "markings" and p.src.startswith(kind + "@")]


def _arm_station(j, part):
    """(arm, smallest station from the junction centre of the part's vertices) - the junction-side edge."""
    best = None
    for a in j.arms:
        if part.src.split("@", 1)[1] != a.chain.id:
            continue
        s = np.array([a.chain.line.project(v)[0] for v in part.V[:, :2]])
        d = s if a.end == "a" else a.chain.length - s
        best = (a, float(d.min()))
    return best


def test_p12_with_b20_not_p13():
    """(3) highway=stop near the junction: B-20 on the minor approach (furniture) -> P-12 (zał. 1 pkt 3.2.21,
    zał. 2 pkt 4.2.3), one continuous 0.50 m line; without the stop node the same approach keeps P-13."""
    from roads import standards as S
    stop = [{"kind": "highway=stop", "e": 0.0, "n": -12.0, "osm_node": 7}]
    juncs, buf, rep = _mark(_junction_net(), stop)
    assert juncs[0].stop
    p12 = _parts(buf, "P-12")
    assert len(p12) == 1 and not _parts(buf, "P-13")
    v = p12[0].V
    depth = np.ptp(v[:, 1])                                 # minor road runs north-south: depth along n
    assert depth == pytest.approx(S.P12_W, abs=1e-6)
    assert np.ptp(v[:, 0]) > 2.0                            # across the inbound lane(s)
    juncs, buf, _ = _mark(_junction_net(), [])
    assert not juncs[0].stop and not _parts(buf, "P-12") and len(_parts(buf, "P-13")) >= 1


@pytest.mark.parametrize("main_lanes,overhead", [(2, False), (4, True)])
def test_p14_before_signal_2m_side_8m_overhead(main_lanes, overhead):
    """(2) zał. 2 pkt 4.2.5: P-14 >= 2.0 m before a signal beside the carriageway, >= 8.0 m before a signal over the
    carriageway (measured to the face of the head). Was trim + 0.6 m = at the foot of the mast (trim + 1.0)."""
    from roads import standards as S
    net = _junction_net(main="primary", main_lanes=main_lanes, four=True)
    sig = [{"kind": "highway=traffic_signals", "e": 0.0, "n": 0.0, "osm_node": 9}]
    juncs, buf, _ = _mark(net, sig)
    j = juncs[0]
    assert j.signalized
    p14 = _parts(buf, "P-14")
    assert p14
    seen = set()
    for p in p14:
        a, d = _arm_station(j, p)
        i = j.arms.index(a)
        post = j.trims[i] + S.SIGNAL_AFTER_TRIM
        sec = a.chain.section(float(a.s(post)), net.sec_list)
        ov = S.signal_overhead(sec, a.end)
        if a.cls(net.sec_list) == "GP" or a.cls(net.sec_list) == "G":
            assert ov is overhead
        need = post + (S.P14_BEFORE_OVERHEAD_SIGNAL if ov else S.SIGNAL_HEAD_FWD + S.P14_BEFORE_SIGNAL)
        assert d >= need - 0.05, (a.chain.id, d, need)
        seen.add((a.chain.id, ov))
    assert any(ov is overhead for _, ov in seen)


# ------------------------------------------------------------------------------------------------ (4) OSM tags
def test_parse_maxspeed_b5_b18_city_limit():
    from streetscape import signs as SG
    from streetscape.signs_route import parse_traffic_sign as P
    assert P("maxspeed", {"maxspeed": "40"}) == ["B-33_40"]                  # 17 nodes of the audit
    assert P("maxspeed", {}) == ["B-33"] and not SG.is_known("B-33")        # no value -> unknown, not invented
    assert P("PL:B-5") == ["B-5"] and SG.is_known("B-5")
    assert P("PL:B-18", {"maxweight": "10"}) == ["B-18_10"] and SG.is_known("B-18_10")
    assert P("PL:B-18[7.5]") == ["B-18_7.5"] and SG.is_known("B-18_7.5")
    assert P("PL:B-18", {}) == ["B-18"] and not SG.is_known("B-18")        # pkt 3.2.19: B-18 carries its number
    assert P("PL:B-33[50];PL:A-7") == ["B-33_50", "A-7"]                    # unchanged behaviour
    assert P("city_limit", {"name": "X"}) == ["D-42"] and P("PL:D-43") == ["D-43"]
    assert P("city_name") == []                                             # E-17a: not a built-up area sign
    for code in ("B-5", "B-18_10", "D-42", "D-43", "A-8", "T-1_150", "T-1S_160"):
        shape, im = SG.face(code)
        assert im.size[0] > 0
    assert SG.rect_size("D-42") == pytest.approx((1.2, 0.7))                # Z1 pkt 5.2.48.1
    assert SG.rect_size("T-1_150")[1] == pytest.approx(0.25)                # Tabela 9.7.1


def _osm_world(nodes, main="secondary"):
    from streetscape import furniture as FU
    from roads import network
    from roads.junctions import build_junctions
    net = _junction_net(main=main)
    for c in net.chains:
        n = len(c.line.s)
        c.z, c.e = np.zeros(n), np.zeros(n)
    juncs = build_junctions(net, [])
    network.assign_sides(net, [], built_up=True)
    src = {"osm": {"nodes": nodes, "areas": []}, "bdot10k": {}}
    pl = FU.Placer(lambda e, n: np.zeros(np.shape(e)))
    return net, juncs, src, pl


def _node(i, e, n, tags):
    return {"osm_node": i, "tags": tags, "geometry": {"type": "Point", "coordinates": [ORIGIN[0] + e, ORIGIN[1] + n]}}


def test_osm_signs_place_b33_b5_b18_and_report_missing_value():
    from streetscape import signs_route as SR
    nodes = [_node(1, -60.0, -4.0, {"traffic_sign": "maxspeed", "maxspeed": "40", "direction": "forward"}),
             _node(2, 60.0, -4.0, {"traffic_sign": "PL:B-5", "direction": "backward"}),
             _node(3, -90.0, 4.0, {"traffic_sign": "PL:B-18", "maxweight": "15", "direction": "backward"}),
             _node(4, 90.0, 4.0, {"traffic_sign": "PL:B-18", "direction": "forward"})]
    net, juncs, src, pl = _osm_world(nodes)
    rep, codes = {}, set()
    SR.osm_signs(pl, net, src, np.array(ORIGIN), juncs, rep, codes)
    placed = rep["osm_signs"]["placed"]
    assert placed == {"B-33_40": 1, "B-5": 1, "B-18_15": 1}
    assert rep["osm_signs"]["unknown"] == {"B-18": 1}
    assert rep["osm_signs"]["needs_value"] == [{"osm_node": 4, "code": "B-18", "tag": "maxweight"}]
    assert {"plate_B-33_40", "plate_B-5", "plate_B-18_15"} <= {it["p"] for it in pl.items}


# ------------------------------------------------------------------------------------------------ (5) new rules
def test_city_limit_gives_d42_and_d43_same_cross_section():
    from streetscape import signs_route as SR
    nodes = [_node(5, -80.0, -4.0, {"traffic_sign": "city_limit", "name": "X", "direction": "forward"})]
    net, juncs, src, pl = _osm_world(nodes)
    rep, codes = {}, set()
    SR.osm_signs(pl, net, src, np.array(ORIGIN), juncs, rep, codes)
    assert rep["osm_signs"]["placed"] == {"D-42": 1, "D-43": 1}
    posts = [it for it in pl.items if it["p"] == "sign_post"]
    assert len(posts) == 2
    a, b = posts                                         # same cross-section, opposite verges (pkt 5.2.49)
    assert abs(a["e"] - b["e"]) < 0.5 and abs(a["n"] - b["n"]) > 5.0
    assert abs(((a["yaw"] - b["yaw"]) % (2 * math.pi)) - math.pi) < 1e-3   # facing opposite directions


def _straight_net(length=1500.0, hw="secondary", maxspeed=None):
    from roads import network
    ox, oy = ORIGIN
    attrs = {"highway": {"v": hw}, "oneway": {"v": "no"}, "lanes": {"v": 2}}
    if maxspeed:
        attrs["maxspeed"] = {"v": maxspeed, "src": "osm"}
    g = {"nodes": [{"id": "a", "x": ox, "y": oy}, {"id": "b", "x": ox + length, "y": oy}],
         "edges": [{"id": "e", "from": "a", "to": "b", "geometry": [[ox, oy], [ox + length, oy]], "attrs": attrs}]}
    net = network.load(g, ORIGIN)
    for c in net.chains:
        n = len(c.line.s)
        c.z, c.e = np.zeros(n), np.zeros(n)
    network.assign_sides(net, [], built_up=False)            # kerbless rural edges (no "początek chodnika")
    return net


def _ptzb(x0, x1, rodzaj="jednorodzinna"):
    ox, oy = ORIGIN
    ring = [[ox + x0, oy + 20], [ox + x1, oy + 20], [ox + x1, oy + 60], [ox + x0, oy + 60], [ox + x0, oy + 20]]
    return {"geometry": {"type": "Polygon", "coordinates": [ring]}, "props": {"rodzaj": rodzaj}}


def test_built_up_rule_boundaries_and_300m_gap():
    """Houses 0-500 m and 1000-1500 m along a 1.5 km road: a 500 m gap (>= 300 m, pkt 5.2.48.1) gives D-43 + D-42 at
    both ends of the gap; a 200 m gap gives no pair; commercial land (pkt 5.2.48.2) is not built-up."""
    from streetscape import built_up as BU
    net = _straight_net()
    o = np.array(ORIGIN)
    a = BU.area({"bdot10k": {"OT_PTZB_A": [_ptzb(0, 500), _ptzb(1000, 1500)]}}, o)
    b = BU.boundaries(net, a)
    st = sorted(round(s) for _, s, _ in b)
    assert len(st) == 2
    assert st[0] == pytest.approx(500 + BU.ROADSIDE_M, abs=BU.STEP_M) and st[1] == pytest.approx(1000 - BU.ROADSIDE_M,
                                                                                               abs=BU.STEP_M)
    assert sorted(d for _, _, d in b) == [-1, 1]
    a2 = BU.area({"bdot10k": {"OT_PTZB_A": [_ptzb(0, 600), _ptzb(800, 1500)]}}, o)
    assert BU.boundaries(net, a2) == []                                       # gap 80 m after the buffer < 300 m
    a3 = BU.area({"bdot10k": {"OT_PTZB_A": [_ptzb(0, 500, "handlowo-usługowa")]}}, o)
    assert a3.is_empty


def test_built_up_rule_signs_placed_and_osm_wins():
    from streetscape import built_up as BU
    from streetscape import furniture as FU
    net = _straight_net()
    o = np.array(ORIGIN)
    src = {"bdot10k": {"OT_PTZB_A": [_ptzb(0, 500)]}, "osm": {"nodes": []}}
    pl, rep, codes = FU.Placer(lambda e, n: np.zeros(np.shape(e))), {}, set()
    BU.rule_signs(pl, net, src, o, [], rep, codes)
    assert rep["built_up"]["placed"] == {"D-42": 1, "D-43": 1} and len(rep["built_up"]["boundaries"]) == 1
    net = _straight_net()
    src["osm"]["nodes"] = [_node(9, 700.0, -4.0, {"traffic_sign": "city_limit", "direction": "backward"})]
    pl, rep, codes = FU.Placer(lambda e, n: np.zeros(np.shape(e))), {}, set()
    BU.rule_signs(pl, net, src, o, [], rep, codes)
    assert rep["built_up"]["placed"] == {} and rep["built_up"]["osm_boundary_nodes"] == 1


def test_legal_speed_and_a8_rule():
    """Art. 20 PoRD defaults; Dz.U. 2026 poz. 132 (pkt 2.2.9): A-8 unless E-1, or built-up and visible."""
    from types import SimpleNamespace as NS
    from streetscape import built_up as BU
    sec_def = NS(maxspeed=50.0, maxspeed_src="default")
    sec_osm = NS(maxspeed=70.0, maxspeed_src="osm")
    assert BU.legal_speed(sec_def, True) == 50.0 and BU.legal_speed(sec_def, False) == 90.0
    assert BU.legal_speed(sec_osm, True) == 70.0
    import shapely
    inside = shapely.box(-10, -10, 10, 10)
    assert BU.needs_a8((0, 0), sec_def, inside, has_e1=True)[0] is False
    assert BU.needs_a8((100, 0), sec_def, inside, has_e1=False)[0] is True       # outside the built-up area
    assert BU.needs_a8((0, 0), sec_def, inside, has_e1=False)[0] is False        # built-up, 50 km/h
    assert BU.needs_a8((0, 0), sec_osm, inside, has_e1=False)[0] is True         # built-up but 70 km/h
    assert BU.needs_a8((100, 0), sec_def, inside, has_e1=False, kerbed=True)[0] is False   # kerbed street = built-up
    assert BU.a8_distance_m(90.0) == 250.0 and BU.a8_distance_m(70.0) == 150.0 and BU.a8_distance_m(50.0) == 50.0


def test_a7_t1_advance_on_fast_minor_road():
    """pkt 2.2.8 (s. 64): A-7 on a minor road with v > 60 km/h preceded 150-300 m before by A-7 + T-1; B-20: A-7 +
    "Stop <m>" (pkt 3.2.21). Minor road 600 m long, OSM maxspeed 90; at 50 km/h nothing is added."""
    from roads import network
    from roads.junctions import build_junctions
    from streetscape import built_up as BU
    from streetscape import furniture as FU
    ox, oy = ORIGIN

    def net_with(minor_speed):
        def edge(eid, a, b, pts, hw, ms=None):
            at = {"highway": {"v": hw}, "oneway": {"v": "no"}, "lanes": {"v": 2}}
            if ms:
                at["maxspeed"] = {"v": ms, "src": "osm"}
            return {"id": eid, "from": a, "to": b, "geometry": [[ox + px, oy + py] for px, py in pts], "attrs": at}
        g = {"nodes": [{"id": "n0", "x": ox, "y": oy}, {"id": "n1", "x": ox - 300.0, "y": oy},
                       {"id": "n2", "x": ox + 300.0, "y": oy}, {"id": "n3", "x": ox, "y": oy - 600.0}],
             "edges": [edge("e1", "n0", "n1", [(0, 0), (-300, 0)], "primary", 90),
                       edge("e2", "n0", "n2", [(0, 0), (300, 0)], "primary", 90),
                       edge("e3", "n0", "n3", [(0, 0), (0, -600)], "tertiary", minor_speed)]}
        n = network.load(g, ORIGIN)
        for c in n.chains:
            k = len(c.line.s)
            c.z, c.e = np.zeros(k), np.zeros(k)
        return n

    def sides(n, juncs):
        network.assign_sides(n, [], built_up=False)

    for speed, stop, want in ((90, False, "T-1_"), (90, True, "T-1S_"), (50, False, None)):
        net = net_with(speed)
        ctx = [{"kind": "highway=stop", "e": 0.0, "n": -12.0, "osm_node": 7}] if stop else []
        juncs = build_junctions(net, ctx)
        sides(net, juncs)
        pl, rep, codes = FU.Placer(lambda e, n: np.zeros(np.shape(e))), {}, set()
        FU.junction_signs(pl, net, juncs, ctx, rep, codes)
        assert getattr(juncs[0], "minor_signs", None) == [(next(i for i, a in enumerate(juncs[0].arms)
                                                                 if a.chain.id.startswith("c:e3")), "B-20" if stop else "A-7")]
        out = {"placed": {}, "advance": [], "advance_dropped": []}
        BU.advance_signs(pl, net, juncs, shapely.Polygon(), out, codes)
        if want is None:
            assert out["advance"] == []
            continue
        (adv,) = out["advance"]
        assert adv["plate"].startswith(want) and 150.0 <= adv["d_m"] <= 300.0 + 20.0
        dist = int(adv["plate"].split("_")[1])
        assert dist % 10 == 0 and 150 <= dist <= 330
        assert out["placed"]["A-7"] == 1
