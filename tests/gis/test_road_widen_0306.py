"""D94 / ADR 0306: roads wider than measured for playability (GAMEPLAY_WIDEN) - +0.25 m per lane on top of the measured
base, curve widening of two-way lanes for the semitrailer off-tracking, truck kerb returns at compact roundabouts, and
the combination lane check (tools/worldgen/qa/combo_lane_check.py)."""
import math
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "worldgen"))
sys.path.insert(0, str(ROOT / "tools" / "worldgen" / "qa"))

from roads import network as N  # noqa: E402
from roads import pipeline  # noqa: E402
from roads import standards as S  # noqa: E402
from roads import compact_roundabout as CR  # noqa: E402
from roads.swept_path import steady_state  # noqa: E402


def _net(region, widen):
    old = S.GAMEPLAY_LANE_WIDEN_M
    S.GAMEPLAY_LANE_WIDEN_M = widen
    try:
        return pipeline.build_network(region)[0]
    finally:
        S.GAMEPLAY_LANE_WIDEN_M = old


def test_widen_is_one_global_gameplay_value():
    assert S.GAMEPLAY_LANE_WIDEN_DEFAULT_M == 0.25      # (tests/gis/conftest.py runs the GIS suite at 0 = measured)


@pytest.fixture(scope="module")
def maczka():
    return _net("bialystok-maczka", 0.0), _net("bialystok-maczka", 0.25)


def test_every_lane_quarter_metre_wider(maczka):
    base, wide = maczka
    assert base.sections.keys() == wide.sections.keys()
    for k, a in base.sections.items():
        b = wide.sections[k]
        assert b.lanes == a.lanes
        limited = float(b.provenance.get("gameplay_widen_limited_m", 0.0))
        dl = 0.25 - limited / a.lanes
        assert b.width == pytest.approx(a.width + dl * a.lanes, abs=1e-3), k
        assert b.lane_w == pytest.approx(a.lane_w + dl, abs=2e-3), k
        assert b.lane_w >= a.lane_w - 1e-9
        if not a.roundabout:
            shift = b.center_offset - a.center_offset
            left, right = b.provenance["gameplay_clearance_m"]
            growth = dl * a.lanes
            assert abs(shift) <= growth / 2 + .002
            if left is not None:
                assert growth / 2 + shift <= left + .002
            if right is not None:
                assert growth / 2 - shift <= right + .002
        else:
            assert b.center_offset == a.center_offset
        assert b.provenance["gameplay_widen_m"] == pytest.approx(dl * a.lanes, abs=0.01)


def test_measured_lane_edges_keep_left_strip_and_grow_per_lane(maczka):
    base, wide = maczka
    n = 0
    for k, a in base.sections.items():
        if not a.lane_edges:
            continue
        b = wide.sections[k]
        assert b.lane_edges[0] == a.lane_edges[0]
        for i in range(1, len(a.lane_edges)):
            assert b.lane_edges[i] - b.lane_edges[i - 1] == pytest.approx(a.lane_edges[i] - a.lane_edges[i - 1] + (b.width - a.width) / a.lanes, abs=1e-3)
        n += 1
    assert n >= 5                          # ADR 0301 orthophoto lanes on Maczka


def test_widen_is_idempotent():
    net = _net("bialystok-maczka", 0.25)
    before = {k: s.width for k, s in net.sections.items()}
    N.gameplay_widen(net, 0.25)
    assert {k: s.width for k, s in net.sections.items()} == before


@pytest.mark.parametrize("R", [25.0, 40.0, 80.0, 150.0])
def test_offtrack_matches_swept_path_closed_form(R):
    ss = steady_state(math.sqrt(R * R - 3.70 ** 2))
    assert N.offtrack_ss(R) == pytest.approx(R - ss["R2"], abs=1e-6)
    assert N.offtrack_ss(R) == pytest.approx(40.0 / R, rel=0.12) if R >= 40 else True


