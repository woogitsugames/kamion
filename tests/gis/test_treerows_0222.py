"""ADR 0222: roadside tree rows (szpalery) along DK65 / the approach roads of Knyszyn.

Synthetic: a straight major road with a side road (junction) and a field access (track) -> no trunk in a sight field,
every trunk >= the legal set-back from the carriageway edge, the rhythm of the data, deterministic layout, opt-in.
Region data from git (streetscape_sources.json, roads.graph.json, tree_rows.yaml, tree_rows_osm.json): counts per
tile in range, no trunk on a carriageway, seams without duplicate trunks. No Data/raw, no build_world.
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import yaml
from shapely.geometry import LineString

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))

from roads import pipeline                   # noqa: E402
from streetscape import tree_rows as TR      # noqa: E402
from streetscape import vegetation as VG     # noqa: E402

TILES = [f"dk65-{i:02d}" for i in range(1, 12)] + ["knyszyn", "knyszyn-s", "knyszyn-w"]


def _edge(eid, a, b, geom, hw="secondary", width=7.0, v=90, way=1):
    return {"id": eid, "from": a, "to": b, "geometry": geom, "osm_way": way,
            "attrs": {"highway": {"v": hw}, "width": {"v": width}, "maxspeed": {"v": v}}}


def _scene():
    """Major road E-W through (0,0) (two edges), a side road to the north at x = 0, a field track to the south at
    x = 250; two row lines 7 m north and 7 m south of the road axis (3.5 m to the edge + 3.5 m)."""
    graph = {"edges": [_edge("w", "A", "J", [[-600.0, 0.0], [0.0, 0.0]]),
                       _edge("e", "J", "B", [[0.0, 0.0], [600.0, 0.0]]),
                       _edge("n", "J", "C", [[0.0, 0.0], [0.0, 300.0]], hw="residential", width=5.0, v=50, way=2)]}
    roads = TR.roads_from_graph(graph, (0.0, 0.0))
    track = LineString([(250.0, -4.0), (250.0, -200.0)])
    lines = [("bdot:N", LineString([(-500.0, 7.0), (500.0, 7.0)]), "bdot"),
             ("bdot:S", LineString([(-500.0, -7.0), (500.0, -7.0)]), "bdot")]
    return graph, roads, track, lines


def _all(res):
    P = [r["P"] for r in res["rows"] if len(r["P"])]
    return np.vstack(P) if P else np.zeros((0, 2))


def test_legal_constants_quoted():
    # Dz.U. 2016 poz. 124 § 53 ust. 3 and zał. 3 ust. 5 (text checked 2026-11-15, ADR 0222)
    assert TR.MIN_TRUNK_EDGE_M == 3.0 and TR.SIGHT_OBS_M == 3.0
    assert TR.SIGHT_L2 == {30: 40, 40: 60, 50: 70, 60: 90, 70: 100, 80: 120, 90: 160, 100: 180}
    assert TR.SIGHT_L1 == {30: 60, 40: 80, 50: 100, 60: 120, 70: 140, 80: 160, 90: 180, 100: 210}
    assert TR._table(TR.SIGHT_L2, 90) == 160 and TR._table(TR.SIGHT_L2, 85) == 160 and TR._table(TR.SIGHT_L2, 120) == 180


def test_no_trunk_in_sight_fields_and_set_back():
    graph, roads, track, lines = _scene()
    res = TR.plan(lines, roads, {"missing_share": 0.0}, tracks=[track], graph=graph)
    P = _all(res)
    rep = res["report"]
    assert rep["junctions"] == 1 and rep["accesses"] == 1          # track: both ends tested, only the road end counts
    assert rep["cut_sight"] > 0 and len(P) > 60
    import shapely
    sight = shapely.union_all(res["cuts"])
    assert not shapely.contains_xy(sight, P[:, 0], P[:, 1]).any()
    d, _ = TR.edge_distance(roads, P)
    assert d.min() >= TR.MIN_TRUNK_EDGE_M - 1e-6
    # the start-from-stop field of the side road reaches L2(90) = 160 m along the near lane: trunks of the north row
    # right next to the junction (observer 3.5 + 3.0 m from the axis, rows at 7 m) are inside the triangle only very
    # close to the junction; the approach field (10 m deep, L1 = 180 m) clears the north row further out
    north = P[P[:, 1] > 0]
    assert np.abs(north[:, 0]).min() > 20.0
    # the access track mouth (no tree within 3 m of the track near the road)
    south = P[P[:, 1] < 0]
    assert np.abs(south[:, 0] - 250.0).min() > 3.0


def test_sight_field_geometry():
    graph, roads, _, _ = _scene()
    J = TR.junctions(graph, roads, {"secondary"})
    assert len(J) == 1 and J[0]["kind"] == "junction"
    polys = TR.sight_polygons(J[0], TR.DEFAULTS)
    assert len(polys) == 4                                           # L2 + L1, both directions
    xs = sorted(round(max(abs(x) for x, _ in p.exterior.coords)) for p in polys)
    assert xs == [160, 160, 180, 180]
    ys = sorted(round(max(y for _, y in p.exterior.coords), 1) for p in polys)
    assert ys == [6.5, 6.5, 13.5, 13.5]                             # observer at half width 3.5 + 3.0 / + 10.0 m


def test_rhythm_and_missing_share():
    line = LineString([(0.0, 0.0), (5000.0, 0.0)])
    P, S, K = TR.layout_line(line, {**TR.DEFAULTS, "spacing_m": [13.0, 17.0], "missing_share": 0.1, "lateral_sd_m": 0.0},
                             "qa")
    gaps = np.diff(P[:, 0])
    assert 13.0 - 1e-6 <= gaps.min() and gaps.max() <= 17.0 + 1e-6
    assert abs(gaps.mean() - 15.0) < 0.5
    assert 0.06 < (~K).mean() < 0.14
    assert set(S) <= set(TR.DEFAULTS["species"])
    dom = max(set(S), key=S.count)
    assert S.count(dom) / len(S) > 0.6                               # one species dominates a planted row


def test_deterministic_and_cut_local():
    graph, roads, track, lines = _scene()
    a = TR.plan(lines, roads, {}, tracks=[track], graph=graph)
    b = TR.plan(lines, roads, {}, tracks=[track], graph=graph)
    assert np.array_equal(_all(a), _all(b))
    c = TR.plan(lines, roads, {}, tracks=[], graph=graph)           # removing the access only adds trees near it
    A, C = _all(a), _all(c)
    far = lambda P: P[np.abs(P[:, 0] - 250.0) > 200.0]  # noqa: E731
    assert np.array_equal(far(A), far(C)) and len(C) >= len(A)


def test_too_close_row_pushed_to_set_back():
    graph, roads, _, _ = _scene()
    lines = [("bdot:X", LineString([(-500.0, 4.5), (-200.0, 4.5)]), "bdot")]      # 1.0 m from the edge
    res = TR.plan(lines, roads, {"missing_share": 0.0, "lateral_sd_m": 0.5}, graph=graph)
    P = _all(res)
    assert len(P) > 10 and res["report"]["moved_to_min_offset"] == len(P)
    d, _ = TR.edge_distance(roads, P)
    assert np.all(d >= 3.0 - 1e-6) and np.all(d < 3.2)


def test_lines_far_from_major_roads_untouched():
    graph, roads, _, _ = _scene()
    lines = [("bdot:F", LineString([(-500.0, 120.0), (500.0, 120.0)]), "bdot")]
    res = TR.plan(lines, roads, {}, graph=graph)
    assert res["handled"] == set() and res["rows"] == []


def test_vegetation_place_opt_in():
    """tree_rows=None leaves vegetation.place unchanged (8 m BDOT rule); a plan replaces the handled rows."""
    line = [[10.0, 60.0], [190.0, 60.0]]
    src = {"bdot10k": {"OT_PTLZ_A": [], "OT_PTRK_A": [], "OT_OIPR_P": [], "OT_PTNZ_A": [], "OT_PTTR_A": [],
                       "OT_OIPR_L": [{"id": "PL.TEST.ROW.1", "props": {"rodzaj": "rząd drzew"},
                                      "geometry": {"coordinates": line}}]},
           "osm": {"nodes": []}}
    blocked = np.zeros((201, 201), bool)
    hf = SimpleNamespace(x0=0.0, y1=200.0)
    zc = np.zeros(blocked.shape, np.float32)
    base, _ = VG.place(src, (0.0, 0.0), hf, zc, blocked, {}, overrides=[])
    again, _ = VG.place(src, (0.0, 0.0), hf, zc, blocked, {}, overrides=[], tree_rows=None)
    assert json.dumps(base) == json.dumps(again) and 8 <= len(base) <= 20     # ADR 0352 addendum: 10-16 m + gaps/replants
    graph = {"edges": [_edge("m", "A", "B", [[0.0, 50.0], [200.0, 50.0]])]}
    plan = TR.plan([("bdot:PL.TEST.ROW.1", LineString(line), "bdot")], TR.roads_from_graph(graph, (0, 0)),
                   {"missing_share": 0.0}, graph=graph)
    for r in plan["rows"]:
        r["key"] = f"treerow:{r['key']}"
    plan["height_m"] = {r["key"]: (12.0, 16.0) for r in plan["rows"]}
    rep = {}
    new, _ = VG.place(src, (0.0, 0.0), hf, zc, blocked, rep, overrides=[], tree_rows=plan)
    assert all(t["src"].startswith("treerow:") for t in new)
    assert rep["tree_rows"]["placed"] == len(new) == len(_all(plan))
    assert 9 <= len(new) <= 15                                                # 180 m / 12-18 m
    assert all(12.0 <= t["h"] <= 16.0 for t in new)


def _half_taken():
    """A BDOT row in a 200 m tile that the plan takes over in half: the line runs 10 m north of the major road
    (y = 60, taken), leaves the tile at x = 200, comes back at y = 150 (100 m from the road: outside `corridor_m`)."""
    import shapely
    coords = [[10.0, 60.0], [190.0, 60.0], [230.0, 60.0], [230.0, 150.0], [190.0, 150.0], [10.0, 150.0]]
    src = {"bdot10k": {"OT_PTLZ_A": [], "OT_PTRK_A": [], "OT_OIPR_P": [], "OT_PTNZ_A": [], "OT_PTTR_A": [],
                       "OT_OIPR_L": [{"id": "PL.TEST.ROW.2", "props": {"rodzaj": "rząd drzew"},
                                      "geometry": {"coordinates": coords}}]},
           "osm": {"nodes": []}}
    graph = {"edges": [_edge("m", "A", "B", [[0.0, 50.0], [200.0, 50.0]])]}
    lines = TR.row_lines(src, (0.0, 0.0), None, {"id": "t"}, shapely.box(0.0, 0.0, 200.0, 200.0))
    plan = TR.plan(lines, TR.roads_from_graph(graph, (0, 0)), {"missing_share": 0.0}, graph=graph)
    for r in plan["rows"]:
        r["key"] = f"treerow:{r['key']}"
    plan["height_m"] = {r["key"]: r["height_m"] for r in plan["rows"]}
    return src, lines, plan


def _place(src, plan, rep=None):
    blocked = np.zeros((201, 261), bool)
    hf = SimpleNamespace(x0=0.0, y1=200.0)
    out, _ = VG.place(src, (0.0, 0.0), hf, np.zeros(blocked.shape, np.float32), blocked, {} if rep is None else rep,
                      overrides=[], tree_rows=plan)
    return out


def test_partly_taken_bdot_row_keeps_old_trees_on_the_rest():
    """Review of PR #101, FIX 1: one taken part used to mark the whole BDOT line handled - the other half lost its
    trees. Now the half that is not taken keeps the 8 m rule, the taken half has the tree_rows trees only."""
    src, lines, plan = _half_taken()
    assert sorted(k for k, *_ in lines) == ["bdot:PL.TEST.ROW.2#0", "bdot:PL.TEST.ROW.2#1"]
    assert plan["taken"] == {"bdot:PL.TEST.ROW.2#0"} and plan["handled"] == set()
    assert list(plan["fallback"]) == ["bdot:PL.TEST.ROW.2"]
    assert plan["fallback"]["bdot:PL.TEST.ROW.2"].length == pytest.approx(190.0)       # the y = 150 half inside the tile
    rep = {}
    new = _place(src, plan, rep)
    old = [t for t in new if t["src"] == "bdot:PL.TEST.ROW.2"]
    row = [t for t in new if t["src"].startswith("treerow:")]
    assert len(old) + len(row) == len(new)
    # the half that is not taken: the default BDOT row rule (ADR 0352 addendum: 10-16 m + +-2.5 m lateral + gaps), inside the tile only
    assert 8 <= len(old) <= 22 and all(abs(t["n"] - 150.0) <= 2.6 and 9.0 <= t["e"] <= 201.0 for t in old)
    xs = sorted(t["e"] for t in old)
    assert all(b - a >= 8.0 for a, b in zip(xs, xs[1:]))
    # ... and they are the very trees the rule alone puts there (same stream: nothing shifts along the line)
    base = [t for t in _place(src, None) if abs(t["n"] - 150.0) <= 2.6 and t["e"] <= 201.0]
    assert json.dumps(old) == json.dumps(base)
    # the taken half: tree_rows trees only (no default-rule tree doubled under the row), nothing outside the tile
    assert 8 <= len(row) <= 16 and all(abs(t["n"] - 60.0) < 4.0 and t["e"] <= 200.0 for t in row)
    assert not [t for t in new if t["e"] > 201.0 or 64.0 < t["n"] < 147.0]
    assert rep["tree_rows"]["lines_handled"] == 0 and rep["tree_rows"]["lines_partly_handled"] == 1
    assert rep["tree_rows"]["fallback_trees"] == len(old)
    assert rep["tree_rows"]["blocked_dropped"] == 0 and rep["tree_rows"]["plan"]["lines_partly_taken"] == 1


def test_partly_taken_bdot_row_respects_sight_fields():
    """The trees the old rule keeps on a partly taken line stay out of the sight fields of the plan."""
    from shapely.geometry import box
    src, _, plan = _half_taken()
    free = [t for t in _place(src, plan) if t["src"].startswith("bdot:")]
    plan["cuts"] = list(plan["cuts"]) + [box(60.0, 140.0, 110.0, 160.0)]
    cut = [t for t in _place(src, plan) if t["src"].startswith("bdot:")]
    assert not [t for t in cut if 60.0 <= t["e"] <= 110.0]
    assert 2 <= len(free) - len(cut) <= 8                                    # 50 m / 10-16 m
    assert json.dumps([t for t in free if not 60.0 <= t["e"] <= 110.0]) == json.dumps(cut)


def test_coverage_whole_line_taken_or_not():
    a, b = LineString([(0, 0), (10, 0)]), LineString([(20, 0), (30, 0)])
    lines = [("bdot:A#0", a, "bdot"), ("bdot:A#1", b, "bdot"), ("bdot:B", a, "bdot"), ("bdot:C", b, "bdot")]
    handled, fb = TR.coverage(lines, {"bdot:A#0", "bdot:A#1", "bdot:B"})
    assert handled == {"bdot:A", "bdot:B"} and fb == {}                       # every part taken; C is all the old rule's
    handled, fb = TR.coverage(lines, {"bdot:A#1"})
    assert handled == set() and list(fb) == ["bdot:A"] and fb["bdot:A"].equals(a)


def test_height_per_line_reaches_the_plan():
    """Review of PR #101, FIX 2: `height_m` of a line (passes the yaml schema) was ignored."""
    graph, roads, _, _ = _scene()
    lines = [("override:x:0", LineString([(-500.0, 7.0), (-300.0, 7.0)]), "authored", {"height_m": [5.0, 6.0]}),
             ("override:x:1", LineString([(-500.0, -7.0), (-300.0, -7.0)]), "authored", {})]
    rows = {r["key"]: r for r in TR.plan(lines, roads, {"height_m": [14.0, 15.0]}, graph=graph)["rows"]}
    assert rows["override:x:0"]["height_m"] == (5.0, 6.0) and rows["override:x:1"]["height_m"] == (14.0, 15.0)


