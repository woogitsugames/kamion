"""ADR 0275: width transitions across tile seams and at the end of a shoulder override (roads/seam_taper.py).

Synthetic tile pairs through the real generator network code (the QA tool's build_nets = the calls of
pipeline.build_network / build), then the region data in git: every road cut by a seam has the same carriageway
half-width on both sides after the transitions.

Shoulders: paved / ground widths of a kerbless edge from roads.xsec (ADR 0272), e.g. dk65-opaska-k1 against the class rule.
"""
from copy import deepcopy
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.worldgen.qa import seams as SM  # noqa: E402

sys.path.insert(0, str(ROOT / "tools" / "worldgen"))
from roads import markings as MK  # noqa: E402
from roads import network as Nw  # noqa: E402
from roads import pipeline  # noqa: E402
from roads import seam_taper as ST  # noqa: E402


A_SET = {"width": 7.3, "edge_strip": 0.2, "edge_lines": "both"}
B_SET = {"width": 6.76, "edge_strip": 0.2, "edge_lines": "both"}


def _tile(tid, x0, set_=None, length=100.0, from_seam=None, flip_way=False, seam_last=False, ways=1, extra=None):
    """100 x 100 m tile at x0 with a two-lane primary road (90 km/h) along y = 50. The road starts on the seam side
    (`from_seam` = x of the seam) and is `length` long; flip_way reverses the OSM edge (left/right of the way swap);
    seam_last gives the seam node the larger id, so the chain runs towards the seam. ways = 2 splits the road into
    way 7 and way 8 at a through node."""
    x1 = x0 + 100.0
    seam = x1 if from_seam is None else from_seam
    far = seam - length if seam == x1 else seam + length
    xs = [seam, far] if ways == 1 else [seam, 0.5 * (seam + far), far]
    names = ["z" if seam_last else "a"] + [f"m{i}" for i in range(len(xs) - 2)] + ["a" if seam_last else "z"]
    nodes = [{"id": f"{tid}:{n}", "x": x, "y": 50.0, "z_terrain": 120.0, "boundary": x in (x0, x1), "degree": 1}
             for n, x in zip(names, xs)]
    attrs = {"highway": {"v": "primary", "src": "osm", "conf": "high"}, "lanes": {"v": 2, "src": "osm", "conf": "high"},
             "maxspeed": {"v": 90, "src": "osm", "conf": "high"}, "oneway": {"v": "no", "src": "default", "conf": "medium"}}
    edges = []
    for i, (na, nb) in enumerate(zip(nodes, nodes[1:])):
        a, b = (nb, na) if flip_way else (na, nb)
        edges.append({"id": f"w{7 + i}:{a['id']}-{b['id']}", "from": a["id"], "to": b["id"], "osm_way": 7 + i,
                      "attrs": attrs, "length_m": abs(b["x"] - a["x"]),
                      "geometry": [[a["x"], 50.0], [0.5 * (a["x"] + b["x"]), 50.0], [b["x"], 50.0]]})
    ov = [{"id": f"xsec-{tid}", "target": {"osm_way": [7]}, "set": dict(set_ or A_SET)}] + list(extra or [])
    region = {"bbox": {"xmin": x0, "ymin": 0.0, "xmax": x1, "ymax": 100.0}, "origin": {"x": x0 + 50.0, "y": 50.0, "z": 120.0}}
    return SM.Tile(id=f"synthetic-{tid}", region=region, graph={"nodes": nodes, "edges": edges,
                                                                 "sources": {"z_terrain": "gugik-nmt-2025-x"}},
                   overrides=ov, route_edges={e["id"] for e in edges})


def _pair(a_kw=None, b_kw=None):
    return [_tile("a", 0.0, **{"set_": A_SET, **(a_kw or {})}), _tile("b", 100.0, **{"set_": B_SET, "from_seam": 100.0, **(b_kw or {})})]


