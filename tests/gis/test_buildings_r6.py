"""ADR 0107 (zabudowa r6): MultiRoof domains / lean-to annexes / step walls, balcony slab tone."""
import sys
from pathlib import Path

import numpy as np
import pytest
import shapely
from shapely.geometry import Polygon

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "worldgen"))

PROPS = {"roof_type_lod2": "1130", "height_lod2_2017_m": 8.0, "lod2_eave_rel_m": 4.0}
# the r13_house2 plan (bdot ...C793): 9 x 9 m body with two small annexes on its gable ends
HOUSE2 = [(4.6, -4.58), (4.59, 2.33), (6.88, 2.34), (6.88, 4.25), (4.59, 4.24), (4.59, 4.59), (-6.86, 4.59),
          (-6.88, 1.37), (-4.49, 1.39), (-4.45, -4.59)]


def _tris(acc, mat, layer="buildings"):
    return sum(len(it[1]) for it in acc.d.get((layer, mat), []))


def test_small_annexes_are_lean_tos_and_do_not_step_the_main_slope():
    """Review 0097 P1-g: an annexe on a gable end is one lean-to plane falling away from the gable wall; its plane
    does not reach into the main body's rectangle (r5: a step with a vertical board in the main slope)."""
    from streetscape import roofs as RF
    poly = Polygon(HOUSE2)
    r = RF.plan(poly, PROPS, 7.0, 100.0, lambda s: 0.9)
    assert isinstance(r, RF.MultiRoof) and len(r.parts) == 3
    assert [p.kind for p in r.parts] == ["gable", "mono", "mono"]
    main = r.parts[0]
    fc, fu, fv = r.frame
    m = r.rects[0]
    # the field over the main rectangle is the main gable everywhere (sampled 5 cm inside its edges)
    us, vs = np.meshgrid(np.linspace(m[0] + 0.05, m[1] - 0.05, 40), np.linspace(m[2] + 0.05, m[3] - 0.05, 40))
    q = fc + us[..., None] * fu + vs[..., None] * fv
    assert np.allclose(r.z(q), main.z(q), atol=1e-6)
    for lean in r.parts[1:]:
        assert lean.zridge <= main.zridge - 1.0                       # high edge well below the main ridge
        assert lean.zeave >= r.zeave - RF.LEAN_DROP_GABLE - 1e-6       # its eave at most 0.35 m under the main eave
        assert RF.LEAN_SLOPE[0] - 1e-9 <= lean.s <= RF.LEAN_SLOPE[1] + 1e-9
    cov = RF.covering(poly, r)
    regs = [f[0] for f in r.faces(RF.OVERHANG + 0.05)]
    uni = shapely.unary_union(regs)
    assert cov.difference(uni).area < 1e-3 and sum(g.area for g in regs) - uni.area < 1e-3
    assert len(r.ridge_lines(RF.OVERHANG)) == 1                        # lean-tos have no ridge cap


def test_steps_between_parts_are_closed_by_walls():
    """Review 0097 P1-g: no see-through slit where a lower roof meets a gable wall - a wall face from the lower
    covering up to the upper one, facing the lower roof."""
    from streetscape import buildings_mesh as B
    from streetscape import roofs as RF
    poly = Polygon(HOUSE2)
    r = RF.plan(poly, PROPS, 7.0, 100.0, lambda s: 0.9)
    steps = r.step_walls(RF.OVERHANG)
    assert len(steps) >= 2
    for q0, q1, lo, hi, n in steps:
        assert hi[0] >= lo[0] and hi[1] >= lo[1] and max(hi[0] - lo[0], hi[1] - lo[1]) > 0.03
        mid = 0.5 * (q0 + q1)
        assert float(r.z(mid + n * 0.06)) <= float(r.z(mid - n * 0.06))     # n points at the lower roof
    acc = B.Acc()
    RF.build(acc, r, poly, "roof_tiles_red", soffit_mat="soffit_boards", fascia_mat="soffit_boards",
             step_mat="plaster_grey")
    assert _tris(acc, "plaster_grey") >= 2 * 2
    assert not r.valley_lines(RF.OVERHANG)                             # steps are not valleys: no flashing strip on them


def test_wing_on_the_eave_side_keeps_its_gable_and_valleys():
    from streetscape import roofs as RF
    poly = Polygon([(0, 0), (12, 0), (12, 8), (8, 8), (8, 14), (2, 14), (2, 8), (0, 8)])
    r = RF.plan(poly, PROPS, 7.0, 100.0, lambda s: 0.9)
    assert [p.kind for p in r.parts] == ["gable", "gable"] and len(r.valley_lines(RF.OVERHANG)) == 2


