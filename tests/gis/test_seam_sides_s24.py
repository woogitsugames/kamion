"""seams-side-s24: the side profile of a road cut by a tile seam is agreed between the two tiles (roads/seam_taper.py,
ADR 0275 extended).

Wave 10 seam report after the axis fix (artifacts/seams-w10-s24/seams_after_fix.md): 7 FAIL `pobocze L/P` (+ one
`krawędź asfaltu`) at bialystok-kleeberga | bialystok-maczka and bialystok-industrial-c | bialystok-maczka. The side
kind is decided per tile from data clipped to the bbox (osm_context footways, BDOT10k paths and yards) and from the
tile's own junction trims, so the two halves of one road met as kerb | flat edge, kerb | kerb + sidewalk or rural
shoulder | flat kerb. Both tiles now compute both nominal ends with the same code from the same data in git and impose
the higher-ranked profile (constrained > sidewalk > flat > kerb > rural) on their own end, over at most SIDE_HOLD_M.
"""
import itertools
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from tools.worldgen.qa import seams as SM  # noqa: E402
from test_seam_taper_0275 import _tile, _seam_view  # noqa: E402

sys.path.insert(0, str(ROOT / "tools" / "worldgen"))
from roads import network as Nw  # noqa: E402
from roads import seam_taper as ST  # noqa: E402
from roads import standards as S  # noqa: E402

SET = {"width": 7.0, "edge_strip": 0.2, "edge_lines": "both"}


def _nets(ts, taper=True):
    """The QA build of the generator: seam transitions + second assign_sides pass (what pipeline.build meshes)."""
    return SM.build_nets(ts, SM.adjacent_pairs(ts), taper=taper, trims=True)


def _footway(t, y, x0=None, x1=None):
    """A footway along the road (y = const) over [x0, x1] of the tile: osm_context clipped to the tile bbox."""
    bx0, bx1 = t.region["bbox"]["xmin"], t.region["bbox"]["xmax"]
    x0, x1 = bx0 if x0 is None else x0, bx1 if x1 is None else x1
    t.ctx = {"points": [], "footways": [{"highway": "footway", "geometry": [[x0, y], [0.5 * (x0 + x1), y], [x1, y]]}]}
    return t


def _pair_with_clipped_footway():
    """Footway north of the road in tile a only (its continuation in tile b was clipped away)."""
    y = 50.0 + 0.5 * SET["width"] + S.KERB_TOP_W + 1.1
    a = _footway(_tile("a", 0.0, set_=SET), y)
    b = _tile("b", 100.0, set_=SET, from_seam=100.0)
    b.ctx = {"points": [], "footways": []}
    return [a, b]


def _cat(net, side, x_seam=100.0):
    c, d, i = _seam_view(net, x_seam)
    return ST.side_cat(c.side[side], i), c, d


def _north(c):
    """Chain side ("L" / "R") that faces north (y+)."""
    return "L" if c.line.n[0][1] > 0 else "R"


# ------------------------------------------------------------------------------------------------ rule
def _sv(cat, w=0.0):
    kind = Nw.RURAL if cat == "rural" else Nw.URBAN
    h = 0.0 if cat == "flat" else S.KERB_HEIGHT
    mat = Nw.MAT_FLUSH_ROAD if cat == "constrained" else (1 if cat == "sidewalk" else 0)
    return ST.SideVal(cat=cat, kind=kind, h=h, w=w, depth=S.FLANGE_DEPTH, mat=mat, walk=cat == "sidewalk", verge=0.0)


VALS = [_sv("rural"), _sv("kerb"), _sv("flat"), _sv("sidewalk", 2.0), _sv("sidewalk", 2.5), _sv("constrained"),
        ST.SideVal(cat="other", kind=Nw.MEDIAN_RURAL, h=0.6, w=0.0, depth=0.5, mat=0, walk=False, verge=0.0), None]


