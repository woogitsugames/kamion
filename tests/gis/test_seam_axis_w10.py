"""seams-w10: the axis of a road cut by a tile seam meets in one point (roads/seam_taper.py, ADR 0275 extended).

Wave 10 seam report (artifacts/regen-wave-10-s24/seams_after.md): 9 FAIL `położenie osi na szwie` of 0.125 / 0.25 /
0.375 m = lanes x GAMEPLAY_LANE_WIDEN_M / 2. D94 (network.gameplay_widen) shifts a carriageway towards its greater
clearance, measured on this tile's piece of the edge only (a parallel road on one side of the seam), so the two halves
of one road were laid with different axes. Both tiles now move their axis half of the offset along the S-curve of the
width transition. Synthetic tile pairs (the helpers of test_seam_taper_0275) through the generator network code.
"""
import math
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from tools.worldgen.qa import seams as SM  # noqa: E402
from test_seam_taper_0275 import _tile, _nets, _seam_view  # noqa: E402

sys.path.insert(0, str(ROOT / "tools" / "worldgen"))
from roads import seam_taper as ST  # noqa: E402
from roads import standards as S  # noqa: E402

SET = {"width": 7.0, "edge_strip": 0.2, "edge_lines": "both"}


def _with_parallel(t, gap=0.0, width=5.0):
    """Adds a two-way service road beside the main road (north side), inside the tile and away from the seam: the
    D94 clearance of the main road on that side is `gap` minus the reserve (0 = no room)."""
    y = 50.0 + 0.5 * (float(SET["width"]) + width) + gap          # widening_clearance reads the widths before D94
    x0 = t.region["bbox"]["xmin"]
    na = {"id": f"{t.id}:p0", "x": x0 + 20.0, "y": y, "z_terrain": 120.0, "boundary": False, "degree": 1}
    nb = {"id": f"{t.id}:p1", "x": x0 + 80.0, "y": y, "z_terrain": 120.0, "boundary": False, "degree": 1}
    attrs = {"highway": {"v": "service", "src": "osm", "conf": "high"}, "lanes": {"v": 2, "src": "osm", "conf": "high"},
             "oneway": {"v": "no", "src": "default", "conf": "medium"}}
    t.graph["nodes"] += [na, nb]
    t.graph["edges"].append({"id": f"w99:{na['id']}-{nb['id']}", "from": na["id"], "to": nb["id"], "osm_way": 99,
                             "attrs": attrs, "length_m": 60.0,
                             "geometry": [[na["x"], y], [0.5 * (na["x"] + nb["x"]), y], [nb["x"], y]]})
    t.overrides.append({"id": "par", "target": {"osm_way": [99]}, "set": {"width": width}})
    return t


def _ends_on_seam(nets, x_seam=100.0):
    out = {}
    for k, net in nets.items():
        c, d, i = _seam_view(net, x_seam)
        out[k] = (c, d, i, c.line.p[i] + np.asarray(net.origin))
    return out


def _main_chain_net(net):
    """_seam_view looks at chains[0]: keep the main road (way 7) first."""
    net.chains.sort(key=lambda c: 0 if c.edges[0][0].startswith("w7:") else 1)
    return net


@pytest.fixture
def d94(monkeypatch):
    """The generator's D94 (tests/gis/conftest.py runs the GIS suite at 0 = measured cross-sections)."""
    monkeypatch.setattr(S, "GAMEPLAY_LANE_WIDEN_M", S.GAMEPLAY_LANE_WIDEN_DEFAULT_M)


def test_d94_shift_in_one_tile_meets_in_the_middle(d94):
    a = _with_parallel(_tile("a", 0.0, set_=SET))
    b = _tile("b", 100.0, set_=SET, from_seam=100.0)
    plain = {k: _main_chain_net(n) for k, n in _nets([a, b], taper=False).items()}
    nets = {k: _main_chain_net(n) for k, n in _nets([a, b]).items()}
    pa, pb = (_ends_on_seam(plain)[k][3] for k in ("synthetic-a", "synthetic-b"))
    # the bug: tile a shifts its axis away from the parallel road by lanes x 0.25 / 2, tile b does not
    off = 2 * S.GAMEPLAY_LANE_WIDEN_M / 2
    assert S.GAMEPLAY_LANE_WIDEN_M > 0
    assert abs(pa[1] - pb[1]) == pytest.approx(off, abs=1e-6)
    e = _ends_on_seam(nets)
    (ca, da, ia, qa), (cb, db, ib, qb) = e["synthetic-a"], e["synthetic-b"]
    assert np.hypot(*(qa - qb)) < 1e-6                                   # one axis on the seam
    assert qa[1] == pytest.approx(0.5 * (pa[1] + pb[1]), abs=1e-6)      # in the middle
    assert ca.hw[ia] == pytest.approx(cb.hw[ib], abs=1e-9)              # and one width (ADR 0275)
    # beyond half of the transition each tile keeps its own placement
    (t,) = nets["synthetic-a"].seam_tapers
    half = t.length / 2
    ya0 = plain["synthetic-a"].chains[0].line.p[:, 1]
    assert np.allclose(ca.line.p[da >= half, 1], ya0[da >= half], atol=1e-9)
    yb0 = plain["synthetic-b"].chains[0].line.p[:, 1]
    assert np.allclose(cb.line.p[db >= half, 1], yb0[db >= half], atol=1e-9)
    # smooth: one monotone S through the seam, the axis turns by at most 1.5 x offset / L per metre
    prof = np.concatenate([ca.line.p[np.argsort(-da), 1], cb.line.p[np.argsort(db), 1][1:]])
    dp = np.diff(prof)
    assert (dp * np.sign(prof[-1] - prof[0]) >= -1e-12).all()
    assert np.abs(dp).max() <= 1.5 * off / t.length * 0.5 + 1e-9         # stations 0.5 m apart
    # both reports carry the same offset; the axis offset counts in the length (edge skew stays 1:RATIO)
    (tb,) = nets["synthetic-b"].seam_tapers
    assert t.report()["axis_offset_m"] == tb.report()["axis_offset_m"] == pytest.approx(off, abs=1e-3)
    assert t.length == tb.length == pytest.approx(max(ST.MIN_LEN_M, ST.RATIO * off))
    assert np.allclose(t.shift_seam, -np.asarray(tb.shift_seam), atol=1e-12)          # half the vector each way


