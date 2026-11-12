"""ADR 0122: static yard vehicle silhouette and visible-wheel regressions."""
import numpy as np
import pytest
from streetscape import life_props as LP
from streetscape import life_cars as LC
from streetscape.export import crease_normals
from streetscape.materials import M


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
            assert M[p['mat']]['set_tile'] is True
        phases.append(float(uv[:, 0].min()))
    assert len(set(phases)) == len(LP.CURTAIN_COLOURS)


@pytest.mark.parametrize('colour', LP.TRACTOR_COLOURS)
def test_static_cab_deposition_survives_export_splitting_without_geometry_changes(colour):
    for mesh in LP.tractor(colour)[:2]:
        before = crease_normals(mesh.out())
        after = LC.paint_deposition(before, f'tractor_{colour}')
        for b, a in zip(before, after):
            for key in ('V', 'T', 'N', 'UV'):
                assert np.array_equal(b[key], a[key])
            if b['mat'].startswith('tractor_paint_'):
                v = a['V']
                assert np.allclose(a['UV'][:, 1], v[:, 2])
                # The frame uses actual cab bottom and both real axle stations,
                # not a generic passenger-car sill or a normalised texture UV.
                assert np.allclose(a['UV1'][:, 0], v[:, 2] - LP.TRACTOR_SILL_Z)
                assert np.allclose(a['UV1'][:, 1] * LP.TRACTOR['wb'] - LP.TRACTOR['fw_ahead'], v[:, 1])
                assert np.max(a['UV'][:, 1]) < 4.0
                assert M[b['mat']]['yard_paint'] is True
                assert M[b['mat']]['texture_set'] == 'car_grime_clean'
            else:
                assert 'UV1' not in a


def test_static_cab_adapter_does_not_add_payload_to_other_yard_objects():
    primitive = dict(mat='container_rust', V=np.array([[0., 0., 0.]]))
    assert LC.paint_deposition([primitive], 'container_20_rust')[0] is primitive
