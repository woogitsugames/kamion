"""ADR 0224: seam cross-section QA (tools/worldgen/qa/seams.py).

Synthetic tile pairs (equal / 0.2 m apart / shared edge without a road) run through the real generator network code,
then the tool on the region data in git: it must work and find >= 1 road (the route) on every DK65 corridor seam.
No assertion on OK/FAIL of real data except the K1 seam dk65-10 / dk65-11 / knyszyn-s (research K1: 6.0-6.4 m).

ADR 0275: the tool applies the seam transitions of roads.seam_taper, so two nominal sections 0.2 m apart are OK on the
seam with a PRZEJŚCIE row; `taper=False` shows the tiles on their own (the FAIL of ADR 0224). ADR 0233: the lane width
row is the local one (`lanes_follow_width`)."""
import copy
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.worldgen.qa import seams as SM  # noqa: E402


def _tile(tid, x0, road=True, z=120.0, set_=None, stop_short=False):
    """100 x 100 m tile at x0; a two-lane primary road along y = 50 from x0 to x0 + 100 (or ending 40 m short)."""
    x1 = x0 + 100.0
    xa, xb = x0, (x1 - 40.0 if stop_short else x1)
    nodes = [{"id": f"{tid}:a", "x": xa, "y": 50.0, "z_terrain": z, "boundary": xa in (0.0, 100.0, 200.0), "degree": 1},
             {"id": f"{tid}:b", "x": xb, "y": 50.0, "z_terrain": z, "boundary": xb in (0.0, 100.0, 200.0), "degree": 1}]
    attrs = {"highway": {"v": "primary", "src": "osm", "conf": "high"},
             "lanes": {"v": 2, "src": "osm", "conf": "high"},
             "maxspeed": {"v": 90, "src": "osm", "conf": "high"},
             "oneway": {"v": "no", "src": "default", "conf": "medium"}}
    edges = [{"id": f"w7:{tid}a-{tid}b", "from": f"{tid}:a", "to": f"{tid}:b", "osm_way": 7, "attrs": attrs,
              "geometry": [[xa, 50.0], [(xa + xb) / 2, 50.0], [xb, 50.0]], "length_m": xb - xa}] if road else []
    ov = [{"id": "xsec", "target": {"osm_way": [7]}, "set": set_ or {"lanes": 2, "lane_width": 3.1, "edge_strip": 0.2,
                                                                       "edge_lines": "both"}}]
    region = {"bbox": {"xmin": x0, "ymin": 0.0, "xmax": x1, "ymax": 100.0},
              "origin": {"x": x0 + 50.0, "y": 50.0, "z": z}}
    return SM.Tile(id=f"synthetic-{tid}", region=region, graph={"nodes": nodes if road else [], "edges": edges,
                                                                 "sources": {"z_terrain": "gugik-nmt-2025-x"}},
                   overrides=ov, route_edges={e["id"] for e in edges})


def _rows(rep):
    assert rep["summary"]["seams"] == 1
    roads = rep["seams"][0]["roads"]
    return roads, {r["param"]: r for rd in roads for r in rd["rows"]}


def test_shared_edge_geometry():
    assert SM.shared_edge((0, 0, 100, 100), (100, 0, 200, 100))["normal_ab"] == (1.0, 0.0)
    assert SM.shared_edge((0, 100, 100, 200), (0, 0, 100, 100))["axis"] == "y"
    assert SM.shared_edge((0, 0, 100, 100), (100, 100, 200, 200)) is None      # corner only


def test_synthetic_equal_pair_all_ok():
    rep = SM.run(loaded=[_tile("a", 0.0), _tile("b", 100.0)])
    roads, r = _rows(rep)
    assert len(roads) == 1 and roads[0]["on_route"]
    assert all(x["status"] in ("OK", "N/D") for x in r.values()), [x for x in r.values() if x["status"] not in ("OK", "N/D")]
    assert r["szerokość jezdni [m]"]["left"] == pytest.approx(6.6)
    assert r["rozstaw linii krawędziowych [m]"]["left"] == pytest.approx(6.2)     # 6.6 - 2 x EDGE_LINE_INSET_MINOR
    assert r["wys. terenu w osi Z [m]"]["status"] == "OK"
    assert r["położenie osi na szwie [m]"]["delta"] == pytest.approx(0.0, abs=1e-6)