def test_curve_widening_on_tight_two_way_bends_only():
    net = _net("tykocin", 0.25)
    wid = [c for c in net.chains if "curve_widen_max_m" in c.meta]
    assert wid, "Tykocin has two-way G / Z bends tighter than 200 m"
    for c in wid:
        assert 0.0 < c.meta["curve_widen_max_m"] <= S.CURVE_WIDEN_MAX_M + 1e-9
        for i in np.unique(c.sec_idx):
            sec = net.sec_list[int(i)]
            if sec.provenance.get("curve_widen"):
                assert not sec.oneway and sec.lanes == 2 and sec.cls in ("GP", "G", "Z") and sec.lane_follow
        for node, s_end in ((c.node_a, 0.0), (c.node_b, c.length)):
            if net.nodes[node].get("boundary"):
                m = np.abs(c.line.s - s_end) < 0.5 * S.CURVE_WIDEN_SEAM_SKIP_M
                base = np.array([net.sec_list[int(i)].width / 2 for i in c.sec_idx])
                assert np.all(c.hw[m] <= base[m] + 0.05), c.id        # nothing added at a tile seam


def test_knyszyn_compact_roundabout_truck_returns(monkeypatch):
    monkeypatch.setattr(S, "GAMEPLAY_LANE_WIDEN_M", 0.25)
    net = _net("knyszyn", 0.25)
    (spec,) = CR.specs(net)
    assert spec.opts["entry_r_m"] >= CR.TRUCK_ENTRY_R_MIN_M
    assert spec.opts["exit_r_m"] >= CR.TRUCK_EXIT_R_MIN_M
    assert spec.opts["lane_w_m"] == pytest.approx(4.0 + 0.25)          # authored 4.0 m + GAMEPLAY_WIDEN
    assert spec.w_ring == pytest.approx(5.0 + 0.25, abs=0.02)            # authored ring 5.0 m + one lane


def test_corridor_pieces_follow_the_links():
    import json
    import combo_lane_check as CL
    d = json.loads(CL.LS.LINKS.read_text(encoding="utf-8"))
    cor = next(c for c in d["corridors"] if c["id"] == "bialystok-tykocin")
    pieces = {t: k for t, k, _L in CL.corridor_pieces(cor, d["links"])}
    assert pieces["knyszyn"] == "link:knyszyn-dk65-to-dw671-w"
    assert pieces["knyszyn-w"] == "link:knyszyn-w-dw671"               # start_epsg2180 link replaces the route
    assert pieces["bialystok-industrial-c"] == "route+link:c-dk8-to-maczka"
    assert pieces["dk65-05"] == "route"


def test_knyszyn_widened_roundabout_builds_clean(monkeypatch):
    monkeypatch.setattr(S, "GAMEPLAY_LANE_WIDEN_M", 0.25)
    """The D94 roundabout (returns 12 / 15 m, corners TRUCK_CORNER_R_M) keeps 4 splitters, 4 crossings, 4 P-13 and no notes."""
    import json
    from roads import junctions as J
    from roads import markings as MK  # noqa: F401
    rid = "knyszyn"
    region = pipeline.load_region(rid)
    origin = (region["origin"]["x"], region["origin"]["y"])
    ctx = json.loads((pipeline.REGIONS / rid / "generated" / "osm_context.json").read_text(encoding="utf-8"))
    net = _net(rid, 0.25)
    pts, foot = pipeline.ctx_local(ctx, origin)
    N.assign_sides(net, foot, built_up=True, walkways=[], yards=None)
    j = next(j for j in J.build_junctions(net, pts) if j.compact is not None)
    sp = j.compact
    rep = CR.report_one(sp)
    assert rep["notes"] == [] and len(rep["rules"]) == 2, rep
    assert rep["splitters"] >= 4 and len(sp.crossings) == 4 and len(sp.p13) == 4     # 7 at GAMEPLAY 0 (refuges cut)
    assert rep["ring_asphalt_m"] == pytest.approx(5.25, abs=0.05)


@pytest.mark.parametrize("neighbour_y,expected_shift", [(9.0, -0.25), (-9.0, 0.25)])
@pytest.mark.parametrize("other_oneway", [True, False])
def test_grows_away_from_parallel_road_on_either_side(neighbour_y, expected_shift, other_oneway):
    from dataclasses import replace
    from types import SimpleNamespace
    sec = N.EdgeSection("w1:a-b", "primary", "G", True, 2, 2, 0, 3.0, .25, 6.5,
                        "measured", "road_asphalt", False, 0, False, None, None, None)
    other = replace(sec, edge_id="w2:c-d", oneway=other_oneway, lanes_fwd=2 if other_oneway else 1,
                    lanes_bwd=0 if other_oneway else 1, provenance={})
    net = SimpleNamespace(sections={sec.edge_id: sec, other.edge_id: other})
    edges = {sec.edge_id: ({}, np.array([[0., 0.], [100., 0.]]), "a", "b"),
             other.edge_id: ({}, np.array([[0., neighbour_y], [100., neighbour_y]]), "c", "d")}
    N.gameplay_widen(net, .25, edges)
    assert sec.width == 7.0
    assert sec.center_offset == expected_shift
    # Both carriageways move away: the original 2.5 m separator survives.
    assert abs(neighbour_y + other.center_offset - sec.center_offset) - (sec.width + other.width) / 2 == pytest.approx(2.5)


