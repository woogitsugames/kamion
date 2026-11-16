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