def test_oblique_boundary_shift_is_matched_but_position_error_still_fails():
    tiles = [_tile("a", 0.0), _tile("b", 100.0)]
    for t in tiles:
        for node in t.graph["nodes"]:
            node["y"] = 20.0 + 0.3 * node["x"]
        edge = t.graph["edges"][0]
        edge["geometry"] = [[x, 20.0 + 0.3 * x] for x, _ in edge["geometry"]]
    tiles[0].overrides[0]["set"]["center_offset"] = 0.25
    roads, rows = _rows(SM.run(loaded=tiles, taper=False))
    assert len(roads) == 1
    assert roads[0]["chain_left"] and roads[0]["chain_right"]
    # Normal shift moves the end > 5 cm off x=100; it is still the boundary road.
    pos = rows["położenie osi na szwie [m]"]
    assert pos["status"] == "FAIL"
    assert pos["delta"] == pytest.approx(0.25, abs=0.001)


def test_oblique_non_boundary_end_is_not_invented_as_a_crossing():
    a, b = _tile("a", 0.0, stop_short=True), _tile("b", 100.0)
    roads, rows = _rows(SM.run(loaded=[a, b], taper=False))
    assert len(roads) == 1 and roads[0]["chain_left"] is None
    assert rows["droga po drugiej stronie"]["status"] == "FAIL"


def test_cut_four_centimetres_from_junction_keeps_seam_ribbon():
    from roads import meshing as M

    a, b = _tile("a", 0.0), _tile("b", 100.0)
    b.graph["bbox"] = b.bbox
    inner = dict(b.graph["nodes"][0], id="junction", x=100.04, boundary=False)
    branch_end = dict(inner, id="branch", x=105.0, y=90.0)
    b.graph["nodes"] += [inner, branch_end]
    edge = b.graph["edges"][0]
    stub = dict(edge, id="w7:cut-junction", to=inner["id"], length_m=0.04, clipped=True,
                geometry=[[100.0, 50.0], [100.04, 50.0]])
    edge["from"] = inner["id"]
    edge["geometry"][0] = [100.04, 50.0]
    branch = dict(edge, id="w8:junction-branch", osm_way=8, to=branch_end["id"],
                  geometry=[[100.04, 50.0], [105.0, 90.0]])
    b.graph["edges"] += [stub, branch]
    pairs = SM.adjacent_pairs([a, b])
    nets = SM.build_nets([a, b], pairs, taper=False, trims=True)
    seam = pairs[0][2]
    left, = SM.crossings(a, seam, nets[a.id])
    right, = SM.crossings(b, seam, nets[b.id])
    assert left.osm_way == right.osm_way == 7
    assert left.xy == right.xy == (100.0, 50.0)

    chain = next(c for c in nets[b.id].chains if c.id == right.chain)
    assert chain.length == pytest.approx(0.04)
    assert chain.t_a == chain.t_b == 0.0
    chain.z = np.zeros_like(chain.line.s)
    chain.e = np.zeros_like(chain.line.s)
    for coarse, layer in ((False, "road"), (True, "collision")):
        buf = M.MeshBuf()
        M.build_ribbon(buf, nets[b.id], chain, coarse=coarse)
        asphalt = next(p for p in buf.parts if p.layer == layer and p.mat.endswith("asphalt"))
        assert len(asphalt.T) >= 2
        assert np.unique(asphalt.V[:, 0] + b.origin[0]) == pytest.approx([100.0, 100.04])


