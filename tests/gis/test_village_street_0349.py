"""ADR 0349: sidewalks at the kerb of DW671 through Krypno (dw671-tykocin-03 / -04), read off the orthophoto into
overrides.ortho_sidewalks.json (qa/ortho_sidewalks.py). Detector logic on synthetic profiles, the generated files in
git, the resulting side profiles of the network, the seam 03 | 04. Runs on the graphs and overrides in git, no Data/raw."""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))

from roads import network as Nw  # noqa: E402
from roads import pipeline  # noqa: E402
from roads import standards as S  # noqa: E402

from test_rural_xsec_0272 import _region_sides  # noqa: E402

spec = importlib.util.spec_from_file_location("ortho_sidewalks", REPO / "tools" / "worldgen" / "qa" / "ortho_sidewalks.py")
OS = importlib.util.module_from_spec(spec)
spec.loader.exec_module(OS)

T03, T04 = "dw671-tykocin-03", "dw671-tykocin-04"
SEAM_EDGE_02 = "w145989268:839431484-2133817368"      # 290 m from the seam with -02: no kerb seen, stays a ground shoulder
VILLAGE_WAYS = {1111506762, 1362040263, 1362040264, 145989268}
LEFT_M, RIGHT_M = 2.75, 2.0                           # docs/reports/village-street-0349/dw671-tykocin-03.json


# ------------------------------------------------------------------------------------------------ detector
def _profile(spans):
    """Synthetic station profile: spans = [(lat_from, lat_to, grey, saturation, green, r_minus_b)], rest = dark grass."""
    lat = np.arange(OS.HALF_M, -OS.HALF_M - 1e-6, -OS.CELL_M)
    gray, sat, green, warm = np.full(len(lat), 90.0), np.full(len(lat), 30.0), np.ones(len(lat)), np.full(len(lat), 5.0)
    for a, b, g, s, gr, w in spans:
        m = (lat >= a) & (lat <= b)
        gray[m], sat[m], green[m], warm[m] = g, s, gr, w
    return gray, sat, green, warm, lat


def test_paved_run_reaches_over_the_sidewalks_and_stops_at_grass():
    left, right, off, seen, core = OS.paved_extent(*_profile([(-5.5, 6.5, 160, 20, 0, 12), (-0.1, 0.1, 180, 20, 0, 12)]))
    assert (left, right) == (pytest.approx(6.5, abs=0.13), pytest.approx(5.5, abs=0.13))
    assert seen and off == pytest.approx(0.0, abs=0.13) and core == pytest.approx(160.0)


def test_beige_verge_and_dark_shadow_end_the_run():
    # sand / dry grass verge: bright and unsaturated enough, but R - B is far above the asphalt's
    left, right, *_ = OS.paved_extent(*_profile([(-3.5, 3.5, 160, 20, 0, 12), (3.5, 6.0, 170, 24, 0, 40)]))
    assert left == pytest.approx(3.5, abs=0.13) and right == pytest.approx(3.5, abs=0.13)
    left, right, *_ = OS.paved_extent(*_profile([(-3.5, 6.0, 160, 20, 0, 12), (3.5, 6.0, 100, 20, 0, 12)]))
    assert left == pytest.approx(3.375, abs=0.26)


def test_centre_line_is_the_lateral_origin():
    left, right, off, seen, _ = OS.paved_extent(*_profile([(-5.0, 7.0, 160, 20, 0, 12), (0.4, 0.6, 185, 20, 0, 12)]))
    assert seen and off == pytest.approx(0.5, abs=0.13)
    assert left + right == pytest.approx(12.0, abs=0.26) and left == pytest.approx(6.5, abs=0.26)


def _edge(eid, a, b, way, rows, cw=7.0, bu=True):
    st = [{"s": 10.0 * i, "left_m": le, "right_m": r, "valid": True, "built_up": bu, "core": 160.0} for i, (le, r) in enumerate(rows)]
    return {"edge": eid, "osm_way": way, "from": a, "to": b, "length_m": 10.0 * len(rows) + 20, "carriageway_m": cw,
            "width_src": "test", "stations": st, **OS.edge_summary(st, cw / 2)}


