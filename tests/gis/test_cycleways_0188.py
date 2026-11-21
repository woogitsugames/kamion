"""ADR 0188: cycle tracks (DDR) from OSM as their own surface. Unit level: no world build needed."""

from __future__ import annotations

import numpy as np
import pytest
import shapely
from shapely.geometry import LineString

from roads import standards as S
from streetscape import cycleways as CY
from streetscape import paved as PV

SEG = {"highway": "path", "bicycle": "designated", "foot": "designated", "segregated": "yes", "surface": "paved"}


def _data(tags, coords, wid=1):
    return {"ways": [{"osm_way": wid, "part": 0, "tags": tags, "geometry": coords}]}


def test_classify_kinds_and_materials():
    assert CY.classify({"highway": "footway"}) is None
    assert CY.classify({"highway": "path", "bicycle": "yes"}) is None              # forest path, not designated
    d = CY.classify({"highway": "cycleway", "surface": "asphalt"})
    assert (d["kind"], d["mat_cycle"], d["mat_foot"], d["two_way"]) == ("ddr", "cycle_asphalt", None, True)
    assert CY.classify({"highway": "cycleway"})["mat_cycle"] == "cycle_asphalt"
    assert CY.classify({"highway": "cycleway", "surface": "asphalt", "colour": "red"})["mat_cycle"] == "cycle_asphalt_red"
    assert CY.classify({"highway": "cycleway", "surface": "asphalt", "colour": "grey"})["mat_cycle"] == "cycle_asphalt"
    assert CY.classify({"highway": "cycleway", "surface": "asphalt", "colour": "black"})["mat_cycle"] == "path_asphalt"
    assert CY.classify({"highway": "cycleway", "surface": "paving_stones"})["mat_cycle"] == "cycle_red"
    assert CY.classify({"highway": "cycleway", "surface": "dirt"})["mat_cycle"] is None
    assert CY.classify({"highway": "cycleway", "oneway": "yes"})["two_way"] is False
    s = CY.classify({**SEG, "cycleway:surface": "asphalt", "footway:surface": "paving_stones"})
    assert (s["kind"], s["mat_cycle"], s["mat_foot"]) == ("segregated", "cycle_asphalt", "sidewalk_paving")
    assert CY.classify({**SEG, "segregated": "no"})["kind"] == "shared"
    assert CY.classify({**SEG, "path": "crossing"})["crossing"] is True


def test_widths():
    assert CY.DDR_W_TWO_WAY == 2.6 and CY.SEG_TOTAL_DEFAULT == 4.6 and CY.SEG_TOTAL_MIN == 4.1
    ddr = CY.classify({"highway": "cycleway"})
    assert CY.widths(ddr, {}, None) == (CY.DDR_W_TWO_WAY, 0.0)
    assert CY.widths(CY.classify({"highway": "cycleway", "oneway": "yes"}), {}, None) == (CY.DDR_W_ONE_WAY, 0.0)
    assert CY.widths(ddr, {"width": "2.5 m"}, 3.0) == (2.5, 0.0)
    seg = CY.classify(SEG)
    assert CY.widths(seg, {}, 5.0) == (3.0, 2.0)                    # BDOT10k 5.0 m without per-way override
    assert CY.widths(seg, {}, 5.0, {"cycle_w_m": 2.6}) == (2.6, 2.4)  # Kuronia 212811563: M65 2.6 m DDR + 2.4 m footway
    cw, fw = CY.widths(seg, {}, 2.0)                                # BDOT 2.0 m for a segregated path: minimum total
    assert cw + fw == CY.SEG_TOTAL_MIN and cw >= CY.DDR_W_TWO_WAY and fw >= CY.SEG_FOOT_MIN
    assert CY.widths(seg, {}, None, {"total_w_m": 6.0, "cycle_w_m": 2.5}) == (2.5, 3.5)