@pytest.fixture(scope="module")
def plans():
    out = {}
    for rid in TILES:
        reg = yaml.safe_load((REPO / "Data" / "Regions" / rid / "region.yaml").read_text(encoding="utf-8"))
        src = json.loads((REPO / "Data" / "Regions" / rid / "generated" / "streetscape_sources.json").read_text(encoding="utf-8"))
        graph = json.loads((REPO / "Data" / "Regions" / rid / "roads.graph.json").read_text(encoding="utf-8"))
        ov = pipeline.load_overrides(rid)
        origin = (reg["origin"]["x"], reg["origin"]["y"])
        out[rid] = (TR.region_plan(rid, ov, src, graph, origin), TR.roads_from_graph(graph, origin, ov), reg, origin)
    return out


def test_every_corridor_tile_opted_in(plans):
    for rid in TILES:
        assert plans[rid][0] is not None, rid
        p = json.loads((REPO / "Data" / "Regions" / rid / "tree_rows_osm.json").read_text(encoding="utf-8"))
        assert p["license"] == "ODbL 1.0" and p["fetched_utc"].startswith("2026-11-15")
    assert TR.region_plan("bialystok-industrial-c", [], {}, {"edges": []}, (0, 0)) is None    # C / Dojlidy untouched
    assert TR.region_plan("bialystok-dojlidy", [], {}, {"edges": []}, (0, 0)) is None