def test_agree_is_symmetric_and_ranked():
    for a, b in itertools.product(VALS, VALS):
        assert ST.agree(a, b) == ST.agree(b, a), (a, b)
    assert ST.agree(_sv("kerb"), _sv("flat")).cat == "flat"
    assert ST.agree(_sv("rural"), _sv("flat")).cat == "flat"                 # kleeberga | maczka w257355872
    assert ST.agree(_sv("kerb"), _sv("sidewalk", 2.0)).cat == "sidewalk"     # industrial-c | maczka w606396470
    assert ST.agree(_sv("sidewalk", 2.0), _sv("sidewalk", 2.5)).w == 2.5
    assert ST.agree(_sv("constrained"), _sv("sidewalk", 2.0)).cat == "constrained"
    assert ST.agree(_sv("constrained"), _sv("constrained")) is None          # both locked: nothing to impose
    assert ST.agree(VALS[-2], _sv("kerb")) is None and ST.agree(None, _sv("kerb")) is None


# ------------------------------------------------------------------------------------------------ synthetic pair
def test_clipped_footway_sidewalk_meets_on_the_seam():
    ts = _pair_with_clipped_footway()
    plain = _nets(ts, taper=False)                 # the tiles on their own (QA build without seam agreement)
    ca = plain["synthetic-a"].chains[0]
    side_a = _north(ca)
    assert _cat(plain["synthetic-a"], side_a)[0] == "sidewalk"
    cb = plain["synthetic-b"].chains[0]
    assert _cat(plain["synthetic-b"], _north(cb))[0] == "rural"               # the bug: one tile without it

    nets = _nets(_pair_with_clipped_footway())
    cat_a, ca, da = _cat(nets["synthetic-a"], side_a)
    side_b = _north(nets["synthetic-b"].chains[0])
    cat_b, cb, db = _cat(nets["synthetic-b"], side_b)
    assert cat_a == cat_b == "sidewalk"
    # tile b holds the sidewalk for SIDE_HOLD_M, then its own rural profile again; tile a is untouched
    sb = cb.side[side_b]
    near, far = db <= ST.SIDE_HOLD_M - 0.5, db > ST.SIDE_HOLD_M + 0.5
    assert (np.asarray(sb["kind"])[near] == Nw.URBAN).all() and np.asarray(sb["walk"])[near].all()
    assert (np.asarray(sb["kind"])[far] == Nw.RURAL).all()
    pa = plain["synthetic-a"].chains[0].side[side_a]
    assert np.array_equal(np.asarray(ca.side[side_a]["kind"]), np.asarray(pa["kind"]))
    rep = [r for r in nets["synthetic-b"].seam_sides_report if r["own"] != r["other"]]
    assert len(rep) == 1 and rep[0]["seam"] == "sidewalk" and rep[0]["own"] == "rural"
    assert 0 < rep[0]["applied_m"] <= ST.SIDE_HOLD_M
    assert all(r.get("applied_m", 0) == 0 for r in nets["synthetic-a"].seam_sides_report)


def test_qa_reports_no_side_fail_after_agreement():
    rep = SM.run(loaded=_pair_with_clipped_footway(), base=None)
    rows = [r for s in rep["seams"] for rd in s["roads"] for r in rd["rows"]]
    side = [r for r in rows if r["param"].startswith(("pobocze", "krawędź asfaltu"))]
    assert side and all(r["status"] != "FAIL" for r in side), [r for r in side if r["status"] == "FAIL"]
    before = SM.run(loaded=_pair_with_clipped_footway(), base=None, taper=False)
    assert any(r["status"] == "FAIL" and r["param"].startswith("pobocze")
               for s in before["seams"] for rd in s["roads"] for r in rd["rows"])