def test_plan_side_strips_and_bdot_replacement():
    way = [[0.0, 0.0], [100.0, 0.0]]                                 # eastwards
    road = [LineString([(0, -12), (100, -12)])]                      # carriageway south = right of the way
    bdot = [{"id": "b1", "props": {"rodzaj": "aleja lub pasaż", "materialnawierzchni": "kostka prefabrykowana",
                                   "szerokosc": 5.0}, "geometry": {"coordinates": [[0, 1.0], [100, 1.0]]}},
            {"id": "b2", "props": {"rodzaj": "aleja lub pasaż", "materialnawierzchni": "kostka prefabrykowana",
                                   "szerokosc": 2.0}, "geometry": {"coordinates": [[0, 40.0], [100, 40.0]]}}]
    rep = {}
    it, = CY.plan(_data(SEG, way), (0, 0), [], bdot, road, rep)
    assert it["side"] == -1.0 and (it["w_cycle"], it["w_foot"]) == (3.0, 2.0)       # DDR on the road side by default
    assert rep["bdot_replaced"] == ["b1"] and rep["built"] == 1 and rep["overrides_stale"] == []
    cands = CY.candidates([it])
    cyc, foot = cands[0][1], cands[1][1]
    assert cands[0][2] == "cycle_asphalt" and cands[1][2] == "sidewalk_paving"
    assert cyc.area == pytest.approx(300.0, abs=0.5) and foot.area == pytest.approx(200.0, abs=0.5)
    assert cyc.intersection(foot).area < 1e-6
    assert cyc.centroid.y < foot.centroid.y                          # the DDR strip is the southern (road) one
    # authored override: the track is the half away from the road (photo P11-001)
    ov = [{"id": "x", "kind": "cycleway", "target": {"osm_way": [1]}, "cycle_side": "away", "colour": "red"},
          {"id": "gone", "kind": "cycleway", "target": {"osm_way": [999]}}]
    rep = {}
    it2, = CY.plan(_data(SEG, way), (0, 0), ov, bdot, road, rep)
    assert it2["side"] == 1.0 and it2["mat_cycle"] == "cycle_asphalt_red" and it2["provenance"] == "authored_override"
    assert rep["overrides_stale"] == ["gone"] and rep["overrides_applied"] == [1]
    c2 = CY.candidates([it2])
    assert c2[0][1].centroid.y > c2[1][1].centroid.y
    # M65 verified RED_ASPHALT_WAYS and AWAY_WAYS work automatically by OSM way ID
    it_putry, = CY.plan(_data(SEG, way, wid=591365139), (0, 0), [], [], road, {})
    assert it_putry["mat_cycle"] == "cycle_asphalt_red" and it_putry["side"] == 1.0 and it_putry["w_cycle"] == 3.3
    it_kuronia, = CY.plan(_data(SEG, way, wid=212811563), (0, 0), [], bdot, road, {})
    assert it_kuronia["mat_cycle"] == "cycle_asphalt" and it_kuronia["side"] == 1.0 and it_kuronia["w_cycle"] == 2.6
    # shared and unpaved ways are not built here
    rep = {}
    assert CY.plan(_data({**SEG, "segregated": "no"}, way), (0, 0), [], [], road, rep) == []
    assert rep["skipped"]["shared"] == 1


def test_ddr_width_only_from_bdot_cycle_line():
    way = [[0.0, 0.0], [100.0, 0.0]]
    bd = lambda rodz: [{"id": "b", "props": {"rodzaj": rodz, "materialnawierzchni": "masa bitumiczna", "szerokosc": 3.5},
                        "geometry": {"coordinates": [[0, 0.5], [100, 0.5]]}}]
    a, = CY.plan(_data({"highway": "cycleway"}, way), (0, 0), [], bd("aleja lub pasaż"), [], {})
    b, = CY.plan(_data({"highway": "cycleway"}, way), (0, 0), [], bd("droga dla rowerów"), [], {})
    assert a["w_cycle"] == CY.DDR_W_TWO_WAY and b["w_cycle"] == 3.5


def test_paved_collect_lays_cycle_strips_and_drops_replaced_bdot():
    way = [[0.0, 0.0], [100.0, 0.0]]
    bdot = [{"id": "b1", "props": {"rodzaj": "aleja lub pasaż", "materialnawierzchni": "kostka prefabrykowana",
                                   "szerokosc": 5.0}, "geometry": {"coordinates": [[0, 1.0], [100, 1.0]]}}]
    rep = {}
    items = CY.plan(_data(SEG, way), (0, 0), [], bdot, [LineString([(0, -12), (100, -12)])], rep)
    src = {"osm": {"areas": []}, "bdot10k": {"OT_PTPL_A": [], "OT_KUKO_A": [], "OT_SKRP_L": bdot}}
    road = shapely.box(40, -20, 47, 20)                               # a carriageway across the path
    prep = {}
    out = PV.collect(src, np.zeros(2), [], [], road, None, prep,
                     cycle={"cands": CY.candidates(items), "bdot_replaced": rep["bdot_replaced"]})
    mats = {}
    for p in out:
        mats[p["mat"]] = mats.get(p["mat"], 0.0) + p["poly"].area
        assert p["poly"].intersection(road).area < 0.5                # the road owns its surface
    assert set(mats) == {"cycle_asphalt", "sidewalk_paving"}          # no second (BDOT) footway beside the track
    assert mats["cycle_asphalt"] == pytest.approx(3.0 * 93, rel=0.03)
    assert mats["sidewalk_paving"] == pytest.approx(2.0 * 93, rel=0.03)
    assert "bdot10k_SKRP" not in prep and prep["osm_cycleway"][0] == 2
    assert "cycle_asphalt" in PV.EDGED and "cycle_asphalt_red" in PV.EDGED
    assert S.SURFACE_OF["cycle_asphalt"] == "asphalt" and S.SURFACE_OF["cycle_asphalt_red"] == "asphalt"