def _nets(ts, taper=True):
    return SM.build_nets(ts, SM.adjacent_pairs(ts), taper=taper)


def _seam_view(net, x_seam=100.0):
    """(chain, distance of every station from the seam, index of the seam station)."""
    c, = [chain for chain in net.chains if np.min(np.abs(chain.line.p[:, 0] + net.origin[0] - x_seam)) < 1e-6]
    xw = c.line.p[:, 0] + net.origin[0]
    i = int(np.argmin(np.abs(xw - x_seam)))
    assert abs(xw[i] - x_seam) < 1e-6 and i in (0, len(xw) - 1)
    return c, np.abs(xw - x_seam), i


# ------------------------------------------------------------------------------------------------ S-curve
def test_weight_is_half_a_smoothstep():
    L = 27.0
    assert ST.weight(0.0, L) == 1.0 and ST.weight(L / 2, L) == 0.0 and ST.weight(40.0, L) == 0.0
    d = np.linspace(0, L / 2, 200)
    assert (np.diff(ST.weight(d, L)) <= 1e-12).all()
    # both halves make one smoothstep: own + (other - own) * w / 2 on side A == mirrored expression on side B
    x = np.linspace(-L / 2, L / 2, 401)
    a, b = 7.3, 6.76
    va = a + (0.5 * (a + b) - a) * ST.weight(-x[x <= 0], L)
    vb = b + (0.5 * (a + b) - b) * ST.weight(x[x >= 0], L)
    f = lambda u: u * u * (3 - 2 * u)  # noqa: E731
    assert np.allclose(np.concatenate([va, vb[1:]]), a + (b - a) * f(0.5 + x / L), atol=1e-12)


# ------------------------------------------------------------------------------------------------ carriageway width
def test_two_tiles_730_676_no_step_on_the_seam():
    nets = _nets(_pair())
    (ca, da, ia), (cb, db, ib) = (_seam_view(nets[k]) for k in ("synthetic-a", "synthetic-b"))
    wa, wb = 2 * ca.hw, 2 * cb.hw
    assert abs(wa[ia] - wb[ib]) < 1e-9 < 0.02
    assert wa[ia] == pytest.approx(7.03, abs=1e-9)
    # length: 0.27 m per edge x RATIO 100 = 27 m, half in each tile; beyond it the nominal width, untouched
    ta, tb = nets["synthetic-a"].seam_tapers, nets["synthetic-b"].seam_tapers
    assert len(ta) == len(tb) == 1
    for t in (ta[0], tb[0]):
        assert t.length == pytest.approx(27.0) and t.step_m == pytest.approx(0.27) and t.skipped is None
    assert np.allclose(wa[da >= 13.5], 7.3, atol=1e-12) and np.allclose(wb[db >= 13.5], 6.76, atol=1e-12)
    assert (wa[da <= 13.0] < 7.3).all() and (wb[db <= 13.0] > 6.76).all()
    # one monotone curve through the seam, no kink: the edge moves at most 1.5 x step / L per metre
    prof = np.concatenate([wa[np.argsort(-da)], wb[np.argsort(db)][1:]])
    assert (np.diff(prof) <= 1e-12).all() and prof[0] == pytest.approx(7.3) and prof[-1] == pytest.approx(6.76)
    assert np.abs(np.diff(prof / 2)).max() <= 1.5 * 0.27 / 27.0 * 0.5 + 1e-9          # stations 0.5 m apart
    assert np.abs(np.diff(prof / 2)).max() < 0.02
    sa = abs(wa[ia] - wa[ia + (1 if ia == 0 else -1)])
    sb = abs(wb[ib] - wb[ib + (1 if ib == 0 else -1)])
    assert sa == pytest.approx(sb, rel=0.02)                                         # same slope on both sides


