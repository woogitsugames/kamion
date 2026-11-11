"""ADR 0097 (zabudowa r5): multi-part roofs, one balustrade type per building, sill streaks, plinth drip, house
palette against the neighbours, door landing, calmer laundry."""
import sys
from pathlib import Path

import numpy as np
import pytest
import shapely
from shapely.geometry import Polygon, box

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "worldgen"))


def _tris(acc, mat, layer="buildings"):
    return sum(len(it[1]) for it in acc.d.get((layer, mat), []))


PROPS = {"roof_type_lod2": "1130", "height_lod2_2017_m": 8.0, "lod2_eave_rel_m": 4.0}


@pytest.mark.parametrize("plan", [
    [(0, 0), (12, 0), (12, 8), (6, 8), (6, 13), (0, 13)],                       # L, wing flush with a gable end
    [(0, 0), (12, 0), (12, 8), (8, 8), (8, 14), (2, 14), (2, 8), (0, 8)],      # T
])
def test_multi_roof_covers_the_plan_once_with_valleys(plan):
    """P1-c: an L / T plan gets one gable per part; the envelope covers the whole covering without gaps or double
    faces, the wing ridge stays below the main ridge, every wall top is >= the eave and the valleys get flashing."""
    from streetscape import buildings_mesh as B
    from streetscape import roofs as RF
    poly = Polygon(plan)
    r = RF.plan(poly, PROPS, 7.0, 100.0, lambda s: 0.9)
    assert isinstance(r, RF.MultiRoof) and len(r.parts) == 2
    assert r.zridge == pytest.approx(108.0, abs=1e-6)
    assert r.parts[1].zridge < r.parts[0].zridge - 0.29
    cov = RF.covering(poly, r)
    regs = [f[0] for f in r.faces(RF.OVERHANG + 0.05)]
    uni = shapely.unary_union(regs)
    assert cov.difference(uni).area < 1e-3
    assert sum(g.area for g in regs) - uni.area < 1e-3
    ring = np.asarray(poly.exterior.coords)
    for a, b in zip(ring[:-1], ring[1:]):
        prof = r.profile(a, b)
        assert min(z for _, z in prof) >= r.zeave - 1e-6
        assert prof[0][0] == 0.0 and prof[-1][0] == pytest.approx(float(np.hypot(*(b - a))))
    assert len(r.valley_lines(RF.OVERHANG)) == 2
    acc = B.Acc()
    RF.build(acc, r, poly, "roof_tiles_red", soffit_mat="soffit_boards", fascia_mat="soffit_boards")
    assert _tris(acc, "hall_flashing") == 8 and _tris(acc, "roof_tiles_red", "buildings_low") > 0


def test_rectangle_keeps_the_single_roof():
    from streetscape import roofs as RF
    r = RF.plan(box(0, 0, 12, 8), PROPS, 7.0, 100.0, lambda s: 0.9)
    assert isinstance(r, RF.Roof) and r.kind == "gable"


def test_balustrade_rows_one_type_per_group():
    """P1-b: every balcony row group shows one balf type; the default group of a building comes from its id."""
    from streetscape import facade_atlas as FA
    assert len(FA.BAL_GROUPS) == 3 and all(FA.is_bal(g) for g in FA.BAL_GROUPS)
    for g in FA.BAL_GROUPS:
        assert FA.bal_type(g) in FA.BAL_TYPES
        assert all(e[0] in ("bal", "w1", "w2") for row in FA.FAR_ROWS[g] for e in row)
    assert FA.far_groups("block", 4, balcony="balcony_6") == ["balcony_6"] * 4
    assert FA.far_groups("block", 4, balcony=True)[0] in FA.BAL_GROUPS
    assert len(FA.FAR_ORDER) == 16


def test_lod0_balconies_follow_the_building_type():
    from streetscape import buildings_mesh as B
    from streetscape import facade_atlas as FA
    vs = []
    for k in range(40):
        ops = B.facade_openings("block", 40.0, 100.0, 100.0 + 1.0 + 5 * 2.8 + 0.6, 5, f"b{k}:3", False, False,
                                {"balcony": "balcony_1", "basement": True}, sh=2.8, zbase=1.0)
        vs += [o[7] for o in ops if o[5] == "bdoor"]
    share = sum(v == 1 for v in vs) / len(vs)
    assert 0.80 <= share <= 0.95                     # 12 % exceptions (WORKING_VALUE)
    assert set(vs) - {1} <= set(B.BAL_EXCEPT)


