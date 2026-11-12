"""ADR 0122: near steel rims must survive export with depth and both sides facing out."""
from collections import Counter

import numpy as np
import pytest

from streetscape import life_props as LP
from streetscape.export import crease_normals


CASES = [(0.535, 0.385, 10), (0.51, 0.32, 14), (0.51, 0.62, 14)]


def exported(radius, width, segments, side):
    mesh = LP.Mesh()
    LP.wheel(mesh, [0, 0, radius], radius, width, segments, out_sign=side)
    return {p['mat']: p for p in crease_normals(mesh.out())}


@pytest.mark.parametrize('radius,width,segments', CASES)
def test_near_rim_has_depth_without_expanding_tyre_and_is_mirrored(radius, width, segments):
    positive = exported(radius, width, segments, 1)
    negative = exported(radius, width, segments, -1)
    assert positive.keys() == negative.keys() == {'rim', 'tyre'}
    for side, parts in ((1, positive), (-1, negative)):
        vertices = np.concatenate([p['V'] for p in parts.values()])
        assert vertices[:, 2].min() >= -1e-6
        assert vertices[:, 2].max() <= 2 * radius + 1e-6
        assert np.max(np.abs(vertices[:, 0])) <= width / 2 + 0.020001
        depth = side * parts['rim']['V'][:, 0] - width / 2
        assert depth.max() - depth.min() > 0.07, 'A flat fan is not a recessed rim'
    for material, pos in positive.items():
        neg = negative[material]
        expected = np.concatenate([pos['V'] * [-1, 1, 1], pos['N'] * [-1, 1, 1]], axis=1)
        actual = np.concatenate([neg['V'], neg['N']], axis=1)
        # Post-crease corner positions/normals, independent of vertex numbering.
        assert Counter(map(tuple, np.round(expected, 5))) == Counter(map(tuple, np.round(actual, 5)))


@pytest.mark.parametrize('radius,width,segments', CASES)
@pytest.mark.parametrize('side', [-1, 1])
def test_dark_recess_backing_is_inside_the_rim_and_faces_the_observer(radius, width, segments, side):
    tyre = exported(radius, width, segments, side)['tyre']
    vertices, normals = tyre['V'], tyre['N']
    depth = side * vertices[:, 0] - width / 2
    radial = np.linalg.norm(vertices[:, [1, 2]] - [0, radius], axis=1)
    backing = (depth < -0.035) & (depth > -0.12) & (radial < radius * 0.62)
    assert np.any(backing), 'No dark surface at the bottom of the inset openings'
    assert np.all(side * normals[backing, 0] > 0.8), 'Mirrored recess backs must not be backface culled'