def test_shallow_bay_on_the_eave_side_continues_the_main_slope():
    """A bay 1.1 m deep on the long side: the main slope runs on over it (no kink, no gable of its own)."""
    from streetscape import roofs as RF
    poly = Polygon([(0, 0), (4, 0), (4, -1.1), (8, -1.1), (8, 0), (12, 0), (12, 8), (0, 8)])
    r = RF.plan(poly, PROPS, 7.0, 100.0, lambda s: 0.9)
    assert isinstance(r, RF.MultiRoof) and r.parts[1].kind == "mono"
    s_main = r.parts[0].s
    assert r.parts[1].s == pytest.approx(min(s_main, RF.LEAN_DROP_EAVE / 1.1))
    assert float(r.z(np.array([6.0, -0.001]))) == pytest.approx(r.zeave, abs=0.01)


def test_balcony_slab_reads_as_painted_soffit():
    """Review 0097 P1-e: slab albedo >= 0.35 and no halving of the ambient of its underside."""
    from streetscape import materials as M
    s = M.M["balcony_slab"]
    assert min(s["color"]) >= 0.35 and s["sky_occ"] == [0.0, 0.0]


def test_tall_plinth_gets_joints_but_not_across_openings():
    """Review 0097 P2-k: a plinth standing > 0.9 m out of the slope carries a band joint and vertical joints; a low
    plinth and the span of a basement door carry none."""
    from streetscape import buildings_mesh as B
    from streetscape import facade_kit as FK
    a, d, n = np.array([0.0, 0.0]), np.array([1.0, 0.0]), np.array([0.0, -1.0])
    acc = B.Acc()
    assert FK.plinth_joints(acc, a, d, n, 12.0, 100.3, 99.0, [], lambda u: 100.0, 0.5) == 0     # 0.3 m plinth
    acc = B.Acc()
    nt = FK.plinth_joints(acc, a, d, n, 12.0, 102.0, 99.0, [], lambda u: 100.0, 0.5)
    assert nt >= 2 * 4 + 2 * 4 and _tris(acc, "hall_flashing") == nt
    acc2 = B.Acc()
    door = [(0.0, 12.0, 100.0, 102.0, 0.1, "door", "x")]
    assert FK.plinth_joints(acc2, a, d, n, 12.0, 102.0, 99.0, door, lambda u: 100.0, 0.5) == 0
    V = np.concatenate([it[0] for it in acc.d[("buildings", "hall_flashing")]])
    assert V[:, 2].max() <= 102.0 - FK.PLINTH_BAND_M + 0.01 and V[:, 1].max() < 0      # in front of the wall (n = -y)


# ---------------------------------------------------------------------------------------------- plots (P1-h)
def _plot_scene():
    from shapely.geometry import box
    road = box(-100, -6, 100, 0)                               # street along x, houses north of it
    houses = [{"id": f"h{k}", "poly": box(20 * k, 6, 20 * k + 10, 14)} for k in range(4)]
    return road, houses


def test_plots_are_deterministic_disjoint_and_face_the_road():
    from streetscape import plots as PL
    road, houses = _plot_scene()
    p1 = PL.plan(houses, road, [], [])
    p2 = PL.plan(houses, road, [], [])
    assert len(p1) == 4 and [p["poly"].wkt for p in p1] == [p["poly"].wkt for p in p2]
    for i, p in enumerate(p1):
        assert p["front"] @ np.array([0.0, -1.0]) > 0.99                    # the street side
        assert p["poly"].distance(road) >= PL.ROAD_CLEAR_M - 1e-6
        assert p["poly"].contains(houses[i]["poly"])
        assert p["poly"].area >= PL.MIN_AREA_RATIO * 80.0
        for q in p1[i + 1:]:
            assert p["poly"].intersection(q["poly"]).area < 0.3
    assert len({p["front_style"] for p in p1} | {p["side_style"] for p in p1}) >= 2      # not one fence for all


def test_plot_layout_has_gate_wicket_drive_and_closed_fence():
    from streetscape import plots as PL
    road, houses = _plot_scene()
    plots = PL.plan(houses, road, [], [])
    near = PL._Near()
    total = 0
    for p in plots:
        lay = PL.layout(p, road.buffer(0.3), near)
        near.add(lay["segs"])
        assert lay["gate"] is not None and lay["wicket"] is not None
        assert lay["gate"][2] @ p["front"] > 0.99
        assert [d[0] for d in lay["drive"]] == ["in", "out"]
        # bays + gate + wicket cover the outline (minus what a neighbour's parallel fence already closes)
        length = sum(float(np.hypot(*(b[4] - b[3]))) for b in lay["bays"]) + PL.GATE_SLOT_M + PL.WICKET_SLOT_M
        assert length <= p["poly"].length + 4 * PL.MODULE_M    # overlap of the pushed-back bays only
        total += length / p["poly"].length
        names = {b[0] for b in lay["bays"]}
        assert names <= set(PL.protos())
    assert total / len(plots) > 0.7