def test_sill_streak_uv1_under_windows_only():
    """P1-a: the wall piece right under a window carries the sill mode of the run-off layer (v >= 64), the piers
    between windows do not."""
    from streetscape import buildings_mesh as B
    acc = B.Acc()
    ops = [(1.0, 2.5, 101.0, 102.4, 0.2, "window", "glass"), (4.0, 5.0, 100.0, 102.2, 0.15, "door", "glass")]
    B.wall_with_openings(acc, "buildings", "plaster_grey", np.array([0.0, 0.0]), np.array([1.0, 0.0]),
                         np.array([0.0, -1.0]), 6.0, 99.5, 103.0, ops, sills=(3.0, 0.7))
    items = acc.d[("buildings", "plaster_grey")]
    sill = [it for it in items if it[3] is not None and it[3][:, 1].min() >= 64.0]
    assert len(sill) == 1
    V = sill[0][0]
    assert V[:, 0].min() == pytest.approx(1.0) and V[:, 0].max() == pytest.approx(2.5) and V[:, 2].max() == pytest.approx(101.0)
    assert sill[0][3][:, 1].min() == pytest.approx(65.0) and sill[0][3][:, 1].max() == pytest.approx(65.0 + 1.5 / 0.7)


def test_plinth_drip_skips_the_door():
    from streetscape import buildings_mesh as B
    from streetscape import facade_kit as FK
    acc = B.Acc()
    FK.plinth_drip(acc, np.array([0.0, 0.0]), np.array([1.0, 0.0]), np.array([0.0, -1.0]), 10.0, 100.9,
                   [(4.0, 5.6, 100.15, 102.4, 0.15, "door", "x")])
    assert _tris(acc, "hall_flashing") == 8               # two runs x (front, underside)


def test_house_palette_differs_from_neighbours():
    from streetscape import buildings_mesh as B
    blds = [{"id": f"h{i}", "typ": "house", "poly": box(i * 15.0, 0, i * 15.0 + 9, 9)} for i in range(30)]
    pal = B.house_palette(blds)
    walls = [pal[f"h{i}"][0] for i in range(30)]
    roofs = [pal[f"h{i}"][1] for i in range(30)]
    assert all(walls[i] != walls[i + 1] for i in range(29))
    assert sum(roofs[i] == roofs[i + 1] for i in range(29)) <= 3
    warm = sum(w in ("plaster_cream", "plaster_beige") for w in walls)
    assert warm <= 0.5 * len(walls)
    assert set(walls) <= {m for m, *_ in B.HOUSE_TONES}


def test_door_landing_and_steps():
    from streetscape import buildings_mesh as B
    from streetscape import facade_kit as FK
    acc = B.Acc()
    FK.door_steps(acc, np.array([0.0, 0.0]), np.array([1.0, 0.0]), np.array([0.0, -1.0]), 3.0, 100.6, 100.0)
    # landing (4 faces) + 3 steps for 0.58 m of rise
    assert _tris(acc, "plinth_dark") == 8 + 3 * 8 and _tris(acc, "window_sill") == 4
    assert _tris(acc, "plinth_dark", "buildings_low") == 0


def test_wall_apron_drapes_on_the_terrain():
    from streetscape import buildings_mesh as B
    from streetscape import facade_kit as FK

    class HF:
        def sample(self, e, n):
            return 100.0 + 0.1 * np.asarray(e)
    acc = B.Acc()
    FK.wall_apron(acc, box(0, 0, 20, 10), HF())
    V = np.concatenate([it[0] for it in acc.d[("buildings", "sidewalk_paving")]])
    assert np.allclose(V[:, 2], 100.0 + 0.1 * V[:, 0] + 0.04)
    area = sum(0.5 * abs(np.cross(t[1] - t[0], t[2] - t[0])[2]) for it in acc.d[("buildings", "sidewalk_paving")]
               for t in it[0].reshape(-1, 3, 3) * np.array([1, 1, 0]))
    assert area == pytest.approx(box(0, 0, 20, 10).buffer(0.5, join_style="mitre").area - 200.0, rel=1e-3)