@pytest.mark.parametrize(("start", "boundary", "expected_u"), [
    ((100.0, 0.01), True, (0.0, 1.0)),
    ((100.0, 0.0), True, None),
    ((100.01, 0.01), False, None),
])
def test_short_cut_near_bbox_corner(start, boundary, expected_u):
    tile = _tile("b", 100.0)
    tile.graph["bbox"] = tile.bbox
    end = (start[0] + 0.04, start[1] if start[1] else 0.01)
    a, b = tile.graph["nodes"]
    a.update(x=start[0], y=start[1], boundary=boundary)
    b.update(x=end[0], y=end[1], boundary=False)
    edge = tile.graph["edges"][0]
    edge.update(geometry=[start, end], length_m=round(float(np.hypot(*np.subtract(end, start))), 3),
                clipped=boundary)

    net = SM.build_plain(tile)
    assert len(net.chains) == int(boundary)
    if boundary:
        assert net.chains[0].meta["seam_stub"]
    seam_u = net.nodes[a["id"]]["seam_u"]
    if expected_u is None:
        assert seam_u is None
    else:
        assert tuple(seam_u) == expected_u


def _pair_0p2():
    return [_tile("a", 0.0), _tile("b", 100.0, set_={"lanes": 2, "lane_width": 3.2, "edge_strip": 0.2,
                                                     "edge_lines": "both"})]


def test_synthetic_pair_0p2_apart_bridged_by_taper_0275():
    _, r = _rows(SM.run(loaded=_pair_0p2()))
    w = r["szerokość jezdni [m]"]
    assert w["status"] == "OK" and abs(w["delta"]) < 1e-6 and w["left"] == pytest.approx(6.7)
    assert r["rozstaw linii krawędziowych [m]"]["status"] == "OK"
    assert r["pasy × szer. pasa [m]"]["status"] == "OK" and r["pasy × szer. pasa [m]"]["left"] == "2 × 3.15"
    for k in SM.EDGE_ROWS:
        assert r[k]["status"] == "OK" and abs(r[k]["delta"]) <= SM.EDGE_TOL_M
    tp = r["przejście szerokości (ADR 0275)"]
    assert tp["status"] == "PRZEJŚCIE" and tp["delta"] == pytest.approx(0.1)
    assert not [x for x in r.values() if x["status"] == "FAIL"]


def test_synthetic_pair_0p2_apart_fails():
    rep = SM.run(loaded=_pair_0p2(), taper=False)
    _, r = _rows(rep)
    w = r["szerokość jezdni [m]"]
    assert w["status"] == "FAIL" and w["delta"] == pytest.approx(0.2)
    assert r["rozstaw linii krawędziowych [m]"]["status"] == "FAIL"
    assert r["opaska (edge_strip) [m]"]["status"] == "OK"


def test_synthetic_tolerance_edge_0p1_ok():
    rep = SM.run(loaded=[_tile("a", 0.0), _tile("b", 100.0, set_={"lanes": 2, "lane_width": 3.15, "edge_strip": 0.2,
                                                                  "edge_lines": "both"})], taper=False)
    _, r = _rows(rep)
    assert r["szerokość jezdni [m]"]["delta"] == pytest.approx(0.1) and r["szerokość jezdni [m]"]["status"] == "OK"
    # the asphalt edge has the tighter tolerance of ADR 0275: 0.05 m per side is a step
    assert all(r[k]["status"] == "FAIL" for k in SM.EDGE_ROWS)


def test_synthetic_lanes_follow_width_adr0233():
    """dk65-11 | knyszyn-s: K1 section 2 x 3.1 against a 7.5 m section whose profile starts at 6.6 m with
    lanes_follow_width - the lanes painted at the seam are 3.10 on both sides (the tool said 3.10 vs 3.55)."""
    b = _tile("b", 100.0, set_={"edge_strip": 0.2, "edge_lines": "both", "lanes_follow_width": True,
                                "width": [[0, 6.6], [0.6, 6.6], [0.8, 7.5], [1, 7.5]]})
    _, r = _rows(SM.run(loaded=[_tile("a", 0.0), b]))
    lw = r["pasy × szer. pasa [m]"]
    assert lw["left"] == lw["right"] == "2 × 3.10" and lw["status"] == "OK"
    assert "lanes_follow_width" in lw["source"]
    assert not [x for x in r.values() if x["status"] == "FAIL"]
    b.overrides[0]["set"]["lanes_follow_width"] = False      # ADR 0095 default: lanes keep the widest station
    _, r = _rows(SM.run(loaded=[_tile("a", 0.0), b]))
    assert r["pasy × szer. pasa [m]"]["right"] == "2 × 3.55" and r["pasy × szer. pasa [m]"]["status"] == "FAIL"