def test_no_space_between_parallel_roads_limits_growth_and_keeps_other_level_out():
    from dataclasses import replace
    from types import SimpleNamespace
    sec = N.EdgeSection("w1:a-b", "primary", "G", True, 2, 2, 0, 3.0, .25, 6.5,
                        "measured", "road_asphalt", False, 0, False, None, None, None)
    secs = [sec, replace(sec, edge_id="w2:c-d", provenance={}), replace(sec, edge_id="w3:e-f", provenance={})]
    net = SimpleNamespace(sections={s.edge_id: s for s in secs})
    edges = {s.edge_id: ({}, np.array([[0., y], [100., y]]), str(i), str(i + 10))
             for i, (s, y) in enumerate(zip(secs, [0., 9., -9.]))}
    N.gameplay_widen(net, .25, edges)
    assert sec.width == 6.5 and sec.center_offset == 0
    assert sec.provenance["gameplay_widen_limited_m"] == .5
    secs[1].layer = secs[2].layer = 1
    assert N.widening_clearance(net, edges)[sec.edge_id] == [float("inf"), float("inf")]


def test_parking_loop_is_not_absorbed_past_its_first_bend():
    from roads import junctions as J
    from shapely.geometry import Polygon, Point
    net = _net("bialystok-industrial-c", .25)
    junction = next(j for j in J.build_junctions(net, []) if "n4103450295" in j.nodes)
    assert max(junction.trims.values()) < 20.0
    # Previously a separator kerb crossed this actual through-lane at the parking entrance.
    polygon = Polygon([p for p, tag in junction.boundary])
    assert polygon.is_valid
    assert polygon.contains(Point(-208.01, -287.49).buffer(.3))


def test_neighbours_share_the_surplus_instead_of_spending_it_twice():
    from dataclasses import replace
    from types import SimpleNamespace
    sec = N.EdgeSection("w1:a-b", "primary", "G", True, 2, 2, 0, 3.0, .25, 6.5,
                        "measured", "road_asphalt", False, 0, False, None, None, None)
    secs = [replace(sec, edge_id=f"w{i}:a-b", provenance={}) for i in range(4)]
    net = SimpleNamespace(sections={s.edge_id: s for s in secs})
    edges = {s.edge_id: ({}, np.array([[0., y], [100., y]]), str(i), str(i + 10))
             for i, (s, y) in enumerate(zip(secs, [-9., 0., 18.75, 27.75]))}
    N.gameplay_widen(net, .25, edges)
    a,b = secs[1:3]
    gap = 18.75 + b.center_offset - a.center_offset - (a.width + b.width) / 2
    assert gap >= S.WIDEN_SEPARATOR_RESERVE_M - .002
    assert a.provenance["gameplay_widen_limited_m"] > 0
    assert b.provenance["gameplay_widen_limited_m"] > 0


def test_clearance_uses_local_profile_width_instead_of_maximum():
    from dataclasses import replace
    from types import SimpleNamespace
    sec = N.EdgeSection("w1:a-b", "primary", "G", True, 2, 2, 0, 3.0, .25, 14.0,
                        "measured", "road_asphalt", False, 0, False, None, None, None,
                        width_profile=[(0,14),(.1,6.5),(.9,6.5),(1,14)])
    other = replace(sec, edge_id="w2:c-d", width=6.5, width_profile=None, provenance={})
    net = SimpleNamespace(sections={sec.edge_id:sec,other.edge_id:other})
    edges = {sec.edge_id: ({}, np.array([[0.,0.],[100.,0.]]), "a", "b"),
             other.edge_id: ({}, np.array([[20.,22.],[80.,22.]]), "c", "d")}
    assert N.widening_clearance(net, edges)[sec.edge_id][0] == pytest.approx(1.75)
