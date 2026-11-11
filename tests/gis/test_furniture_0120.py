"""Regression cases from the HIL review: metre-high plinth and steel-like concrete pole."""
import numpy as np
from shapely.geometry import LineString

from streetscape import furniture as F, props as P


class Buffer:
    def __init__(self):
        self.parts = []

    def add(self, layer, mat, V, UV, T, **kwargs):
        self.parts.append((layer, mat, np.asarray(V), np.asarray(T)))


def test_steep_plot_fence_does_not_turn_into_a_metre_high_retaining_wall():
    buf = Buffer()
    lin = F.Lin(buf, lambda e, n: 0.4 * e)
    F.panel_fence(lin, LineString([(0, 0), (10, 0)]), 'fence_green', 'review-I1')
    boards = [v for layer, mat, v, t in buf.parts if mat == 'concrete_plinth']
    # 20 cm board plus at most 25 cm step; this is an explicit visual design budget.
    assert max(np.max(v[:, 2] - 0.4*v[:, 0]) for v in boards) <= 0.46
    assert {mat for layer, mat, v, t in buf.parts if layer == 'furniture'} == {
        'concrete_plinth', 'fence_green', 'fence_green_mesh'}


def test_old_concrete_column_keeps_its_taper_on_both_render_lods():
    for mesh in P.lamp_old(9, 'concrete')[:2]:
        body = next(p for p in mesh.out() if p['mat'] == 'furniture_concrete')
        v = body['V']
        foot = v[np.isclose(v[:, 2], 0)]
        top = v[np.isclose(v[:, 2], 9)]
        foot_r = np.max(np.linalg.norm(foot[:, :2], axis=1))
        top_r = np.max(np.linalg.norm(top[:, :2], axis=1))
        assert 0.145 <= foot_r <= 0.155
        assert 0.065 <= top_r <= 0.075
        assert foot_r / top_r > 2