def test_lanes_follow_the_width_inside_the_transition():
    """Without `lanes_follow_width` the centre line of a two-way road is laid from the edge: it would leave the axis
    by half the width change. The touched sections get the flag (provenance derived)."""
    nets = _nets(_pair())
    for k in ("synthetic-a", "synthetic-b"):
        c, _d, _i = _seam_view(nets[k])
        sec = nets[k].sec_list[int(c.sec_idx[0])]
        assert sec.lane_follow and sec.provenance["lanes_follow_width"].startswith("derived:seam_taper")
        for hw in c.hw[::5]:
            lat_c, _b, centres = MK.lane_layout(sec, float(hw), 0)
            assert abs(lat_c) < 1e-9
            assert centres["fwd"][0] == pytest.approx(-centres["bwd"][0])
        lines = MK.edge_lines(sec, c.hw, 0)
        assert len(lines) == 2 and np.allclose(np.abs(lines[0][0]), np.abs(lines[1][0]))


def test_equal_sections_are_untouched():
    ts = [_tile("a", 0.0), _tile("b", 100.0, from_seam=100.0)]
    nets, plain = _nets(ts), _nets(ts, taper=False)
    for k in nets:
        assert nets[k].seam_tapers == []
        assert np.array_equal(nets[k].chains[0].hw, plain[k].chains[0].hw)
        assert not nets[k].sec_list[0].lane_follow


def test_deterministic_and_independent_of_tile_order():
    n1, n2, n3 = _nets(_pair()), _nets(_pair()), _nets(list(reversed(_pair())))
    for k in n1:
        assert np.array_equal(n1[k].chains[0].hw, n2[k].chains[0].hw)
        assert np.array_equal(n1[k].chains[0].hw, n3[k].chains[0].hw)
        assert [t.report() for t in n1[k].seam_tapers] == [t.report() for t in n3[k].seam_tapers]


def test_each_tile_needs_only_the_neighbours_nominal_end():
    """The plan of tile a from (own ends, neighbour ends) equals what the pair run gives - and tile b gets the mirror."""
    ts = _pair()
    plain = {t.id: SM.build_plain(t) for t in ts}
    ea, eb = ST.ends(plain["synthetic-a"]), ST.ends(plain["synthetic-b"])
    ta = ST.plan(ea, {"b": [e for e in eb if abs(e.xy[0] - 100.0) < 0.05]})
    tb = ST.plan(eb, {"a": [e for e in ea if abs(e.xy[0] - 100.0) < 0.05]})
    assert len(ta) == len(tb) == 1
    assert ta[0].hw_seam == tb[0].hw_seam and ta[0].length == tb[0].length
    assert (ta[0].hw_own, ta[0].hw_other) == (tb[0].hw_other, tb[0].hw_own)


def test_short_chain_limits_the_length():
    ts = _pair(b_kw={"length": 8.0})
    nets = _nets(ts)
    (ca, da, ia), (cb, db, ib) = (_seam_view(nets[k]) for k in ("synthetic-a", "synthetic-b"))
    for k in nets:
        assert nets[k].seam_tapers[0].length == pytest.approx(16.0)      # 2 x the 8 m chain, not 27 m
    assert abs(ca.hw[ia] - cb.hw[ib]) < 1e-9
    far = int(np.argmax(db))
    assert 2 * cb.hw[far] == pytest.approx(6.76, abs=1e-9)               # the junction end keeps its width
    assert np.allclose(2 * ca.hw[da >= 8.0], 7.3, atol=1e-12)


def test_measured_lane_edges_are_not_blended():
    """ADR 0095 sections (measured lane edges / width profile without lanes_follow_width) keep their width: the
    transition is reported as skipped instead of bending measured lanes."""
    prof = {"edge_strip": 0.2, "edge_lines": "both", "width": [[0, 6.76], [1, 6.76 + 1e-9]]}
    ts = _pair(b_kw={"set_": prof})
    nets, plain = _nets(ts), _nets(ts, taper=False)
    for k in nets:
        assert np.array_equal(nets[k].chains[0].hw, plain[k].chains[0].hw)
        (t,) = nets[k].seam_tapers
        assert t.skipped and "skipped" in t.report()


