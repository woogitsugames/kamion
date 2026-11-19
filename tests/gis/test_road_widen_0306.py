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
    assert S.GAMEPLAY_LANE_WIDEN_M == 0.25


@pytest.fixture(scope="module")
def maczka():
    return _net("bialystok-maczka", 0.0), _net("bialystok-maczka", 0.25)


def test_every_lane_quarter_metre_wider(maczka):
    base, wide = maczka
    assert base.sections.keys() == wide.sections.keys()
    for k, a in base.sections.items():
        b = wide.sections[k]
        assert b.lanes == a.lanes
        assert b.width == pytest.approx(a.width + 0.25 * a.lanes, abs=1e-3), k
        assert b.lane_w == pytest.approx(a.lane_w + 0.25, abs=2e-3), k
        if a.oneway and not a.roundabout and not a.center_offset_profile:
            # one-way: grows to the right, the left (median) edge stays: centre moves right by half the growth
            sh = min(0.25 * a.lanes / 2, S.GROW_RIGHT_MAX_M)
            assert b.center_offset == pytest.approx(a.center_offset - sh, abs=2e-3), k
            assert (b.center_offset + b.width / 2) - (a.center_offset + a.width / 2) <= 0.25 * a.lanes / 2 + 2e-3
        else:
            assert b.center_offset == a.center_offset                 # two-way: symmetric, alignment kept
        assert b.provenance["gameplay_widen_m"] == pytest.approx(0.25 * a.lanes)


def test_measured_lane_edges_keep_left_strip_and_grow_per_lane(maczka):
    base, wide = maczka
    n = 0
    for k, a in base.sections.items():
        if not a.lane_edges:
            continue
        b = wide.sections[k]
        assert b.lane_edges[0] == a.lane_edges[0]
        for i in range(1, len(a.lane_edges)):
            assert b.lane_edges[i] - b.lane_edges[i - 1] == pytest.approx(a.lane_edges[i] - a.lane_edges[i - 1] + 0.25, abs=1e-3)
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


def test_knyszyn_compact_roundabout_truck_returns():
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


def test_knyszyn_widened_roundabout_builds_clean():
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
