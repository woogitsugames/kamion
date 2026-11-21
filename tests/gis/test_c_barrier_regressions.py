"""C regeneration: continuous abutments and traced rails beside widened roads."""
from types import SimpleNamespace

import numpy as np
import pytest
from shapely.geometry import LineString, box

from roads import barrier_audit as BA
from roads.meshing import MeshBuf
from roads.network import BRIDGE, URBAN
from streetscape import furniture as FU

pytestmark = pytest.mark.unit


def _road(buf, bounds):
    x0, y0, x1, y1 = bounds
    v = np.array([[x0, y0, 0.], [x1, y0, 0.], [x1, y1, 0.], [x0, y1, 0.]])
    buf.add("road", "road_asphalt", v, v[:, :2], [[0, 1, 2], [0, 2, 3]], src="road")


def _authored(y):
    p = np.column_stack([np.arange(30.), np.full(30, y)])
    return dict(P=p, Z=np.zeros(30), key="authored:median", tall=np.zeros(30, bool),
                term=(False, True), dense=None, dark=None)


def test_traced_median_survives_small_road_widening_with_clear_hardware():
    buf = MeshBuf()
    _road(buf, (-10., -5., 40., 0.))
    q = [_authored(.36)]  # C: post .36 m from final road, envelope requires .47 m
    before = q[0]["P"].copy()
    FU._fit_authored_rails_to_pavement(q, buf.parts)
    FU._clip_rails_to_pavement(q, buf.parts)
    assert len(q) == 1 and len(q[0]["P"]) == 30
    assert np.linalg.norm(q[0]["P"] - before, axis=1).max() < .13
    assert LineString(q[0]["P"]).distance(box(-10., -5., 40., 0.)) >= .47
    assert q[0]["term"] == (False, True)


def test_traced_rail_cannot_be_fitted_into_median_narrower_than_hardware():
    buf = MeshBuf()
    _road(buf, (-10., -5., 40., 0.))
    _road(buf, (-10., .60, 40., 5.))
    q = [_authored(.30)]
    FU._fit_authored_rails_to_pavement(q, buf.parts)
    FU._clip_rails_to_pavement(q, buf.parts)
    assert not q


def test_pinned_separator_joint_follows_matching_deck_instead_of_other_traced_rail():
    traced = _authored(0.)
    traced["nojoin"] = {-1}
    traced["term"] = (True, False)
    other_trace = _authored(.25)  # nearer than the deck; historically the wrong join
    deck = dict(P=np.column_stack([np.arange(29.64, 50.64), np.full(21, -1.05)]),
                Z=np.full(21, -.22), key="c:deck:L:bridge", tall=np.ones(21, bool), term=(True, True))
    original = traced["P"].copy()
    FU._join_authored_deck_ends([traced, other_trace, deck])
    np.testing.assert_allclose(traced["P"][-1], deck["P"][0])
    assert traced["Z"][-1] == pytest.approx(deck["Z"][0])
    np.testing.assert_allclose(traced["P"][:-8], original[:-8])
    assert traced["term"] == (True, False) and deck["term"] == (False, True)
    np.testing.assert_allclose(other_trace["P"][:, 1], .25)


@pytest.mark.parametrize("height,reverse", [(2., False), (0., True)])
def test_pinned_joint_rejects_deck_at_wrong_level_or_direction(height, reverse):
    traced = _authored(0.)
    traced["nojoin"] = {-1}
    x = np.arange(30., 51.)
    if reverse:
        x = 60. - x
    deck = dict(P=np.column_stack([x, np.full(21, -.5)]), Z=np.full(21, height),
                key="c:deck:L:bridge", tall=np.ones(21, bool), term=(True, True))
    before = traced["P"].copy()
    FU._join_authored_deck_ends([traced, deck])
    np.testing.assert_allclose(traced["P"], before)


def test_underdeck_clearance_uses_the_generated_chamfered_collision():
    from qa import check_piers_vs_roads as K
    from streetscape import hero_bridge as H
    from shapely.geometry import MultiPoint
    params = dict(col_len_m=1., col_wid_m=1.2, col_chamfer_m=.25)
    centre, tangent = [12., -8.], np.array([.8, -.6])
    buf = MeshBuf()
    H._prism(buf, centre, tangent, .5, .6, .25, 0., 5., "pier_yellow", "column", collision=True)
    collision = next(p for p in buf.parts if p.layer == "collision")
    actual = MultiPoint(collision.V[:, :2]).convex_hull
    audited = K._footprint(centre, tangent, params)
    assert actual.symmetric_difference(audited).area < 1e-10
    assert len(audited.exterior.coords) == 9
    assert audited.area == pytest.approx(1.2 - 4 * .25 ** 2 / 2)


@pytest.mark.parametrize("cap_width", [.30, .40])
def test_narrowing_cap_keeps_barrier_connected_to_ground_approaches(monkeypatch, cap_width):
    stations = np.arange(60.)
    bridge = (stations >= 15) & (stations < 45)
    line = SimpleNamespace(offset_point=lambda s, o: np.column_stack([s, np.broadcast_to(o, np.shape(s))]))
    chain = SimpleNamespace(id="c:abutment", length=60., t_a=0., t_b=0., line=line,
                            bridge=bridge, edges=[], meta={},
                            idx=lambda s: np.asarray(s, int),
                            hw_at=lambda s: np.full(np.shape(s), 4.),
                            crossfall_z=lambda s, o: np.zeros(np.shape(s)))
    net = SimpleNamespace(chains=[chain], authored=[], overrides_applied=[], overrides_stale=[])
    monkeypatch.setattr(FU, "_structures", lambda net: [])
    monkeypatch.setattr(FU, "side_params", lambda c, side, s:
                        (BRIDGE, .15, cap_width, .60, 2) if 15 <= s < 45 else (URBAN, .15, 0., .2, 0))
    lin = FU.Lin(MeshBuf(), lambda e, n: np.zeros(np.shape(e)))
    report = {}
    FU.guardrails(lin, net, lambda e, n: np.zeros(np.shape(e)), report)
    runs = report["guardrail_runs"]
    assert len(runs) == 2
    assert all(any(p[3] for p in r["pts"]) for r in runs)
    assert all(not r["pts"][0][3] and not r["pts"][-1][3] for r in runs)
    assert not BA.find_free_ends(runs)