@pytest.mark.parametrize("b_kw", [{}, {"flip_way": True}, {"seam_last": True}, {"flip_way": True, "seam_last": True}])
def test_authored_offset_any_chain_direction(b_kw):
    """Different lateral placement on the two sides (here an authored ADR 0077 center_offset in tile a, 0.6 m: more
    than seam_taper.MATCH_M between the built axes - the ends pair up by the graph cut) meets on the seam whichever
    way the neighbour's way and chain run; the seam QA tool sees no axis FAIL."""
    a = _tile("a", 0.0, set_={**SET, "center_offset": 0.6})
    b = _tile("b", 100.0, set_=SET, from_seam=100.0, **b_kw)
    nets = _nets([a, b])
    e = _ends_on_seam(nets)
    qa, qb = e["synthetic-a"][3], e["synthetic-b"][3]
    assert np.hypot(*(qa - qb)) < 1e-6, b_kw
    assert qa[1] == pytest.approx(50.3, abs=1e-6) or qa[1] == pytest.approx(49.7, abs=1e-6)
    ts = [a, b]
    rep = SM.run(loaded=ts, base=None)
    rows = [r for s in rep["seams"] for rd in s["roads"] for r in rd["rows"] if r["param"].startswith("położenie osi")]
    assert rows and all(r["status"] == "OK" for r in rows), rows


def test_same_axis_is_untouched():
    a, b = _tile("a", 0.0, set_=SET), _tile("b", 100.0, set_=SET, from_seam=100.0)
    nets, plain = _nets([a, b]), _nets([a, b], taper=False)
    for k in nets:
        assert nets[k].seam_tapers == []
        assert np.array_equal(nets[k].chains[0].line.p, plain[k].chains[0].line.p)
        assert "center_offset" not in nets[k].chains[0].meta


def test_deterministic_and_independent_of_tile_order(d94):
    def mk():
        return [_with_parallel(_tile("a", 0.0, set_=SET)), _tile("b", 100.0, set_=SET, from_seam=100.0)]
    n1, n2 = _nets(mk()), _nets(list(reversed(mk())))
    for k in n1:
        for c1, c2 in zip(n1[k].chains, n2[k].chains):
            assert np.array_equal(c1.line.p, c2.line.p)
        assert [t.report() for t in n1[k].seam_tapers] == [t.report() for t in n2[k].seam_tapers]


# ------------------------------------------------------------------------------------------------ data in git
# Wave 10 FAIL `położenie osi na szwie` (artifacts/regen-wave-10-s24/seams_after.md): way -> offset of the two axes
# before the fix (both tiles' nominal ends, D94 at the generator default).
REAL = {("bialystok-kleeberga", "bialystok-knyszynska"): {76084085: 0.25, 261104557: 0.25, 281813932: 0.25},
        ("dk65-04", "dk65-05"): {249298671: 0.25},
        ("dk65-05", "dk65-06"): {1560819273: 0.25}}


@pytest.mark.parametrize("pair", sorted(REAL))
def test_real_wave10_axis_fails_meet_on_the_seam(pair, d94):
    a, b = pair
    if not all((ST.REGIONS / t / "roads.graph.json").exists() for t in pair):
        pytest.skip("region data missing")
    ts = [SM.load_tile(t) for t in pair]
    plain = {t.id: SM.build_plain(t) for t in ts}
    ends = {k: ST.ends(n) for k, n in plain.items()}
    se = ST.shared_edge(ts[0].bbox, ts[1].bbox)
    on = {k: [e for e in v if e.on_seam(se)] for k, v in ends.items()}
    before = {x.osm_way: math.hypot(x.xy[0] - y.xy[0], x.xy[1] - y.xy[1]) for x, y in ST.match(on[a], on[b])}
    for w, off in REAL[pair].items():
        assert before.get(w) == pytest.approx(off, abs=0.01), (pair, w, before.get(w))      # the wave 10 FAIL
    for k, other in ((a, b), (b, a)):
        plain[k].seam_tapers = ST.plan(ends[k], {other: on[other]})
        ST.apply_widths(plain[k], plain[k].seam_tapers)
    after_a, after_b = ([e for e in ST.ends(plain[k]) if e.on_seam(se)] for k in (a, b))
    got = {x.osm_way: (math.hypot(x.xy[0] - y.xy[0], x.xy[1] - y.xy[1]),
                       abs(x.hw - y.hw) if x.blendable and y.blendable else 0.0)
           for x, y in ST.match(after_a, after_b)}
    for w in REAL[pair]:
        assert got[w][0] <= 0.02 and got[w][1] < 1e-9, (pair, w, got[w])
    assert all(d <= SM.TOL_M for d, _ in got.values()), got                 # no axis FAIL left on the seam