def test_smoothing_keeps_authored_width_at_a_short_boundary_section():
    prof = {"width": [[0, 14.5], [1, 14.5]]}
    ts = _pair(a_kw={"set_": prof}, b_kw={
        "set_": {"width": 14.5}, "ways": 2,
        "extra": [{"id": "wider-approach", "target": {"osm_way": [8]}, "set": {"width": 15.0}}],
    })
    graph = ts[1].graph
    graph["nodes"][1]["x"] = 101.35
    for edge, ends in zip(graph["edges"], ((100, 101.35), (101.35, 200))):
        a, b = ends
        edge["length_m"] = b - a
        edge["geometry"] = [[a, 50.0], [b, 50.0]]
    nets = _nets(ts)
    for tile in ts:
        chain, _, end = _seam_view(nets[tile.id])
        assert 2 * chain.hw[end] == pytest.approx(14.5)
        assert not nets[tile.id].seam_tapers
    chain, _, end = _seam_view(nets[ts[1].id])
    assert 2 * chain.hw[-1 if end == 0 else 0] == pytest.approx(15.0)


@pytest.mark.parametrize("width_b", [8.0, 8.2])
def test_edge_line_spacing_blends_an_override_against_the_default(width_b):
    ts = _pair(a_kw={"set_": {"width": 8.0, "edge_lines": "both", "edge_line_spacing": 7.3}},
               b_kw={"set_": {"width": width_b, "edge_lines": "both"}, "flip_way": True})
    nets = _nets(ts)
    nominal = (7.3, width_b - 2 * Nw.S.EDGE_LINE_INSET_MINOR)
    for tile, own in zip(ts, nominal):
        net = nets[tile.id]
        chain, distance, end = _seam_view(net)
        sec = net.sec_list[int(chain.sec_idx[end])]
        far = int(np.argmax(distance))
        for i, want in ((end, np.mean(nominal)), (far, own)):
            s = chain.line.s[i]
            lines = MK.edge_lines(sec, chain.hw_at(s), chain.dirn[i], chain.edge_line_spacing_delta_at(s))
            assert abs(lines[1][0] - lines[0][0]) == pytest.approx(want)
        (taper,) = net.seam_tapers
        assert taper.report()["edge_line_spacing_seam_m"] == pytest.approx(np.mean(nominal))