def test_synthetic_edge_without_road():
    rep = SM.run(loaded=[_tile("a", 0.0, stop_short=True), _tile("b", 100.0, road=False)])
    roads, _ = _rows(rep)
    assert roads == []


def test_synthetic_road_ending_on_one_side_fails():
    rep = SM.run(loaded=[_tile("a", 0.0), _tile("b", 100.0, road=False)])
    roads, r = _rows(rep)
    assert len(roads) == 1 and r["droga po drugiej stronie"]["status"] == "FAIL"


def test_nearby_unpaired_branch_leaves_same_way_continuation_available():
    """A branch cut just before a junction cannot consume the continuation of the through road."""
    branch = SM.Crossing("a", "branch", 7, "residential", (100.0, 50.0), False, {})
    through_a = SM.Crossing("a", "through-a", 8, "tertiary", (100.0, 50.584), False, {})
    through_b = SM.Crossing("b", "through-b", 8, "tertiary", (100.0, 50.584), False, {})
    assert SM.match([branch, through_a], [through_b]) == [(branch, None), (through_a, through_b)]
    assert SM.match([through_b], [through_a, branch]) == [(through_b, through_a), (None, branch)]


@pytest.mark.parametrize(("left_y", "right_y"), [
    ((1.0, 4.0), (-4.0, 2.0)),  # The nearest pair would leave both other ends unmatched.
    ((1.0, 4.0), (-1.0, 2.0)),  # Both complete assignments fit, but one costs 4 m and the other 6 m.
])
def test_same_way_pairs_maximize_count_then_minimize_distance(left_y, right_y):
    left = [SM.Crossing("a", f"a{i}", 7, "residential", (100.0, y), False, {})
            for i, y in enumerate(left_y)]
    right = [SM.Crossing("b", f"b{i}", 7, "residential", (100.0, y), False, {})
             for i, y in enumerate(right_y)]
    assert SM.match(left[::-1], right[::-1]) == list(zip(left, right))
    assert SM.match(right, left) == list(zip(right, left))


def test_synthetic_edge_line_spacing_rule_adr0220():
    st = {"width": 7.6, "edge_lines": "both"}
    a, b = _tile("a", 0.0, set_=st), _tile("b", 100.0, set_=st)
    b.overrides = copy.deepcopy(b.overrides) + [{"id": "k1", "target": {"osm_way": [7]}, "set": {"edge_line_spacing": 6.2}}]
    _, r = _rows(SM.run(loaded=[a, b], taper=False))
    sp = r["rozstaw linii krawędziowych [m]"]
    assert sp["left"] == pytest.approx(7.2) and sp["right"] == pytest.approx(6.2) and sp["status"] == "FAIL"
    _, r = _rows(SM.run(loaded=[a, b]))
    sp = r["rozstaw linii krawędziowych [m]"]
    assert sp["left"] == sp["right"] == pytest.approx(6.7) and sp["status"] == "OK"


def test_synthetic_deterministic():
    t = lambda: [_tile("a", 0.0), _tile("b", 100.0)]  # noqa: E731
    assert SM.run(loaded=t()) == SM.run(loaded=t())


# ------------------------------------------------------------------ real data in git
DK65 = sorted({t for p in SM.DK65_SEAMS for t in p})


@pytest.fixture(scope="module")
def real():
    if not all((SM.REG / t / "roads.graph.json").exists() for t in DK65):
        pytest.skip("region data missing")
    return SM.run(DK65)


