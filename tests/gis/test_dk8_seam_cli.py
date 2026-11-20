"""DK8 north: oblique boundary placement and edge paint on the single-lane main road.

Uses tracked region data and flat heights; no Unity, GLBs or tile rebuild.
"""
import copy
import json
import sys
from pathlib import Path

import numpy as np
import pytest
import shapely
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.worldgen.qa import seams as Q
from roads import markings as M, seam_taper as ST, standards as S
from roads.meshing import MeshBuf


@pytest.fixture
def gameplay(monkeypatch):
    monkeypatch.setattr(S, "GAMEPLAY_LANE_WIDEN_M", 0.25)


def test_real_wasilkow_boundary_ends_and_symmetric_taper(gameplay, tmp_path):
    tiles = [Q.load_tile(t) for t in ("dk8-wasilkow-01", "dk8-wasilkow-02")]
    seam = Q.shared_edge(tiles[0].bbox, tiles[1].bbox)
    nets = [Q.build_plain(t) for t in tiles]
    # Real generator neighbour loading (not just the QA's in-memory planner).
    for t in tiles:
        d = tmp_path / t.id
        d.mkdir()
        (d / "region.yaml").write_text(yaml.safe_dump(t.region), encoding="utf-8")
        (d / "roads.graph.json").write_text(json.dumps(t.graph), encoding="utf-8")
        (d / "overrides.yaml").write_text(yaml.safe_dump({"overrides": t.overrides}), encoding="utf-8")
    tapers = [ST.plan_region(n, t.id, tmp_path) for t, n in zip(tiles, nets)]
    expected = {251697731, 306912739, 1220009819, 876126468, 760390608}
    for t, n, tp in zip(tiles, nets, tapers):
        ST.apply_widths(n, tp)
        Q.add_sides(t, n)
        assert {x.osm_way for x in Q.crossings(t, seam, n)} == expected
    trunk = [next(p for p in tp if "876126468" in (p.chain + p.other_chain)) for tp in tapers]
    assert trunk[0].hw_seam == pytest.approx(trunk[1].hw_seam)
    assert trunk[0].hw_seam * 2 == pytest.approx(8.75)
    assert trunk[0].length == pytest.approx(trunk[1].length)
    # The short edge survives as part of the longer chain, with its own end section.
    cross = next(x for x in Q.crossings(tiles[0], seam, nets[0]) if x.osm_way == 876126468)
    assert "211148033" in cross.chain
    assert cross.params["szerokoÅ›Ä‡ jezdni [m]"][0] == pytest.approx(8.75)


@pytest.mark.parametrize("direction", [1, -1])
def test_single_lane_gp_edge_paint_inside_asphalt_and_overrides(gameplay, direction):
    t = Q.load_tile("dk8-korycin-01")
    net = Q.build_plain(t)
    sec = copy.deepcopy(next(s for s in net.sec_list if s.edge_id.startswith("w304733170:")))
    assert sec.lanes == 1 and sec.edge_strip == 0
    hw = np.array([2.0, 2.75, 3.0])
    lines = M.edge_lines(sec, hw, direction)
    assert len(lines) == 2
    for lat, kind in lines:
        assert kind == "P-7b"
        assert np.all(np.abs(lat) + M.edge_line_width(sec) / 2 <= hw + 1e-9)
    for override, count in (("none", 0), ("left", 1), ("right", 1), ("both", 2)):
        sec.edge_lines = override
        assert len(M.edge_lines(sec, 2.75, direction)) == count
    sec.construction = True
    assert not M.edge_lines(sec, 2.75, direction)
    sec.construction = False
    sec.roundabout = True
    assert not M.edge_lines(sec, 2.75, direction)
    sec.roundabout = False
    sec.edge_lines = None
    sec.cls = "D"
    assert not M.edge_lines(sec, 2.75, direction)


def test_korycin_route_480m_right_edge_mesh_survives_overlap_pass(gameplay):
    net = Q.build_plain(Q.load_tile("dk8-korycin-01"))
    for c in net.chains:
        c.z = np.zeros(len(c.line.s))
        c.e = np.zeros(len(c.line.s))
    buf = MeshBuf()
    try:
        M._build_markings(buf, net, [], [], {})
        M.drop_overlapping(buf, net, 0)
    finally:
        M._SECS.clear()
    c = next(c for c in net.chains if c.id.startswith("c:w100913073:"))
    triangles = np.concatenate([p.V[p.T, :2] for p in buf.parts if p.src == "P-7b@" + c.id])
    paint = shapely.union_all(shapely.polygons(triangles))
    for s in (450.0, 480.0, 510.0):
        sec = c.section(s, net.sec_list)
        assert sec.edge_id.startswith("w304733170:")
        q = c.line.offset_point(s, -c.hw_at(s) + S.LINE_W_WIDE / 2)
        assert paint.covers(shapely.Point(q)), f"missing right edge at chain station {s}"


@pytest.mark.parametrize("pair,way", [
    (("bialystok-kleeberga", "bialystok-knyszynska"), 261104557),
    (("dk65-05", "dk65-06"), 1560819273),
])
def test_d94_reported_breaks_use_graph_boundary(gameplay, tmp_path, pair, way):
    """Wave 2: displaced oblique endpoints are real seam ends, in both directions.

    Exercise the generator's neighbour loader as well as QA; a loose matching
    tolerance alone cannot recover a candidate rejected by the seam plane test.
    """
    tiles = [Q.load_tile(t) for t in pair]
    seam = Q.shared_edge(tiles[0].bbox, tiles[1].bbox)
    nets = [Q.build_plain(t) for t in tiles]
    for t in tiles:
        d = tmp_path / t.id
        d.mkdir()
        (d / "region.yaml").write_text(yaml.safe_dump(t.region), encoding="utf-8")
        (d / "roads.graph.json").write_text(json.dumps(t.graph), encoding="utf-8")
        (d / "overrides.yaml").write_text(yaml.safe_dump({"overrides": t.overrides}), encoding="utf-8")
    ends = [next(e for e in ST.ends(n) if e.osm_way == way and e.on_seam(seam)) for n in nets]
    assert any(not ST.on_seam(e.xy, seam) for e in ends)  # reproduces the old rejection
    assert ST.match([ends[0]], [ends[1]]) == [(ends[0], ends[1])]
    transitions = []
    crossings = []
    for t, n, e in zip(tiles, nets, ends):
        neighbours = ST.neighbour_ends(t.id, [e], tmp_path)
        assert any(x.osm_way == way for xs in neighbours.values() for x in xs)
        tp = ST.plan_region(n, t.id, tmp_path)
        transitions.append(next((p for p in tp if p.chain == e.chain and p.end == e.end), None))
        ST.apply_widths(n, tp)
        Q.add_sides(t, n)
        crossings.append(next(x for x in Q.crossings(t, seam, n) if x.osm_way == way))
    assert (transitions[0] is None) == (transitions[1] is None)
    if transitions[0]:
        assert transitions[0].hw_seam == pytest.approx(transitions[1].hw_seam)
        assert transitions[0].length == pytest.approx(transitions[1].length)
    rows = Q.compare_pair(*crossings)
    assert all(r["param"] != "droga po drugiej stronie" for r in rows)
    assert next(r for r in rows if r["param"] == "szerokoœæ jezdni [m]")["status"] == "OK"
