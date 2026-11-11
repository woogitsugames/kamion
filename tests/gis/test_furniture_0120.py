"""Regression cases from the HIL review: metre-high plinth and steel-like concrete pole."""
import numpy as np
from shapely.geometry import LineString
import pytest

from streetscape import furniture as F, props as P
from streetscape import signs as SG
from roads import standards as S


class Buffer:
    def __init__(self):
        self.parts = []
        self.colors = []

    def add(self, layer, mat, V, UV, T, **kwargs):
        self.parts.append((layer, mat, np.asarray(V), np.asarray(T)))
        self.colors.append(kwargs.get('COL'))


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


def test_short_steep_fence_edge_still_steps_instead_of_forming_a_tall_plinth():
    buf = Buffer()
    lin = F.Lin(buf, lambda e, n: e)
    F.panel_fence(lin, LineString([(0, 0), (0.30, 0)]), 'fence_green', 'short-bank')
    boards = [v for layer, mat, v, t in buf.parts if mat == 'concrete_plinth']
    assert max(np.max(v[:, 2]-v[:, 0]) for v in boards) <= 0.46


def test_only_our_boards_receive_byte_stable_detail_markers_and_ground_height():
    buf = Buffer()
    lin = F.Lin(buf, lambda e, n: .4*e)
    lin.posts('barrier_post', np.array([[0., 3.], [2., 3.]]), None, .06, .04, 1)
    protected = buf.parts[0][2].copy()
    F.panel_fence(lin, LineString([(0,0), (2,0)]), 'fence_green', 'marked-board')
    assert np.array_equal(buf.parts[0][2], protected) and buf.colors[0] is None
    for (layer, mat, v, t), colors in zip(buf.parts, buf.colors):
        if mat != 'concrete_plinth':
            assert colors is None
            continue
        packed = np.round(colors*255).astype(np.uint8)
        assert np.all(packed[:,2] == 64) and np.all(packed[:,3] == 128)
        decoded = packed[:,1]/255-.25
        expected = v[:,2]-.4*v[:,0]
        assert np.max(np.abs(decoded-expected)) <= 1/255


@pytest.mark.parametrize('code', ['A-7', 'C-12', 'B-20', 'D-1', 'D-6'])
def test_sign_back_and_folded_rim_never_wrap_the_wear_atlas(code):
    for mesh in P.plate(code)[:2]:
        uv = next(p['UV'] for p in mesh.out() if p['mat'] == 'plate_back')
        assert np.all(uv >= 0) and np.all(uv <= 1)


@pytest.mark.parametrize('code', ['A-7', 'C-12'])
def test_rust_runoff_is_registered_below_the_actual_steel_mounts(code):
    back = next(p for p in P.plate(code)[0].out() if p['mat'] == 'plate_back')
    # Recover the affine XZ -> UV mapping from the exported plate geometry, not the author's UV formula.
    xyz = back['V'][:3]
    basis = np.column_stack([xyz[:, 0], xyz[:, 2], np.ones(3)])
    mapping = np.linalg.solve(basis, back['UV'][:3])
    shape, _ = SG.face(code)
    height = S.SIGN_SIZE[shape] * (np.sqrt(3)/2 if shape == 'triangle' else 1)
    texture = np.asarray(SG.plate_back().convert('RGB'), dtype=float)
    for z in (-0.28*height, 0.22*height):
        for x in (-0.04, 0.04):
            u, v = np.array([x, z-0.025, 1]) @ mapping
            red, green, blue = texture[round((1-v)*(len(texture)-1)), round(u*(texture.shape[1]-1))]
            assert red-blue > 25  # local warm transfer below the mount, not a neutral-grey plate sample