def test_real_every_dk65_seam_has_route_road(real):
    got = {(s["a"], s["b"]): s for s in real["seams"]}
    for a, b in SM.DK65_SEAMS:
        s = got.get((a, b)) or got.get((b, a))
        assert s is not None, (a, b)
        assert len(s["roads"]) >= 1, (a, b)
        assert sum(r["on_route"] for r in s["roads"]) >= 1, (a, b)


def test_real_rows_have_status_and_source(real):
    for s in real["seams"]:
        for rd in s["roads"]:
            for r in rd["rows"]:
                assert r["status"] in ("OK", "FAIL", "UWAGA", "N/D", "PRZEJŚCIE") and r["source"], (s["a"], s["b"], r)


def _k1(real, a, b):
    s = next(x for x in real["seams"] if (x["a"], x["b"]) == (a, b))
    rd = next(r for r in s["roads"] if r["on_route"])
    return [r for r in rd["rows"] if r["param"].startswith("referencja rozstawu linii")]


def test_real_k1_seam_dk65_10_side_has_k1_section(real):
    """dk65-10 carries `dk65-xsec-k1` (ADR 0214 r3): lines 6.2 m apart at the seam with dk65-11."""
    rows = _k1(real, "dk65-10", "dk65-11")
    left = next(r for r in rows if "(lewa)" in r["param"])
    assert left["status"] == "OK" and left["left"] == pytest.approx(6.2, abs=0.05)


def test_real_k1_seams_10_11_knyszyn_s_all_k1(real):
    """ADR 0233 (was xfail until the joint K1 correction): K1 section through both seams."""
    for a, b in (("dk65-10", "dk65-11"), ("dk65-11", "knyszyn-s")):
        for r in _k1(real, a, b):
            assert r["status"] == "OK", (a, b, r)


def test_real_seam_dk65_11_knyszyn_s_lanes_follow_width(real):
    """ADR 0233: no false FAIL "3,10 vs 3,55" - every carriageway row of the route road agrees on this seam."""
    s = next(x for x in real["seams"] if (x["a"], x["b"]) == ("dk65-11", "knyszyn-s"))
    rd = next(r for r in s["roads"] if r["on_route"])
    rows = {r["param"]: r for r in rd["rows"]}
    assert rows["pasy × szer. pasa [m]"]["left"] == rows["pasy × szer. pasa [m]"]["right"] == "2 × 3.10"
    for k in ("pasy × szer. pasa [m]", "szerokość jezdni [m]", "rozstaw linii krawędziowych [m]", *SM.EDGE_ROWS):
        assert rows[k]["status"] == "OK", rows[k]
    assert not [r for r in rd["rows"] if r["status"] == "FAIL"], [r for r in rd["rows"] if r["status"] == "FAIL"]


@pytest.mark.parametrize("widen", [0.0, 0.1, 0.25])
@pytest.mark.parametrize("pair,spacing,limits", [
    (("dk65-05", "dk65-06"), 6.2, (6.0, 6.4)),
    (("knyszyn-s", "knyszyn"), 6.8, (6.6, 7.0)),
])
@pytest.mark.parametrize("error", [0.0, 0.5])
def test_reference_tracks_d94_without_relaxing_measured_range(monkeypatch, widen, pair, spacing, limits, error):
    from roads import standards as S
    monkeypatch.setattr(S, "GAMEPLAY_LANE_WIDEN_M", widen)
    st = {"width": 8.0, "edge_lines": "both", "edge_line_spacing": spacing + error}
    a, b = _tile(pair[0], 0.0, set_=st), _tile(pair[1], 100.0, set_=st)
    a.id, b.id = pair
    rep = SM.run(loaded=[a, b], trims=False)
    refs = [r for seam in rep["seams"] for road in seam["roads"] for r in road["rows"]
            if r["param"].startswith("referencja rozstawu linii")]
    assert len(refs) == 2
    lo, hi = (v + 2 * widen for v in limits)
    for r in refs:
        assert f"{lo:.1f}–{hi:.1f} m" in r["param"]
        assert r["status"] == ("FAIL" if error else "OK")
        assert (r["left"] if r["left"] is not None else r["right"]) == pytest.approx(spacing + error + 2 * widen)
