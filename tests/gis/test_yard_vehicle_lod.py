"""ADR 0122: static yard vehicle silhouette and visible-wheel regressions."""
import numpy as np
import pytest
from streetscape import life_props as LP


@pytest.mark.parametrize('kind,colour', [('curtain','grey'), ('box',None), ('reefer',None)])
def test_trailer_distant_wheels_have_real_axle_gaps_and_ground_contact(kind, colour):
    mesh = LP.trailer(kind, colour)[1]
    tyre = next(p for p in mesh.out() if p['mat'] == 'tyre')
    v, t = tyre['V'], tyre['T']
    assert -1e-6 <= v[:, 2].min() < 0.01
    for side in (-1, 1):
        faces = v[t[np.all(side * v[t, 0] > 0, axis=1)]]
        assert len(faces)
        # A tyre must occupy every axle, with empty space across each midpoint.
        for axle in LP.TRAILER_AXLES:
            assert np.any(np.abs(faces[:, :, 1] - axle) < 1e-5)
        for a, b in zip(LP.TRAILER_AXLES, LP.TRAILER_AXLES[1:]):
            midpoint = (a + b) / 2
            assert not np.any((faces[:, :, 1].min(axis=1) < midpoint) &
                              (faces[:, :, 1].max(axis=1) > midpoint))


def test_tractor_distant_tyres_have_visible_outer_faces():
    tyre = next(p for p in LP.tractor('blue')[1].out() if p['mat'] == 'tyre')
    faces = tyre['V'][tyre['T']]
    normals = np.cross(faces[:, 1] - faces[:, 0], faces[:, 2] - faces[:, 0])
    for side in (-1, 1):
        outer = np.all(side * faces[:, :, 0] > 0, axis=1)
        # Open tread tubes only have radial normals: their side view is a hole.
        assert np.any(outer & (side * normals[:, 0] > 0.01))


def test_curtain_road_grime_stays_in_one_vertical_tile_and_varies_by_fleet():
    phases = []
    for colour in LP.CURTAIN_COLOURS:
        for mesh in LP.trailer('curtain', colour)[:2]:
            p = next(p for p in mesh.out() if p['mat'].startswith('trailer_curtain_'))
            uv, vertices = p['UV'], p['V']
            assert 0 <= uv[:, 1].min() < uv[:, 1].max() < 2.7
            assert np.isclose(np.ptp(uv[:, 1]), np.ptp(vertices[:, 2]))
        phases.append(float(uv[:, 0].min()))
    assert len(set(phases)) == len(LP.CURTAIN_COLOURS)
