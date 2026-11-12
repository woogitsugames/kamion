"""Candidate contract: real four-way fork openings, not painted dark slots.

Install as tests/gis/test_pallet_openings.py only with the chosen geometry.
Run that single file under heavy before the final GIS suite.
"""
import numpy as np
import pytest

from streetscape.life_props import pallets_empty


def triangles(mesh):
    parts = mesh.out()
    assert [p['mat'] for p in parts] == ['pallet_wood']
    p = parts[0]
    return p['V'][p['T']]


def ray_hits(tris, origin, direction, entering=False):
    """Two-sided Moller-Trumbore, independent of the model's construction."""
    edge1, edge2 = tris[:, 1]-tris[:, 0], tris[:, 2]-tris[:, 0]
    cross = np.cross(np.broadcast_to(direction, edge2.shape), edge2)
    determinant = np.einsum('ij,ij->i', edge1, cross)
    valid = abs(determinant) > 1e-10
    inv = np.zeros_like(determinant)
    inv[valid] = 1/determinant[valid]
    offset = np.asarray(origin)-tris[:, 0]
    u = np.einsum('ij,ij->i', offset, cross)*inv
    q = np.cross(offset, edge1)
    v = np.einsum('j,ij->i', direction, q)*inv
    distance = np.einsum('ij,ij->i', edge2, q)*inv
    hits = valid & (u >= -1e-8) & (v >= -1e-8) & (u+v <= 1+1e-8) & (distance > 0)
    if not np.any(hits):
        return False
    if not entering:
        return True
    first = np.flatnonzero(hits)[np.argmin(distance[hits])]
    return np.dot(np.cross(edge1[first], edge2[first]), direction) < -1e-10


@pytest.mark.parametrize('n', [4, 8, 12, 16])
@pytest.mark.parametrize('lod', [0, 1])
def test_four_way_fork_openings_and_load_bearing_blocks(n, lod):
    mesh = pallets_empty(n)[lod]
    tris = triangles(mesh)
    jitter = np.random.default_rng(n).uniform(-.03, .03, (n, 2))
    for layer, (dx, dy) in enumerate(jitter):
        z = layer*.144+.061
        # Both fork slots stay open all the way through, from either direction.
        for offset in (-.30, .30):
            for sign in (-1, 1):
                assert not ray_hits(tris, [dx+offset, dy-sign*2, z], [0, sign, 0]), (n, lod, layer, 'end')
        for offset in (-.16, .16):
            for sign in (-1, 1):
                assert not ray_hits(tris, [dx-sign*2, dy+offset, z], [sign, 0, 0]), (n, lod, layer, 'side')
        # A hollow shell with no support blocks must not pass the opening test.
        for sign in (-1, 1):
            assert ray_hits(tris, [dx, dy-sign*2, z], [0, sign, 0], entering=True)
            assert ray_hits(tris, [dx-sign*2, dy, z], [sign, 0, 0], entering=True)


@pytest.mark.parametrize('n', [4, 8, 12, 16])
def test_stack_envelope_collision_and_determinism(n):
    first = pallets_empty(n)
    second = pallets_empty(n)
    for lod in (0, 1):
        a, b = first[lod].out()[0], second[lod].out()[0]
        for key in ('V', 'T', 'UV'):
            np.testing.assert_array_equal(a[key], b[key])
        v = a['V']
        assert np.isfinite(v).all() and np.isfinite(a['UV']).all()
        assert v[:, 0].min() >= -.630001 and v[:, 0].max() <= .630001
        assert v[:, 1].min() >= -.430001 and v[:, 1].max() <= .430001
        assert v[:, 2].min() >= -1e-9 and abs(v[:, 2].max()-.144*n) <= .001001
        tri = triangles(first[lod])
        assert np.all(np.linalg.norm(np.cross(tri[:, 1]-tri[:, 0], tri[:, 2]-tri[:, 0]), axis=1) > 1e-10)
    assert len(first[1].out()[0]['T']) < len(first[0].out()[0]['T'])
    collision = first[2].out()
    assert len(collision) == 1 and collision[0]['mat'] == 'collision_steel'
    assert len(collision[0]['T']) == 12
    np.testing.assert_allclose(collision[0]['V'].min(0), [-.6, -.4, 0], atol=1e-12)
    np.testing.assert_allclose(collision[0]['V'].max(0), [.6, .4, .144*n], atol=1e-12)