# trees per tile with the data of 2026-11-15 (ADR 0222 table); a range, so a data refresh does not break the test
EXPECTED = {"dk65-01": (5, 15), "dk65-02": (45, 80), "dk65-03": (12, 30), "dk65-04": (45, 80), "dk65-05": (40, 70),
            "dk65-06": (1, 6), "dk65-07": (12, 28), "dk65-08": (25, 45), "dk65-09": (0, 0), "dk65-10": (0, 0),
            "dk65-11": (0, 0), "knyszyn": (6, 16), "knyszyn-s": (0, 0), "knyszyn-w": (80, 130)}


def test_tile_counts_in_range(plans):
    for rid, (lo, hi) in EXPECTED.items():
        n = sum(len(r["P"]) for r in plans[rid][0]["rows"])
        assert lo <= n <= hi, (rid, n)


def test_no_trunk_on_or_near_a_carriageway(plans):
    for rid in TILES:
        res, roads, reg, origin = plans[rid]
        P = _all(res)
        if not len(P):
            continue
        d, _ = TR.edge_distance(roads, P)
        assert d.min() >= TR.MIN_TRUNK_EDGE_M - 1e-6, rid
        bb = reg["bbox"]
        assert (P[:, 0] >= bb["xmin"] - origin[0]).all() and (P[:, 0] <= bb["xmax"] - origin[0]).all(), rid
        assert (P[:, 1] >= bb["ymin"] - origin[1]).all() and (P[:, 1] <= bb["ymax"] - origin[1]).all(), rid