def _decide(edges):
    OS.pool_ways(edges)
    OS.fill_from_neighbours(edges)
    OS.even_runs(OS.runs_of(edges))
    return {e["edge"]: (e["left"]["sidewalk_w"], e["right"]["sidewalk_w"]) for e in edges}


def test_decision_needs_share_stations_and_built_up():
    yes = [(6.4, 5.65)] * 6
    d = _decide([_edge("a", "n1", "n2", 1, yes), _edge("b", "n5", "n6", 2, yes, bu=False),
                 _edge("c", "n7", "n8", 3, [(6.4, 3.6)] * 3 + [(3.6, 3.6)] * 3),
                 _edge("d", "n9", "n10", 4, [(4.6, 4.6)] * 6)])
    assert d["a"] == (2.75, 2.0)                       # extent - 3.5 m - 0.15 m kerb, rounded to 0.25 m
    assert d["b"] == (None, None)                      # outside the BDOT10k built-up area: a gravel shoulder, not a sidewalk
    assert d["c"] == (None, None)                      # 3 of 6 stations < SHARE
    assert d["d"] == (None, None)                      # 1.1 m beyond the carriageway < MIN_EXTRA_M: a shoulder


def test_short_edges_inherit_and_runs_get_one_width():
    long_a = _edge("a", "n1", "n2", 1, [(6.4, 5.65)] * 10)
    short_same_way = _edge("b", "n2", "n3", 1, [(6.4, 5.65)])
    short_other_way = _edge("c", "n3", "n4", 2, [])                 # no station of its own, no pool on its way
    long_d = _edge("d", "n4", "n5", 3, [(6.9, 5.65)] * 4)           # per-edge 3.0 / 2.0
    reversed_e = _edge("e", "n6", "n5", 3, [(5.65, 6.4)] * 5)       # runs against d: its left is d's right
    d = _decide([long_a, short_same_way, short_other_way, long_d, reversed_e])
    assert short_same_way["left"]["decided_by"] == "way" and short_other_way["left"]["decided_by"] == "neighbours"
    assert d["a"] == d["b"] == d["c"] == d["d"] == (2.75, 2.0)      # weighted median of the run, not 3.0 on d
    assert d["e"] == (2.0, 2.75) and long_d["left"]["sidewalk_edge_w"] == 3.0


def test_runs_cut_by_a_tile_seam_get_one_width():
    a = {"edges": [_edge("a", "n1", "Bx:0s", 7, [(6.4, 5.65)] * 10)]}
    b = {"edges": [_edge("b", "Bx:0n", "n9", 7, [(6.15, 5.65)] * 4)]}
    for rep in (a, b):
        _decide(rep["edges"])
    assert b["edges"][0]["left"]["sidewalk_w"] == 2.5
    OS.even_across_seams([a, b])
    assert a["edges"][0]["left"]["sidewalk_w"] == b["edges"][0]["left"]["sidewalk_w"] == 2.75


def test_override_entry_shape():
    rep = {"ortho": {"source_manifest": "m"}, "edges": [_edge("w1:1-2", "n1", "n2", 1, [(6.4, 3.6)] * 6)]}
    _decide(rep["edges"])
    (o,) = OS.overrides_of(rep)
    assert o["target"] == {"edge": "w1:1-2"} and o["id"] == "ortho-sidewalk-w1:1-2"
    assert o["set"] == {"side_left": "sidewalk", "sidewalk_w_left": 2.75, "shoulder_left": "kerb"}
    assert {"id", "target", "source", "reason", "confidence", "verify", "set"} <= set(o)


# ------------------------------------------------------------------------------------------------ files in git
def test_generated_file_is_registered_after_the_other_generated_files():
    assert pipeline.GENERATED_OVERRIDES[-1] == OS.OUT_NAME == "overrides.ortho_sidewalks.json"


