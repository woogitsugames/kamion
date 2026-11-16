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