def test_authored_k1_rows(plans):
    """K1-133 (km 14.6, dk65-05): the west row is there with ~15 m rhythm; K1-132 (km 11.7) split at the seam."""
    res, _, reg, origin = plans["dk65-05"]
    west = [r for r in res["rows"] if r["key"] == "treerow:override:dk65-05-roadside-rows:0"]
    assert west and 7 <= len(west[0]["P"]) <= 13                   # 12 stations, 2 missing, N end in a sight field
    P = west[0]["P"] + np.asarray(origin)
    assert np.all((P[:, 1] > 601480) & (P[:, 1] < 601680))
    n02 = sum(len(r["P"]) for r in plans["dk65-02"][0]["rows"] if "override:" in r["key"])
    n03 = sum(len(r["P"]) for r in plans["dk65-03"][0]["rows"] if "override:" in r["key"])
    assert 3 <= n02 + n03 <= 9                                     # ~180 m / 20-25 m


def test_tree_rows_yaml_schema():
    for rid in TILES:
        d = yaml.safe_load((REPO / "Data" / "Regions" / rid / "tree_rows.yaml").read_text(encoding="utf-8"))
        for e in d["tree_rows"]:
            assert e["id"] and e["reason"] and e["verify"]
            assert set(e) - {"id", "reason", "confidence", "verify", "lines"} <= set(TR.DEFAULTS), rid
            for ln in e.get("lines", []):
                assert len(ln["line_epsg2180"]) >= 2
                assert set(ln) - {"line_epsg2180"} <= set(TR.DEFAULTS)
