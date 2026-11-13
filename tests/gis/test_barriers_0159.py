"""ADR 0159: barrier terminals, dark deck barrier, dense ground posts, no_guardrail zones, audit of ends led onto a
rail, screen / pier / block-wall materials. Unit tests on synthetic geometry and on the tracked region files."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

from conftest import REGION_ID
from roads import barrier_audit as BA
from roads import standards as S
from roads.meshing import MeshBuf
from streetscape import furniture as FU
from streetscape import materials as MT

ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.unit


class _Lin(FU.Lin):
    def __init__(self, z0=0.0):
        super().__init__(MeshBuf(), lambda e, n: np.full(len(np.atleast_1d(e)), z0))


def _rail(n, ground=10.0, **kw):
    lin = _Lin(ground)
    P = np.column_stack([np.arange(n, dtype=float), np.zeros(n)])
    FU.guardrail(lin, P, np.full(n, 10.0), kw.pop("key", "c:test:R:embankment"), **kw)
    return lin.buf.parts


def _beam(parts, mat="barrier_steel"):
    return [p for p in parts if p.mat == mat and p.layer in ("furniture", "bridge")
            and abs(float(p.UV[:, 1].max()) - FU._w_unrolled()[0]) < 1e-6 and float(p.UV[:, 1].min()) == 0.0]


def test_short_run_gets_short_terminals_instead_of_ends_in_the_air():
    """A 10 m run (too short for two 4 m terminals) used to keep both ends at full height."""
    parts = _rail(10, term=(True, True))
    b = _beam(parts)[0]
    z = b.V[:, 2] - 10.0
    ends = b.V[(b.V[:, 0] < 0.5) | (b.V[:, 0] > 8.5)]
    assert np.isclose(z.max(), S.GUARDRAIL_H)
    assert np.isclose((ends[:, 2] - 10.0).max(), S.GUARDRAIL_TERMINAL_END_TOP)
    assert (ends[:, 2] - 10.0).min() < 0.0                      # the section at the end is sunk below the foot line


def test_terminal_follows_ground_that_lies_lower_than_the_foot_line():
    """482392: a run on a kerb whose verge falls away - the terminal end goes down with the ground (capped)."""
    def end_top(ground):
        b = _beam(_rail(30, ground=ground, term=(True, True)))[0]
        e = b.V[b.V[:, 0] < 0.5]
        return float(e[:, 2].max())
    assert np.isclose(end_top(10.0), 10.0 + S.GUARDRAIL_TERMINAL_END_TOP)
    assert np.isclose(end_top(9.6), 9.6 + S.GUARDRAIL_TERMINAL_END_TOP)
    assert np.isclose(end_top(5.0), 10.0 - FU.TERMINAL_GROUND_DROP_M + S.GUARDRAIL_TERMINAL_END_TOP)   # capped
    # the full-height part of the run is not lowered
    b = _beam(_rail(30, ground=9.6, term=(True, True)))[0]
    assert np.isclose(b.V[:, 2].max(), 10.0 + S.GUARDRAIL_H)


def test_dense_ground_posts_every_two_metres():
    def posts(parts):         # web part of the posts: 8 vertices per post, drawn from both sides (4 triangles)
        w = [p for p in parts if p.mat == "barrier_steel" and len(p.T) == len(p.V) // 2 and len(p.V) % 8 == 0
             and float(np.ptp(p.V[:, 2])) > 0.6 and not _beam([p])]
        return min(len(p.V) // 8 for p in w)
    n = 41
    sparse = posts(_rail(n, term=(False, False)))
    dense = posts(_rail(n, term=(False, False), dense=np.ones(n, bool)))
    assert sparse == round(40 / S.GUARDRAIL_POST_SPACING_GROUND) + 1
    assert dense == round(40 / S.GUARDRAIL_POST_SPACING) + 1


def test_dark_deck_barrier_is_painted_and_closed_under_the_beam():
    n = 40
    tall = np.ones(n, bool)
    plain = _rail(n, key="c:test:R:bridge", tall=tall)
    dark = _rail(n, key="c:test:R:bridge", tall=tall, dark=tall)
    assert not any(p.mat == FU.DARK_BARRIER_MAT for p in plain)
    vis = [p for p in dark if p.layer == "bridge"]
    assert vis and all(p.mat == FU.DARK_BARRIER_MAT for p in vis)          # no galvanised part left on the deck run
    # flat rails under the W-beam: the widest open slot between the cap and the beam bottom is under 0.10 m
    zs = sorted([0.0] + [z for r in FU.DARK_BARRIER_RAILS for z in r] + [S.GUARDRAIL_H - 0.31])
    slots = [b - a for a, b in zip(zs[0::2], zs[1::2])]
    assert max(slots) <= 0.10
    # the collision face is the same with and without the paint
    c0 = [p for p in plain if p.layer == "collision"][0]
    c1 = [p for p in dark if p.layer == "collision"][0]
    assert np.allclose(c0.V, c1.V)
    tri = lambda parts: sum(len(p.T) for p in parts if p.layer != "collision")   # noqa: E731
    assert tri(dark) - tri(plain) <= 8 * len(FU.DARK_BARRIER_RAILS) * 4          # straight run: a few quads only


def test_end_led_onto_another_rail_is_not_a_free_end():
    a = {"key": "a", "pts": np.column_stack([np.arange(30.0), np.zeros(30), np.full(30, 5.0), np.ones(30)])}
    # b ends ON the body of a (x = 15), far from both ends of a
    b = {"key": "b", "pts": np.column_stack([np.full(10, 15.0), np.arange(9.0, -1.0, -1.0) * 0.5 + 0.2, np.full(10, 5.0),
                                             np.ones(10)])}
    free = BA.find_free_ends([a, b])
    assert {(f["key"], f["end"]) for f in free} == {("a", "start"), ("a", "end"), ("b", "start")}
    # ... but not when the other rail passes at another level (a deck over a ground rail)
    b2 = {"key": "b", "pts": b["pts"].copy()}
    b2["pts"][:, 2] = 9.0
    assert ("b", "end") in {(f["key"], f["end"]) for f in BA.find_free_ends([a, b2])}


def test_region_has_no_free_deck_ends():
    assert BA.analyze_region(REGION_ID)["deck_run_ends_free"] == 0


def _overrides():
    return yaml.safe_load((ROOT / "Data/Regions" / REGION_ID / "overrides.yaml").read_text(encoding="utf-8"))["overrides"]


def test_authored_zones_and_median_rail():
    ov = {o["id"]: o for o in _overrides()}
    for k in ("andersa-link-no-guardrail", "andersa-se-cyclepath-no-guardrail"):
        assert ov[k]["kind"] == "no_guardrail" and len(ov[k]["polygon_en"]) >= 3 and "Mapillary" in ov[k]["reason"]
    # after4: the zone on the SW edge of the median was wrong (810896 / 962702: a W-beam right behind the kerb)
    assert "andersa-se-ramp-median-sw-no-guardrail" not in ov
    r = ov["andersa-se-ramp-median-barrier"]
    assert r["kind"] == "guardrail" and r["post_spacing_m"] == 2.0 and r["free_ends"] == [False, True]
    q = np.asarray(r["polyline_en"], float)
    assert 95.0 < float(np.hypot(*(q[-1] - q[0]))) < 105.0
    st = next(o for o in _overrides() if o["id"] == "andersa-viaduct-putry-style")["set"]
    assert st["barrier"] == "dark_rails"


def _left_normal_side(q, target):
    """True when `target` lies on the LEFT normal side of polyline q at its nearest vertex (= the beam face)."""
    q = np.asarray(q, float)
    k = int(np.hypot(*(q - np.asarray(target, float)).T).argmin())
    k = min(max(k, 1), len(q) - 1)
    d = q[k] - q[k - 1]
    n = np.array([-d[1], d[0]])
    return float(n @ (np.asarray(target, float) - q[k])) > 0.0


def test_beam_face_is_on_the_left_normal_of_the_point_order():
    lin = _Lin(0.0)
    n = 30
    FU.guardrail(lin, np.column_stack([np.arange(n, dtype=float), np.zeros(n)]), np.zeros(n), "c:test:R:embankment")
    beam = _beam([p for p in lin.buf.parts if p.layer != "collision"])[0]
    posts = [p for p in lin.buf.parts if p.layer != "collision" and float(np.ptp(p.V[:, 2])) > 0.6]
    assert beam.V[:, 1].min() > 0.0 and min(float(p.V[:, 1].min()) for p in posts) < 0.0


def test_median_rails_face_their_carriageways():
    """after4: the NE rail faced the grass (drawn from the nose with "the road on the right")."""
    ov = {o["id"]: o for o in _overrides()}
    # a point on the NW-bound carriageway (NE of the median) / on the SE-bound one (SW of it), mid-way along the rails
    assert _left_normal_side(ov["andersa-se-ramp-median-barrier"]["polyline_en"], (-341.0, -146.5))
    sw = ov["andersa-se-ramp-median-sw-barrier"]
    assert sw["kind"] == "guardrail" and sw["post_spacing_m"] == 2.0 and sw["free_ends"] == [True, False]
    assert _left_normal_side(sw["polyline_en"], (-350.0, -156.0))
    q = np.asarray(sw["polyline_en"], float)
    assert 90.0 < float(np.hypot(*np.diff(q, axis=0).T).sum()) < 102.0
    ext = ov["biezenstwa-link-barrier-se-end"]
    assert ext["free_ends"] == [False, True] and _left_normal_side(ext["polyline_en"], (522.0, -678.0))
    q = np.asarray(ext["polyline_en"], float)
    assert float(np.hypot(*np.diff(q, axis=0).T).sum()) >= 13.0          # long enough for a 4 m terminal


def test_generated_runs_respect_the_zones():
    """On the regenerated world: no rule run inside the zones, both median rails reach the nose, the rule run of the
    SW cap is back and the link barrier at Rondo Biezenstwa ends where the orthophoto has it."""
    from shapely.geometry import Polygon
    p = ROOT / "Data/Regions" / REGION_ID / "generated/streetscape_qa.json"
    q = json.loads(p.read_text(encoding="utf-8"))["furniture"]
    runs = {}
    for r in q.get("guardrail_runs", []):
        runs.setdefault(r["key"], []).append(np.asarray(r["pts"], float))
    if "authored:andersa-se-ramp-median-sw-barrier" not in runs:
        pytest.skip("world not regenerated with ADR 0159 after4 yet")
    ov = {o["id"]: o for o in _overrides()}
    zones = [Polygon(ov[k]["polygon_en"]) for k in ("andersa-link-no-guardrail", "andersa-se-cyclepath-no-guardrail")]
    import shapely
    for key, parts in runs.items():
        if key.startswith("authored:"):
            continue
        for P in parts:
            for z in zones:
                assert not shapely.contains_xy(z, P[:, 0], P[:, 1]).any(), key
    assert q["guardrails_m"]["no_guardrail"] >= 60
    for key in ("authored:andersa-se-ramp-median-barrier", "authored:andersa-se-ramp-median-sw-barrier"):
        assert sum(len(P) for P in runs[key]) >= 90, key
    # the rule run of the SW cap of the ramp (removed by the zone of the first three builds) reaches the fill end again
    cap = [P for k, v in runs.items() if k.startswith("c:w173956078") and k.endswith(":L:bridge") for P in v]
    assert cap and min(float(np.hypot(*(P[:, :2] - [-383.65, -126.28]).T).min()) for P in cap) < 1.5
    end = runs["authored:biezenstwa-link-barrier-se-end"][-1][-1]
    assert float(np.hypot(end[0] - 528.05, end[1] + 686.07)) < 0.6


def test_screen_and_pier_materials():
    assert max(MT.M["noise_post"]["color"]) <= 0.07                         # dark paint, not pale mint (0.17-0.21)
    lines, strength, duty = MT.M["noise_glass_lined"]["screen"]["stripe"]
    assert strength <= 0.12                                                  # faint lines: no raster on Low
    c = MT.M["pier_yellow"]["color"]
    assert c[0] > c[1] > 2 * c[2] and 0.2 <= c[0] <= 0.3                     # still ochre, in the shade of the deck
    pm = MT.M["ramp_wall_panels"]                                            # after4: Biezenstwa ramps, not blocks
    assert pm["texture_set"] == "concrete_panels_wall" and pm.get("set_tile") is True
    assert min(pm["color"]) > max(MT.M["ramp_wall_blocks"]["color"])        # lighter than the split blocks
    bz = next(o for o in _overrides() if o["id"] == "andersa-viaduct-biezenstwa-style")["set"]
    assert bz["wall_mat"] == "ramp_wall_panels"
    m = MT.M["ramp_wall_blocks"]
    assert m["texture_set"] == "concrete_blocks_split" and m.get("set_tile") is True
    sys.path.insert(0, str(ROOT / "art-source/world/materials/_src"))
    import sets_facade as F
    reg = next(v for v in vars(F).values() if isinstance(v, dict) and "concrete_blocks_split" in v and "brick" in v)
    assert reg["concrete_blocks_split"]["tile_m"] == [2.0, 1.0]
    s = F.concrete_blocks_split(256)
    alb = np.asarray(s.albedo if hasattr(s, "albedo") else s.alb, float).mean(-1)
    joint = np.asarray(s.joint, float)
    assert alb[joint > 0.9].mean() <= 0.75 * alb[joint < 0.05].mean()        # joints at least 25 % darker than blocks
    assert reg["concrete_panels_wall"]["tile_m"] == [3.0, 3.0]
    s2 = F.concrete_panels_wall(256)
    alb2 = np.asarray(s2.albedo if hasattr(s2, "albedo") else s2.alb, float).mean(-1)
    j2 = np.asarray(s2.joint, float)
    assert 0.01 < float((j2 > 0.5).mean()) < 0.08                            # thin joints, large panels
    assert alb2[j2 < 0.05].std() < alb[joint < 0.05].std()                   # smooth face: less contrast than the blocks