def test_plot_shrinks_to_an_existing_fence_and_does_not_double_it():
    from shapely.geometry import LineString, box
    from streetscape import plots as PL
    road = box(-100, -6, 100, 0)
    house = [{"id": "h0", "poly": box(0, 6, 10, 14)}]
    fence = LineString([(12.5, 0), (12.5, 40)])               # a real fence 2.5 m east of the house
    p = PL.plan(house, road, [], [fence])[0]
    assert p["poly"].bounds[2] <= 12.5 - 0.4
    near = PL._Near()
    near.add(PL._segments(fence))
    lay = PL.layout(p, road.buffer(0.3), near)
    east = [b for b in lay["bays"] if abs(b[2][0] - 1.0) < 1e-6]         # bays facing east
    assert not [b for b in east if abs(b[1][0] - 12.5) < PL.PARALLEL_SKIP_M]


def test_terrace_gets_a_wicket_per_house():
    from shapely.geometry import box
    from streetscape import plots as PL
    road = box(-100, -6, 100, 0)
    row = [{"id": f"t{k}", "poly": box(7 * k, 6, 7 * k + 7, 14)} for k in range(4)]
    plots = PL.plan(row, road, [], [])
    assert len(plots) == 1 and len(plots[0]["houses"]) == 4
    lay = PL.layout(plots[0], road.buffer(0.3), PL._Near())
    assert lay["gate"] is None and len(lay["wickets"]) == 4 and not lay["drive"]


def test_plot_prototypes_are_small_and_use_existing_materials():
    from streetscape import materials as M
    from streetscape import plots as PL
    P = PL.protos()
    assert len(P) == 19 and not [k for k in P if k.endswith('_h') and 'concrete' not in k]
    for name, (lod0, lod1, col) in P.items():
        t0 = sum(len(p["T"]) for p in lod0.out())
        t1 = sum(len(p["T"]) for p in lod1.out())
        assert t1 <= t0 and t0 <= 420, (name, t0, t1)
        assert len(lod0.out()) <= 2 and {p["mat"] for p in lod0.out()} <= set(M.M), name
        assert col is None


def test_rectangular_plots_close_with_whole_bays():
    """Budget: one bay prototype per fence type - a clean rectangular plot is a whole number of 2.5 m modules and the
    gate group sits on the module, so mesh / panel / picket runs need no half bay and overlap nothing."""
    from streetscape import plots as PL
    road, houses = _plot_scene()
    plots = PL.plan(houses, road, [], [])
    for p in plots:
        x0, y0, x1, y1 = p["poly"].bounds
        assert (x1 - x0) / PL.MODULE_M == pytest.approx(round((x1 - x0) / PL.MODULE_M), abs=1e-6)
        assert (y1 - y0) / PL.MODULE_M == pytest.approx(round((y1 - y0) / PL.MODULE_M), abs=1e-6)
        lay = PL.layout(p, None, None)
        g, w = lay["gate"][1], lay["wicket"][1]
        assert float(np.hypot(*(g - w))) == pytest.approx((PL.GATE_SLOT_M + PL.WICKET_SLOT_M) / 2)
        front = [b for b in lay["bays"] if b[2] @ p["front"] > 0.7 and "concrete" not in b[0]]
        if front:
            mids = sorted(float(b[1][0]) for b in front)
            assert all(abs((b_ - a_) / PL.MODULE_M - round((b_ - a_) / PL.MODULE_M)) < 1e-6 for a_, b_ in zip(mids, mids[1:]))


def test_roof_faces_keep_their_own_plane_on_a_step_line():
    """r1 of ADR 0107: covering / soffit vertices on the line between a lean-to and the gable above it took the
    envelope height (the higher roof) - roof- and soffit-coloured sails standing on the annexe. Every covering and
    soffit triangle lies in a roof plane (never steeper than 60 deg), and the annexe walls stay under the lean-to."""
    from streetscape import buildings_mesh as B
    from streetscape import roofs as RF
    poly = Polygon(HOUSE2)
    r = RF.plan(poly, PROPS, 7.0, 100.0, lambda s: 0.9)
    acc = B.Acc()
    RF.build(acc, r, poly, "roof_tiles_red", soffit_mat="soffit_boards", fascia_mat="hall_flashing", step_mat="plaster_grey")
    for mat in ("roof_tiles_red", "soffit_boards"):
        for it in acc.d[("buildings", mat)]:
            V, T = np.asarray(it[0]), np.asarray(it[1])
            for t in T:
                tri = V[t]
                nrm = np.cross(tri[1] - tri[0], tri[2] - tri[0])
                area = np.linalg.norm(nrm) / 2
                if area > 0.05 and not (mat == "roof_tiles_red" and area < 1.0 and abs(tri[:, 2].max() - r.zridge) < 0.5):
                    assert abs(nrm[2]) / (2 * area) > 0.5, (mat, tri)          # ridge cap facets excepted
    ring = np.asarray(poly.exterior.coords)
    lean_top = max(p.zridge for p in r.parts[1:])
    for a, b in zip(ring[:-1], ring[1:]):
        m = 0.5 * (a + b)
        if any(r._inside(k, m) for k in (1, 2)) and not r._inside(0, m):
            assert max(z for _, z in r.profile(a, b)) <= lean_top + 0.01