def test_p23_glyph_dimensions():
    for small, d in ((True, CY.P23_SMALL), (False, CY.P23)):
        g = CY.p23_glyph(small)
        x0, y0, x1, y1 = g.bounds
        assert g.is_valid and not g.is_empty
        assert x0 == pytest.approx(0.0, abs=0.01) and x1 == pytest.approx(d["len"], abs=0.03)
        assert y1 - y0 == pytest.approx(d["h"], abs=0.01)
        assert len(g.interiors if g.geom_type == "Polygon" else [i for p in g.geoms for i in p.interiors]) >= 2   # wheels
    assert (CY.P23["len"], CY.P23["h"], CY.P23["line"]) == (2.00, 1.10, 0.10)        # rys. 5.2.9.1
    assert S.P11_CLEAR_TWO_WAY == 3.0 and S.P11_CLEAR == 2.0


def test_region_files_and_materials():
    from roads import build_world as BW
    for rid in ("bialystok-industrial-c", "bialystok-dojlidy"):
        d = CY.load(rid)
        assert d and d["schema"] == CY.SCHEMA and len(d["ways"]) > 10
        assert all(CY.is_cycle(w["tags"]) for w in d["ways"])
    c_grey, red, xr, r_grey = (BW.MATERIALS[k] for k in ("cycle_asphalt", "cycle_asphalt_red", "cycle_crossing_red", "road_asphalt"))
    for m in (c_grey, red, xr):
        assert m["texture_set"] == "asphalt_tint" and m["uv"] == "planar" and m["rough"] >= 0.85    # no plastic
        r, g, b = m["color"]
        assert r > g >= b and r / max(b, 1e-6) < 1.8                  # weathered, not a saturated plastic red
        assert 1.2 < (0.2126 * r + 0.7152 * g + 0.0722 * b) / r_grey["color"][1] < 3.0     # render-calibrated
    # M65 §5 A: Dojlidy warm-grey DDR has low R/B (< 1.2); Rondo Putry red-brown DDR has higher R/B (> 1.4)
    assert c_grey["color"][0] / c_grey["color"][2] < 1.2
    assert red["color"][0] / red["color"][2] > 1.4
    assert xr.get("decal") is True and "decal" not in red and "decal" not in c_grey
    assert len(CY.P11_RED_NODES_DOJLIDY) == 9 and len(CY.P11_RED_NODES_C) == 16 and len(CY.P11_RED_NODES) == 25


def _flat_chain():
    from types import SimpleNamespace
    from roads.geom import Polyline
    from roads.network import Chain, DENSE

    s_pts = np.arange(0.0, 80.0 + 1e-6, DENSE)
    line = Polyline(np.column_stack([s_pts, np.zeros_like(s_pts)]))
    n = len(line.s)
    c = Chain(
        id="c0",
        node_a="a",
        node_b="b",
        edges=[(1, False)],
        raw=line.p.copy(),
        raw_spans=[(0.0, float(line.length), 1, False)],
        line=line,
        sec_idx=np.zeros(n, int),
        hw=np.full(n, 3.5),
        dirn=np.zeros(n, int),
        z=np.zeros(n),
        e=np.full(n, np.nan),
        t_a=6.0,
        t_b=6.0,
    )
    sec = SimpleNamespace(
        cls="Z",
        highway="tertiary",
        maxspeed=50,
        width=7.0,
        lanes=2,
        lanes_fwd=1,
        lanes_bwd=1,
        lane_w=3.5,
        edge_strip=0.0,
        oneway=False,
        roundabout=False,
        turn_fwd=[],
        turn_bwd=[],
        lane_edges=None,
    )
    return c, sec


def test_p11_drape_crossing_keeps_red_when_kerb_edges_step():
    from roads import markings as M
    from roads.meshing import MeshBuf

    c, _ = _flat_chain()
    buf = MeshBuf()
    red: list[bool] = []
    # Smooth asphalt inside |n| <= 3.38 m; raised kerb / off-plate beyond hw - 0.12
    top_of = lambda e, n: 0.0 if abs(n) <= 3.38 else float("nan")
    ok = M._drape_crossing(buf, c, s_c=5.5, hw=3.5, s0=8.0, s1=72.0, top_of=top_of,
                           kind="P-11", clear=3.0, red_out=red)
    assert ok is True
    assert red == [True]
    mats = {p.mat for p in buf.parts}
    assert "marking_white" in mats and "cycle_crossing_red" in mats