@pytest.mark.parametrize("reversed_chain", [False, True])
def test_d94_measured_lanes_share_the_tighter_clearance_at_the_seam(monkeypatch, reversed_chain):
    monkeypatch.setattr(Nw.S, "GAMEPLAY_LANE_WIDEN_M", Nw.S.GAMEPLAY_LANE_WIDEN_DEFAULT_M)
    measured = {"width": 9.95, "lane_edges": [0.2, 3.7, 7.2], "edge_lines": "both"}
    ts = _pair(a_kw={"set_": measured, "flip_way": True},
               b_kw={"set_": measured, "seam_last": reversed_chain})
    for tile, neighbours in zip(ts, ((40.0, 60.0), (60.0,))):
        main = tile.graph["edges"][0]
        main["attrs"]["highway"]["v"] = "motorway"
        main["attrs"]["oneway"]["v"] = "yes"
        for way, y in enumerate(neighbours, start=8):
            x1, x2 = [p[0] for p in main["geometry"]][::2]
            first, last = f"n{way}:first", f"n{way}:last"
            x1, x2 = x2 - 3, x1 + 3  # opposite carriageway, wholly inside its tile
            tile.graph["nodes"] += [{"id": node, "x": x, "y": y, "boundary": False}
                                    for node, x in ((first, x1), (last, x2))]
            edge = deepcopy(main)
            edge.update(id=f"w{way}:{first}-{last}", osm_way=way, geometry=[[x1, y], [x2, y]])
            edge.update({"from": first, "to": last})
            tile.graph["edges"].append(edge)
            tile.overrides.append({"id": f"separator-{way}", "target": {"osm_way": [way]}, "set": measured})
    plain, nets = _nets(ts, taper=False), _nets(ts)
    points = []
    for tile, nominal in zip(ts, (9.95, 10.45)):
        chain, distance, end = _seam_view(nets[tile.id])
        sec = nets[tile.id].sec_list[int(chain.sec_idx[end])]
        plain_chain, _, plain_end = _seam_view(plain[tile.id])
        assert 2 * plain_chain.hw[plain_end] == pytest.approx(nominal)
        assert 2 * chain.hw[end] == pytest.approx(9.95)
        assert 2 * chain.hw[np.argmax(distance)] == pytest.approx(nominal)
        dirn = int(chain.dirn[end])
        coords = np.asarray(sec.lane_edges_at(chain.hw[end]))
        assert coords == pytest.approx(measured["lane_edges"])
        assert sec.lane_w_at(chain.hw[end]) == pytest.approx(3.5)
        far_hw = chain.hw[np.argmax(distance)]
        _, far_bounds, _ = MK.lane_layout(sec, far_hw, dirn)
        _, bounds, _ = MK.lane_layout(sec, chain.hw[end], dirn)
        assert MK.follow_edge(sec, far_bounds[0], far_hw, chain.hw[end], dirn) == pytest.approx(bounds[0])
        assert sec.lane_coord(np.array(bounds), chain.hw[end], dirn) == pytest.approx([1.0])
        lines = MK.edge_lines(sec, chain.hw[end], dirn)
        assert abs(lines[1][0] - lines[0][0]) == pytest.approx(7.0)
        points.append(chain.line.p[end] + nets[tile.id].origin)
    assert points[0] == pytest.approx(points[1])


def test_open_shoulder_uses_the_neighbours_median_at_the_seam():
    ts = _pair()
    nets = _nets(ts)
    a, b = (_seam_view(nets[tile.id]) for tile in ts)
    for chain, _, end in (a, b):
        chain.side["L"]["kind"][:] = Nw.RURAL
        chain.side["L"]["mat"][:] = 0
    a[0].side["L"]["kind"][a[2]] = Nw.MEDIAN_RURAL
    median, rural = (ST.side_val(chain, "L", end) for chain, _, end in (a, b))
    assert ST.agree(median, rural) == ST.agree(rural, median) == median
    chain, distance, end = b
    ST.apply_sides(nets[ts[1].id], [ST.SideFix(chain.id, end, "L", median, rural, median)])
    assert ST.side_cat(chain.side["L"], end) == "median"
    assert chain.side["L"]["median"][end]
    assert ST.side_cat(chain.side["L"], int(np.argmax(distance))) == "rural"


# ------------------------------------------------------------------------------------------------ shoulders (ADR 0272)
SH_A = {"lanes": 2, "lane_width": 3.1, "edge_strip": 0.2, "edge_lines": "both",
        "shoulder": {"kind": "ground", "paved_m": 0.35, "ground_m": 0.75}}          # dk65-opaska-k1: 6.6 + 2 x 0.35 = 7.3
SH_B = {"lanes": 2, "lane_width": 3.1, "edge_strip": 0.2, "edge_lines": "both"}     # class rule


def _paved(net, side):
    c = net.chains[0]
    return np.array([ST.shoulder_at(c, side, i)[0] for i in range(len(c.line.s))])