@pytest.mark.parametrize("region_id,n", [(T03, 15), (T04, 2)])
def test_generated_entries_target_graph_edges(region_id, n):
    rdir = pipeline.REGIONS / region_id
    gen = json.loads((rdir / OS.OUT_NAME).read_text(encoding="utf-8"))
    assert gen["schema"] == OS.SCHEMA and len(gen["overrides"]) == n
    edges = {e["id"]: e for e in json.loads((rdir / "roads.graph.json").read_text(encoding="utf-8"))["edges"]}
    assert len({o["id"] for o in gen["overrides"]}) == n
    for o in gen["overrides"]:
        e = edges[o["target"]["edge"]]
        assert e["osm_way"] in VILLAGE_WAYS and e["attrs"]["ref"]["v"] == "671"
        assert o["set"] == {"side_left": "sidewalk", "sidewalk_w_left": LEFT_M, "shoulder_left": "kerb",
                            "side_right": "sidewalk", "sidewalk_w_right": RIGHT_M, "shoulder_right": "kerb"}
    assert pipeline.generated_overrides(region_id)[-n:] == gen["overrides"]
    rep = json.loads((REPO / "docs" / "reports" / "village-street-0349" / f"{region_id}.json").read_text(encoding="utf-8"))
    assert OS.overrides_of(rep) == gen["overrides"]                 # the report in git reproduces the file


def test_no_generated_sidewalks_on_the_open_road_tiles():
    for rid in ("dw671-tykocin-01", "dw671-tykocin-02", "dw671-tykocin-05", "dw671-tykocin-06", "dw671-tykocin-07",
                "dw671-tykocin-08", "dw671-tykocin-09"):
        assert not (pipeline.REGIONS / rid / OS.OUT_NAME).exists(), rid
        rep = json.loads((REPO / "docs" / "reports" / "village-street-0349" / f"{rid}.json").read_text(encoding="utf-8"))
        assert OS.overrides_of(rep) == [], rid


def test_edge_target_takes_a_list_and_goes_stale_as_a_whole():
    ov = yaml.safe_load((pipeline.REGIONS / T03 / "overrides.yaml").read_text(encoding="utf-8"))["overrides"]
    village = next(o for o in ov if o["id"] == "dw671-village-kerb")
    assert isinstance(village["target"]["edge"], list) and SEAM_EDGE_02 not in village["target"]["edge"]
    graph = json.loads((pipeline.REGIONS / T03 / "roads.graph.json").read_text(encoding="utf-8"))
    origin = (757515.0, 608511.0)
    net = Nw.load(graph, origin, [village])
    assert net.overrides_stale == [] and net.overrides_applied[0]["targets"] == sorted(village["target"]["edge"])
    bad = {**village, "target": {"edge": village["target"]["edge"] + ["w1:1-2"]}}
    net = Nw.load(graph, origin, [bad])
    assert net.overrides_stale == ["dw671-village-kerb"] and net.overrides_applied == []
    from roads import closures
    assert closures.target_edge_ids(village, graph["edges"]) == sorted(village["target"]["edge"])
    assert closures.target_edge_ids(bad, graph["edges"]) == []


# ------------------------------------------------------------------------------------------------ network
@pytest.fixture(scope="module")
def net03():
    return _region_sides(T03)


@pytest.fixture(scope="module")
def net04():
    return _region_sides(T04)


def _dw671(net):
    for c in net.chains:
        if c.roundabout:
            continue
        for i in range(len(c.line.s)):
            sec = net.sec_list[int(c.sec_idx[i])]
            if sec.ref == "671" and not c.bridge[i]:
                yield c, i, sec


def _side_w(c, i, sec, osm_side):
    """(kind, kerb height, sidewalk width, mat) of the OSM-direction side of a station."""
    rev = bool(c.meta["rev"][i])
    sd = {"left": "L", "right": "R"}[osm_side if not rev else {"left": "right", "right": "left"}[osm_side]]
    d = c.side[sd]
    return int(d["kind"][i]), float(d["raw"]["h"][i]), float(d["raw"]["w"][i]), int(d["mat"][i])