@pytest.mark.parametrize("kind", ["P-10", "P-11"])
def test_flared_crossing_keeps_inner_paint_when_outer_stripe_reaches_kerb(kind):
    """D94 Putry: the chain width reaches beyond the asphalt of a flared junction mouth."""
    from roads import markings as M
    from roads.meshing import MeshBuf

    c, _ = _flat_chain()
    buf = MeshBuf()
    top_of = lambda e, n: 0.0 if abs(n) <= 2.8 else float("nan")
    assert M._drape_crossing(buf, c, s_c=8.0, hw=3.5, s0=12.0, s1=72.0,
                             top_of=top_of, kind=kind, clear=3.0, red=False)
    assert len(buf.parts) >= 2
    assert all(np.abs(p.V[:, 1]).max() <= 2.8 for p in buf.parts)
    if kind == "P-11":
        assert {int(np.sign(p.V[:, 0].mean() - 8.0)) for p in buf.parts} == {-1, 1}


@pytest.mark.parametrize("kind", ["P-10", "P-11"])
def test_crossing_rejects_obstacle_between_valid_outer_stripes(kind):
    from roads import markings as M
    from roads.meshing import MeshBuf

    c, _ = _flat_chain()
    buf = MeshBuf()
    top_of = lambda e, n: float("nan") if abs(n) < 0.3 else 0.0
    assert not M._drape_crossing(buf, c, s_c=8.0, hw=3.5, s0=12.0, s1=72.0,
                                 top_of=top_of, kind=kind, clear=3.0, red=False)
    assert not buf.parts


def test_p11_crossing_clamps_to_ribbon_never_demotes_to_p10():
    from types import SimpleNamespace
    from roads import markings as M
    from roads.meshing import MeshBuf

    c, sec = _flat_chain()
    buf = MeshBuf()
    net = SimpleNamespace(
        chains=[c],
        sec_list=[sec],
        cycle_items=[{"kind": "ddr", "line": LineString([(4.0, -10.0), (4.0, 10.0)]), "two_way": True}],
    )
    ctx_points = [{"kind": "highway=crossing", "osm_node": 1001, "e": 4.0, "n": 0.0, "crossing": "uncontrolled"}]
    report: dict = {}
    M._build_markings(buf, net, juncs=[], ctx_points=ctx_points, report=report)

    counts = report.get("markings", {})
    assert counts.get("P-11 cycle crossing") == 1
    assert counts.get("P-11 red surfacing") == 1
    assert "P-10 crossing" not in counts
    srcs = [p.src for p in buf.parts]
    assert any(s.startswith("P-11@") for s in srcs)
    assert any(p.mat == "cycle_crossing_red" for p in buf.parts)
    assert not any(s.startswith("P-10") for s in srcs)


def test_p11_red_surfacing_only_on_m65_verified_nodes():
    from types import SimpleNamespace
    from roads import markings as M
    from roads.meshing import MeshBuf

    c, sec = _flat_chain()
    net = SimpleNamespace(
        chains=[c],
        sec_list=[sec],
        cycle_items=[
            {"kind": "ddr", "line": LineString([(20.0, -10.0), (20.0, 10.0)]), "two_way": True},
            {"kind": "ddr", "line": LineString([(40.0, -10.0), (40.0, 10.0)]), "two_way": True},
            {"kind": "ddr", "line": LineString([(60.0, -10.0), (60.0, 10.0)]), "two_way": True},
        ],
    )
    # 5825973689 = P11-056 (verified red); 2163381053 = P11-063 (white P-11 only); 4391371828 = none
    ctx_points = [
        {"kind": "highway=crossing", "osm_node": 5825973689, "e": 20.0, "n": 0.0, "crossing": "traffic_signals"},
        {"kind": "highway=crossing", "osm_node": 2163381053, "e": 40.0, "n": 0.0, "crossing": "traffic_signals"},
        {"kind": "highway=crossing", "osm_node": 4391371828, "e": 60.0, "n": 0.0, "crossing": "uncontrolled"},
    ]
    buf = MeshBuf()
    report: dict = {}
    M._build_markings(buf, net, juncs=[], ctx_points=ctx_points, report=report)

    counts = report.get("markings", {})
    assert counts.get("P-11 cycle crossing") == 2       # 5825973689 + 2163381053 (4391371828 skipped as none)
    assert counts.get("P-11 red surfacing") == 1        # ONLY 5825973689 gets cycle_crossing_red
    assert report.get("crossings_p11_red_nodes") == [5825973689]
    red_parts = [p for p in buf.parts if p.mat == "cycle_crossing_red"]
    assert len(red_parts) == 1
    assert np.all(red_parts[0].V[:, 0] < 30.0)          # red field only at x ≈ 20 m, none at x ≈ 40 m