@pytest.mark.parametrize("b_kw", [{}, {"flip_way": True}, {"seam_last": True}, {"flip_way": True, "seam_last": True}])
def test_shoulder_730_676_asphalt_edge_meets_on_the_seam(b_kw):
    rule = ST.X.class_rule(SM.build_plain(_tile("b", 100.0, set_=SH_B)).sec_list[0])
    ts = _pair(a_kw={"set_": SH_A}, b_kw={"set_": SH_B, **b_kw})
    nets, plain = _nets(ts), _nets(ts, taper=False)
    (ca, da, ia), (cb, db, ib) = (_seam_view(nets[k]) for k in ("synthetic-a", "synthetic-b"))
    assert np.array_equal(ca.hw, plain["synthetic-a"].chains[0].hw)           # carriageway 6.6 m on both: untouched
    seam_cm = (35 + int(round(rule.paved_m * 100)) + 1) // 2
    for side in ("L", "R"):
        pa, pb = _paved(nets["synthetic-a"], side), _paved(nets["synthetic-b"], side)
        assert pa[ia] == pb[ib] == pytest.approx(seam_cm / 100.0)             # same centimetre in both tiles
        assert abs((ca.hw[ia] + pa[ia]) - (cb.hw[ib] + pb[ib])) < 0.02
        step = abs(0.35 - rule.paved_m)
        half = 0.5 * min(max(ST.RATIO * step, ST.MIN_LEN_M), ST.MAX_LEN_M)
        assert np.allclose(pa[da >= half], 0.35, atol=1e-9) and np.allclose(pb[db >= half], rule.paved_m, atol=1e-9)
        prof = np.concatenate([pa[np.argsort(-da)], pb[np.argsort(db)][1:]])
        assert (np.diff(prof) <= 1e-12).all() and np.abs(np.diff(prof)).max() <= 0.02 + 1e-9
    # without the transition: the step the task describes
    p0a, p0b = _paved(plain["synthetic-a"], "L"), _paved(plain["synthetic-b"], "L")
    assert abs(p0a[ia] - p0b[ib]) == pytest.approx(abs(0.35 - rule.paved_m))


def test_shoulder_sides_are_matched_in_the_world_frame():
    """One-sided override in tile a (the way's left = one world side): the same world side of tile b blends, the
    other stays on the class rule - whichever way the neighbour's way and chain run."""
    a_set = {**SH_B, "shoulder_left": {"kind": "ground", "paved_m": 0.45, "ground_m": 0.75}}
    for b_kw in ({}, {"seam_last": True}, {"flip_way": True}, {"flip_way": True, "seam_last": True}):
        ts = _pair(a_kw={"set_": a_set}, b_kw={"set_": SH_B, **b_kw})
        nets = _nets(ts)
        out = {}
        for k in ("synthetic-a", "synthetic-b"):
            c, d, i = _seam_view(nets[k])
            far = int(np.argmax(d))
            for side, sgn in (("L", 1.0), ("R", -1.0)):
                w = "N" if sgn * c.line.n[i][1] > 0 else "S"
                out[(k, w)] = ST.shoulder_at(c, side, i)
                out[(k, w, "far")] = ST.shoulder_at(c, side, far)
        rule = min(out[("synthetic-b", "N", "far")], out[("synthetic-b", "S", "far")])
        assert out[("synthetic-b", "N", "far")] == out[("synthetic-b", "S", "far")] == rule
        ov = "N" if out[("synthetic-a", "N", "far")][0] == pytest.approx(0.45) else "S"
        other = "S" if ov == "N" else "N"
        assert out[("synthetic-a", ov, "far")][0] == pytest.approx(0.45) and out[("synthetic-a", other, "far")] == rule
        assert out[("synthetic-a", ov)] == out[("synthetic-b", ov)], b_kw
        assert rule[0] < out[("synthetic-a", ov)][0] < 0.45
        assert out[("synthetic-a", other)] == out[("synthetic-b", other)] == rule, b_kw