def test_village_street_has_kerb_and_sidewalk_on_both_sides(net03):
    n = ok = 0
    for c, i, sec in _dw671(net03):
        if sec.edge_id == SEAM_EDGE_02:
            continue
        s = float(c.line.s[i])
        if s < c.t_a + 2.0 or s > c.length - c.t_b - 2.0:           # inside a junction patch
            continue
        n += 1
        le, ri = _side_w(c, i, sec, "left"), _side_w(c, i, sec, "right")
        ok += (le == (Nw.URBAN, S.KERB_HEIGHT, LEFT_M, 1)) and (ri == (Nw.URBAN, S.KERB_HEIGHT, RIGHT_M, 1))
        assert sec.edge_lines in (None, "none"), sec.edge_id       # no edge line beside a kerb
    assert n > 3000 and ok / n > 0.97, (n, ok)                     # ~1.6 km of street at 0.5 m stations (3197)


def test_carriageway_width_is_bdot_plus_the_gameplay_widening_only(net03):
    """BDOT10k 7.0 m (orthophoto: 7.2 m +- 0.3 between the kerbs) + D94 2 x 0.25 m: nothing else widens the street."""
    for c, i, sec in _dw671(net03):
        assert sec.width == pytest.approx(7.0 + sec.lanes * S.GAMEPLAY_LANE_WIDEN_M)
        assert sec.lanes == 2 and sec.provenance.get("gameplay_widen_limited_m", 0.0) == 0.0
    hw = np.array([float(c.hw[i]) for c, i, _ in _dw671(net03)])
    assert np.median(hw) == pytest.approx(3.5 + S.GAMEPLAY_LANE_WIDEN_M) and (hw <= 3.5 + S.GAMEPLAY_LANE_WIDEN_M + 0.01).mean() > 0.9


def test_stretch_from_the_02_seam_keeps_its_ground_shoulder(net03):
    n = rural = 0
    for c, i, sec in _dw671(net03):
        if sec.edge_id != SEAM_EDGE_02:
            continue
        assert sec.provenance["shoulder"] == "authored_override:dw671-ground-shoulder" and sec.edge_lines == "both"
        for sd in "LR":
            n += 1
            rural += int(c.side[sd]["kind"][i]) == Nw.RURAL
    assert n > 1000 and rural / n > 0.9, (n, rural)


def test_sidewalks_continue_across_the_seam_03_04(net03, net04):
    def at_seam(net):
        for c in net.chains:
            for node, i in ((c.node_a, 0), (c.node_b, len(c.line.s) - 1)):
                sec = net.sec_list[int(c.sec_idx[i])]
                if net.nodes[node]["boundary"] and sec.ref == "671" and abs(c.line.p[i][0] - 38.0) < 5.0:
                    return c, i, sec
        raise AssertionError("no DW671 chain end on the seam")
    c3, i3, s3 = at_seam(net03)
    c4, i4, s4 = at_seam(net04)
    assert float(c3.hw[i3]) == pytest.approx(float(c4.hw[i4]))
    for osm_side, w in (("left", LEFT_M), ("right", RIGHT_M)):
        assert _side_w(c3, i3, s3, osm_side) == _side_w(c4, i4, s4, osm_side) == (Nw.URBAN, S.KERB_HEIGHT, w, 1)


def test_open_road_of_tile_04_is_unchanged(net04):
    """Way 244403510 (fields south of Krypno Wielkie): paved run 6.6-7.1 m on the orthophoto = the carriageway alone."""
    n = walk = 0
    for c, i, sec in _dw671(net04):
        if sec.edge_id.startswith("w244403510:"):
            n += 2
            walk += sum(float(c.side[sd]["raw"]["w"][i]) > 0.05 and int(c.side[sd]["mat"][i]) == 1 for sd in "LR")
    assert n > 5000 and walk == 0, (n, walk)
