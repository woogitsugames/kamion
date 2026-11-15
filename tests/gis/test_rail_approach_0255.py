"""ADR 0255: approach signs of level crossings (A-9 / A-10, G-1a...G-1f, "Sygnalizacja automatyczna", U-1a / U-1b).
Synthetic scenes only (no Data/raw): the crossing of tests/gis/test_rail_0217.py (rail along E at n = 500, road along N
at e = 500, 7 m carriageway)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
import shapely
from shapely.geometry import LineString

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "worldgen"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import test_rail_0217 as T  # noqa: E402

pytestmark = pytest.mark.unit


def _plan(road=((500.0, 0.0), (500.0, 1000.0)), speeds=(), overrides=(), tile=(0, 0, 1000, 1000), **kw):
    from roads.meshing import MeshBuf
    from streetscape import rail as RL
    road_line = LineString(road)
    p = RL.Plan(T._src(**kw), (0.0, 0.0), shapely.box(*tile), road_line.buffer(3.5, cap_style=2), [road_line],
                overrides=list(overrides), road_speeds=list(speeds))
    p.build(MeshBuf(), T.ground_at, T.road_z_at, log=lambda *a: None)
    return p


def _signs(p, approach=None, side=None):
    return [m for m in p.report["approach"] if m["kind"] == "approach_sign"
            and (approach is None or m["approach"] == approach) and (side is None or m["side"] == side)]


def _outer_rail(p):
    from streetscape import rail as RL
    t = p.tracks[0]
    return max(abs(o) for o in t.offsets) + t.gauge / 2 + RL.RAIL_HEAD_W / 2


# ------------------------------------------------------------------------------------------------ rules
@pytest.mark.parametrize("dev, cat, code, sa", [
    ({}, "D", "A-10", False),                                   # signs only
    ({"light": True}, "C", "A-10", True),                       # automatic signals, no barriers
    ({"barrier": "half", "light": True}, "B", "A-9", True),     # automatic half barriers
    ({"barrier": "double_half", "light": True}, "B", "A-9", True),
    ({"barrier": "full"}, "A", "A-9", False),                   # full barriers
])
def test_category_warning_sign_and_board(dev, cat, code, sa):
    """§ 6 ust. 1 (categories), § 79 pkt 1 lit. a (A-9 with barriers / A-10 without), pkt 6 (board before B and C)."""
    p = _plan(**dev)
    qa = p.report["approach_qa"]["crossings"][0]
    assert qa["category"] == cat and qa["warning"] == code
    first = [m for m in _signs(p) if m["dist_m"] == 150.0]
    assert len(first) == 2                                      # one per approach
    for m in first:
        assert m["parts"][0] == code and m["parts"][-1] == "G-1a"
        assert ("SA" in m["parts"]) is sa


def test_category_override_and_validation():
    from streetscape import rail as RL
    ov = [{"id": "c", "kind": "rail_crossing", "target": {"osm_node": 1}, "set": {"category": "C", "light": True}}]
    assert _plan(overrides=ov).report["approach_qa"]["crossings"][0]["category"] == "C"
    assert {"category", "approach_kmh", "left_side", "approach_signs"} <= set(RL.OVERRIDE_KEYS)
    with pytest.raises(ValueError):
        _plan(overrides=[{"id": "c", "kind": "rail_crossing", "target": {"osm_node": 1}, "set": {"category": "Z"}}])


@pytest.mark.parametrize("cls, avail, expect, left", [
    ("fast", 400.0, [(150.0, 3, True), (100.0, 2, False), (50.0, 1, False)], False),
    ("fast", 120.0, [(120.0, 2, True), (60.0, 1, False)], False),
    ("fast", 70.0, [(70.0, 1, True)], True),
    ("fast", 30.0, [], False),
    ("slow", 80.0, [(60.0, 3, True), (40.0, 2, False), (20.0, 1, False)], False),
    ("slow", 50.0, [(50.0, 2, True), (25.0, 1, False)], False),
    ("slow", 25.0, [(25.0, 1, True)], True),
])
def test_layout_follows_table_2_2(cls, avail, expect, left):
    """Dz.U. 2019 poz. 2311 zał. 1 pkt 2.2.10: G-1a under the sign, G-1b at 2/3, G-1c at 1/3; shorter approaches use
    columns II / III (G-1b + G-1c at half; G-1c under the sign + the same on the left)."""
    from streetscape import rail_approach as RA
    posts, variant, left_too = RA.layout(avail, cls)
    assert [(pytest.approx(d), n, w) for d, n, w in expect] == posts and left_too is left
    cols = RA.TABLE_2_2[cls]
    if variant == "I":                                          # every post inside its column of Tabela 2.2
        for (d, n, _), (lo, hi) in zip(posts, cols):
            assert lo <= d <= hi, (d, n)


# ------------------------------------------------------------------------------------------------ geometry
def test_positions_headings_and_distances():
    from streetscape import rail as RL
    p = _plan(barrier="no")
    rail = _outer_rail(p)
    for a, sgn in ((1, -1.0), (-1, 1.0)):                       # +1: northbound (comes from n < 500)
        ss = sorted(_signs(p, a), key=lambda m: -m["dist_m"])
        assert [m["parts"] for m in ss] == [["A-10", "G-1a"], ["G-1b"], ["G-1c"]]
        for m in ss:
            assert m["side"] == "R"
            assert m["e"] == pytest.approx(500.0 - sgn * (3.5 + RL.SIGN_LATERAL))      # right of the driver
            assert m["n"] == pytest.approx(500.0 + sgn * (rail + m["dist_m"]), abs=0.02)
            assert m["heading_deg"] == (180.0 if a == 1 else 0.0)                     # face looks at the driver
            assert m["z"] == pytest.approx(T.road_z_at(np.array([m["e"]]), np.array([m["n"]]))[0], abs=1e-3)
    assert p.report["approach_qa"]["min_track_distance_m"] > RL.CLEARANCE_HALF


def test_guide_posts_u1():
    """§ 79 pkt 5 lit. a: no barriers -> 4 m from the outer rails, every 3 m, 15-20 m, both sides; lit. b: outside the
    barriers."""
    from streetscape import rail as RL
    from streetscape import rail_approach as RA
    p = _plan(barrier="no")
    u = [m for m in p.report["approach"] if m["kind"] == "delineator"]
    assert len(u) == 2 * 2 * 5                                  # 2 approaches x 2 verges x posts at 4, 7, 10, 13, 16 m
    assert sorted({m["dist_m"] for m in u}) == [4.0, 7.0, 10.0, 13.0, 16.0]
    assert {m["code"] for m in u if m["side"] == "R"} == {"U-1a"} and {m["code"] for m in u if m["side"] == "L"} == {"U-1b"}
    assert max(m["dist_m"] for m in u) <= 20.0 and RA.U1_SPAN_M >= 15.0
    pb = _plan(barrier="half")
    ub = [m for m in pb.report["approach"] if m["kind"] == "delineator"]
    c = pb.crossings[0]
    barrier_from_rail = c["half_track"] / c["sin"] + RL.BARRIER_SETBACK - _outer_rail(pb)
    assert min(m["dist_m"] for m in ub) == pytest.approx(barrier_from_rail + RA.U1_AFTER_BARRIER_M, abs=0.01)


def test_speed_from_road_line_and_override():
    slow = _plan(speeds=[50.0])
    qa = slow.report["approach_qa"]["crossings"][0]
    assert qa["speed_class"] == "slow" and qa["kmh"] == 50.0 and qa["kmh_src"] == "osm maxspeed"
    assert max(m["dist_m"] for m in _signs(slow)) == 60.0
    fast = _plan()                                               # no maxspeed: over 60 km/h (rural default)
    assert fast.report["approach_qa"]["crossings"][0]["speed_class"] == "fast"
    ov = [{"id": "s", "kind": "rail_crossing", "target": {"osm_node": 1}, "set": {"approach_kmh": 40}}]
    assert _plan(speeds=[90.0], overrides=ov).report["approach_qa"]["crossings"][0]["kmh_src"] == "override"


def test_short_approach_and_tile_edge():
    """Road line ends 80 m south of the rails (junction): column III on that side -> G-1c under the sign, repeated with
    G-1f on the left; the north approach is unchanged. A tile cut at n = 400 drops the far posts and reports them."""
    p = _plan(road=((500.0, 420.0), (500.0, 1000.0)))
    south = _signs(p, 1)
    assert sorted((m["side"], tuple(m["parts"])) for m in south) == [("L", ("A-10", "G-1f")), ("R", ("A-10", "G-1c"))]
    assert all(m["dist_m"] == pytest.approx(80.0 - _outer_rail(p) - 5.0, abs=0.01) for m in south)
    assert len(_signs(p, -1)) == 3
    q = _plan(tile=(0, 400, 1000, 1000))
    assert len(_signs(q, 1)) == 0 and len(_signs(q, -1)) == 3     # the 50 m G-1c (n ~ 449) never stands alone
    assert any("outside the tile" in s for s in q.report["approach_qa"]["crossings"][0]["skipped"])


def test_left_side_and_switch_off():
    ov = [{"id": "l", "kind": "rail_crossing", "target": {"osm_node": 1}, "set": {"left_side": True}}]
    left = [m for m in _signs(_plan(overrides=ov)) if m["side"] == "L"]
    assert sorted(m["parts"][-1] for m in left) == ["G-1d", "G-1d", "G-1e", "G-1e", "G-1f", "G-1f"]
    off = [{"id": "o", "kind": "rail_crossing", "target": {"osm_node": 1}, "set": {"approach_signs": False}}]
    p = _plan(overrides=off)
    assert p.report["approach"] == [] and p.report["approach_qa"]["crossings"][0]["skipped"]


# ------------------------------------------------------------------------------------------------ faces + instances
def test_faces_dimensions_and_stripes():
    from streetscape import gate3_landmarks as G3
    from streetscape import rail_signs as RS
    assert G3.FACE_DIM["A-9"][1] == G3.FACE_DIM["A-10"][1] == 0.90               # Tabela 1.1, group S
    for k in ("G-1a", "G-1b", "G-1c", "G-1d", "G-1e", "G-1f"):
        assert G3.FACE_DIM[k] == ("rect", 0.30, 1.00)                              # rys. 9.8.1-9.8.6
        im = RS.draw(k, 126, 420, G3._fit_text)
        col = [im.getpixel((63, y))[1] < 100 for y in range(12, 408)]              # red runs inside the edge
        runs = sum(1 for i in range(1, len(col)) if col[i] and not col[i - 1]) + (1 if col[0] else 0)
        assert runs == RS.G1[k][0], k
        left_low = RS.G1[k][1] == "R"                                              # stripes fall towards the road
        y_l = next(y for y in range(408, 0, -1) if im.getpixel((10, y))[1] < 100 and y < 405)
        y_r = next(y for y in range(408, 0, -1) if im.getpixel((115, y))[1] < 100 and y < 405)
        assert (y_l > y_r) is left_low, k
    for code in ("A-9", "A-10", "SA"):
        w, h = int(G3.FACE_DIM[code][1] * 420), int(G3.FACE_DIM[code][2] * 420)
        assert G3.draw_face(code, w, h).size == (w, h)


def test_place_approach_instances_and_budget():
    from streetscape import rail_props as RP
    from streetscape.materials import M
    p = _plan(barrier="half", light=True)
    RP.PROTOS.clear()
    pl, rep, boards = T._Placer(), {}, {}
    n_dev = RP.place(pl, p, T.road_z_at, rep)
    n = RP.place_approach(pl, p, T.road_z_at, rep, boards)
    assert n == len(p.report["approach"]) == 6 + 20
    assert rep["rail_approach_devices"] == {"A-9+SA+G-1a": 2, "G-1b": 2, "G-1c": 2, "U-1a": 10, "U-1b": 10}
    assert len(pl.items) == n_dev + n
    signs = {k: v for k, v in RP.prototypes().items() if k.startswith("sign_g3_")}
    assert len(signs) == 3 and len(boards) == 3                  # one prototype + one face atlas per distinct set
    tris = {}
    for name, (lod0, lod1, col) in RP.prototypes().items():
        if name.startswith("sign_g3_"):
            assert len({q["mat"] for q in lod0.out()}) == 1      # one material = one draw per sign
        else:
            assert {q["mat"] for q in lod0.out()} <= set(M) and col is not None
        tris[name] = sum(len(q["T"]) for q in lod0.out())
    # LoD0 triangles of the whole approach set of one crossing (budget, ADR 0255): 2 x (A-9 set + G-1b + G-1c) + 20 posts
    per = {it["p"]: tris[it["p"]] for it in pl.items if it["p"] in tris}
    total = sum(per[it["p"]] for it in pl.items if it["p"] in per and it["src"].startswith("rail:approach"))
    assert total < 2500, total
    RP.PROTOS.clear()