def test_shoulder_override_ending_inside_a_tile_gets_a_ramp():
    """Way 7 carries the override, way 8 of the same chain the class rule: S-curve centred on the way boundary."""
    t = _tile("a", 0.0, set_=SH_A, ways=2, extra=[{"id": "w8", "target": {"osm_way": [8]}, "set": SH_B}])
    net = SM.add_sides(t, SM.build_plain(t))
    c = net.chains[0]
    raw = _paved(net, "L")
    j = np.where(np.diff(raw) != 0)[0]
    assert len(j) == 1 and abs(raw[j[0] + 1] - raw[j[0]]) > 0.2
    rep = ST.apply_shoulders(net, [])
    assert rep["in_chain_ramps"] == 2                                   # one per side
    p = _paved(net, "L")
    s_step = 0.5 * (c.line.s[j[0]] + c.line.s[j[0] + 1])
    step = abs(raw[-1] - raw[0])
    half = 0.5 * min(max(ST.RATIO * step, ST.MIN_LEN_M), ST.MAX_LEN_M)
    d = np.abs(c.line.s - s_step)
    assert np.array_equal(p[d > half], raw[d > half])
    assert np.abs(np.diff(p)).max() <= 0.02 + 1e-9 and (np.diff(p) * np.sign(raw[-1] - raw[0]) >= -1e-12).all()
    assert ST.apply_shoulders(net, [])["in_chain_ramps"] == 0 or np.abs(np.diff(_paved(net, "L"))).max() <= 0.02 + 1e-9


# ------------------------------------------------------------------------------------------------ data in git
REGIONS = sorted(p.name for p in ST.REGIONS.iterdir() if (p / "roads.graph.json").exists() and (p / "region.yaml").exists())


@pytest.fixture(scope="module")
def built():
    if not REGIONS:
        pytest.skip("region data missing")
    return {r: pipeline.build_network(r) for r in REGIONS}


def test_real_every_seam_road_has_one_width(built):
    """After pipeline.build_network every road cut by a tile seam has the same half-width on both sides."""
    ends = {r: ST.ends(net) for r, (net, *_x) in built.items()}
    pairs = 0
    for r in REGIONS:
        for nb, se in ST.neighbours(r):
            if nb < r:
                continue
            ea, eb = ([e for e in ends[x] if ST.on_seam(e.xy, se)] for x in (r, nb))
            for a, b in ST.match(ea, eb):
                pairs += 1
                if a.blendable and b.blendable:
                    assert abs(a.hw - b.hw) < 1e-9, (r, nb, a.chain, a.hw, b.hw)
    assert pairs >= 20


def test_real_transitions_are_mirrored_and_reported(built):
    rows = {r: st["seam_tapers"] for r, (_n, _g, _o, st) in built.items()}
    n = 0
    for r, lst in rows.items():
        for t in lst:
            n += 1
            assert t["neighbour"] in rows and 0 < t["in_tile_m"] <= ST.MAX_LEN_M / 2
            twin = [x for x in rows[t["neighbour"]] if x["neighbour"] == r and x["width_seam"] == t["width_seam"]
                    and x["length_m"] == t["length_m"] and x["width_own"] == t["width_other"]]
            assert twin, (r, t)
    assert n % 2 == 0


def test_real_build_network_is_idempotent(built):
    r = next((x for x in REGIONS if built[x][3]["seam_tapers"]), REGIONS[0])
    net2, _g, _o, st2 = pipeline.build_network(r)
    assert st2["seam_tapers"] == built[r][3]["seam_tapers"]
    for c1, c2 in zip(built[r][0].chains, net2.chains):
        assert c1.id == c2.id and np.array_equal(c1.hw, c2.hw)


def test_real_no_taper_flag_gives_the_tile_on_its_own(built):
    r = next((x for x in REGIONS if any(not t.get("skipped") and t["width_own"] != t["width_seam"]
                                        for t in built[x][3]["seam_tapers"])), None)
    if r is None:
        pytest.skip("no carriageway transition in the data")
    net0, _g, _o, st0 = pipeline.build_network(r, seam_taper=False)
    assert st0["seam_tapers"] == []
    assert any(not np.array_equal(c1.hw, c2.hw) for c1, c2 in zip(built[r][0].chains, net0.chains))