def test_deterministic_and_independent_of_tile_order():
    n1, n2 = _nets(_pair_with_clipped_footway()), _nets(list(reversed(_pair_with_clipped_footway())))
    for k in n1:
        assert n1[k].seam_sides_report == n2[k].seam_sides_report
        for c1, c2 in zip(n1[k].chains, n2[k].chains):
            for s in ("L", "R"):
                for key in ("kind", "mat", "walk"):
                    assert np.array_equal(np.asarray(c1.side[s][key]), np.asarray(c2.side[s][key]))


def test_constrained_own_end_is_never_overridden():
    nets = _nets(_pair_with_clipped_footway())
    net = nets["synthetic-b"]
    c = net.chains[0]
    side = _north(c)
    # rebuild b's side from scratch, mark the seam stations as tight (another carriageway at the edge)
    plain = _nets(_pair_with_clipped_footway(), taper=False)["synthetic-b"]
    pc = plain.chains[0]
    d = pc.side[side]
    _c, dist, i = _seam_view(plain)
    d["tight"] = np.asarray(dist) <= 5.0
    fix = [f for f in net.seam_sides if f.side == side][0]
    f2 = ST.SideFix(chain=pc.id, end=fix.end, side=side, want=fix.want, own=fix.own, other=fix.other)
    kind0 = np.asarray(d["kind"]).copy()
    ST.apply_sides(plain, [f2])
    assert f2.kept == "own end is constrained" and np.array_equal(np.asarray(d["kind"]), kind0)


def test_equal_sides_are_untouched():
    a = _tile("a", 0.0, set_=SET)
    b = _tile("b", 100.0, set_=SET, from_seam=100.0)
    nets, plain = _nets([a, b]), _nets([_tile("a", 0.0, set_=SET), _tile("b", 100.0, set_=SET, from_seam=100.0)],
                                       taper=False)
    for k in nets:
        assert all(r["applied_m"] == 0 and "kept" not in r for r in nets[k].seam_sides_report)
        for s in ("L", "R"):
            assert np.array_equal(np.asarray(nets[k].chains[0].side[s]["kind"]),
                                  np.asarray(plain[k].chains[0].side[s]["kind"]))


# ------------------------------------------------------------------------------------------------ data in git
# The 7 FAIL rows of artifacts/seams-w10-s24/seams_after_fix.md (pair -> OSM ways).
REAL = {("bialystok-industrial-c", "bialystok-maczka"): {606396470},
        ("bialystok-kleeberga", "bialystok-maczka"): {257355872, 227027719, 25899482, 25899483, 305072031}}


@pytest.fixture(scope="module")
def real():
    tiles = sorted({t for p in REAL for t in p})
    if not all((ST.REGIONS / t / "roads.graph.json").exists() for t in tiles):
        pytest.skip("region data missing")
    return SM.run(tiles, base=None)


@pytest.mark.parametrize("pair", sorted(REAL))
def test_real_side_fails_agree_on_the_seam(real, pair):
    s = next(x for x in real["seams"] if (x["a"], x["b"]) == pair)
    roads = {rd["osm_way"]: rd for rd in s["roads"]}
    for w in REAL[pair]:
        rows = [r for r in roads[w]["rows"] if r["param"].startswith(("pobocze", "krawędź asfaltu"))]
        assert rows and all(r["status"] != "FAIL" for r in rows), (pair, w, [r for r in rows if r["status"] == "FAIL"])
    assert s["fail"] == 0, [(rd["osm_way"], r["param"]) for rd in s["roads"] for r in rd["rows"] if r["status"] == "FAIL"]


def test_real_generator_and_qa_agree(real):
    """pipeline.build's planner (ST.plan_sides_region: every tile reads the neighbours' files) gives the same fixes
    as the QA tool for these tiles."""
    for tid in ("bialystok-kleeberga", "bialystok-industrial-c"):
        fixes = ST.plan_sides_region(tid)
        mine = [(f.chain, f.end, f.side, f.want.cat) for f in fixes if f.neighbour == "bialystok-maczka"]
        assert mine, tid
