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
    assert (d["kind"], d["mat_cycle"], d["mat_foot"], d["two_way"]) == ("ddr", "cycle_asphalt_red", None, True)
    assert CY.classify({"highway": "cycleway"})["mat_cycle"] == "cycle_asphalt_red"
    assert CY.classify({"highway": "cycleway", "surface": "asphalt", "colour": "grey"})["mat_cycle"] == "path_asphalt"
    assert CY.classify({"highway": "cycleway", "surface": "paving_stones"})["mat_cycle"] == "cycle_red"
    assert CY.classify({"highway": "cycleway", "surface": "dirt"})["mat_cycle"] is None
    assert CY.classify({"highway": "cycleway", "oneway": "yes"})["two_way"] is False
    s = CY.classify({**SEG, "cycleway:surface": "asphalt", "footway:surface": "paving_stones"})
    assert (s["kind"], s["mat_cycle"], s["mat_foot"]) == ("segregated", "cycle_asphalt_red", "sidewalk_paving")
    assert CY.classify({**SEG, "segregated": "no"})["kind"] == "shared"
    assert CY.classify({**SEG, "path": "crossing"})["crossing"] is True


def test_widths():
    ddr = CY.classify({"highway": "cycleway"})
    assert CY.widths(ddr, {}, None) == (CY.DDR_W_TWO_WAY, 0.0)
    assert CY.widths(CY.classify({"highway": "cycleway", "oneway": "yes"}), {}, None) == (CY.DDR_W_ONE_WAY, 0.0)
    assert CY.widths(ddr, {"width": "2.5 m"}, 3.0) == (2.5, 0.0)
    seg = CY.classify(SEG)
    assert CY.widths(seg, {}, 5.0) == (3.0, 2.0)                    # Kuronia: BDOT10k 5.0 m
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
    assert cands[0][2] == "cycle_asphalt_red" and cands[1][2] == "sidewalk_paving"
    assert cyc.area == pytest.approx(300.0, abs=0.5) and foot.area == pytest.approx(200.0, abs=0.5)
    assert cyc.intersection(foot).area < 1e-6
    assert cyc.centroid.y < foot.centroid.y                          # the DDR strip is the southern (road) one
    # authored override: the track is the half away from the road (photo P11-001)
    ov = [{"id": "x", "kind": "cycleway", "target": {"osm_way": [1]}, "cycle_side": "away"},
          {"id": "gone", "kind": "cycleway", "target": {"osm_way": [999]}}]
    rep = {}
    it2, = CY.plan(_data(SEG, way), (0, 0), ov, bdot, road, rep)
    assert it2["side"] == 1.0 and it2["provenance"] == "authored_override"
    assert rep["overrides_stale"] == ["gone"] and rep["overrides_applied"] == [1]
    c2 = CY.candidates([it2])
    assert c2[0][1].centroid.y > c2[1][1].centroid.y
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
    assert set(mats) == {"cycle_asphalt_red", "sidewalk_paving"}      # no second (BDOT) footway beside the track
    assert mats["cycle_asphalt_red"] == pytest.approx(3.0 * 93, rel=0.03)
    assert mats["sidewalk_paving"] == pytest.approx(2.0 * 93, rel=0.03)
    assert "bdot10k_SKRP" not in prep and prep["osm_cycleway"][0] == 2
    assert "cycle_asphalt_red" in PV.EDGED and S.SURFACE_OF["cycle_asphalt_red"] == "asphalt"


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
    red, xr, grey = (BW.MATERIALS[k] for k in ("cycle_asphalt_red", "cycle_crossing_red", "road_asphalt"))
    for m in (red, xr):
        assert m["texture_set"] == "asphalt_tint" and m["uv"] == "planar" and m["rough"] >= 0.85    # no plastic
        r, g, b = m["color"]
        assert r > g >= b and r / max(b, 1e-6) < 1.8                  # weathered red-brown, not a saturated red
        assert 1.2 < (0.2126 * r + 0.7152 * g + 0.0722 * b) / grey["color"][1] < 2.2
    assert xr.get("decal") is True and "decal" not in red
