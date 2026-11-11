"""Car deposition coordinates are a data addition, never a geometry rebuild."""
import numpy as np
import pytest

from streetscape import life_cars as cars
from streetscape.export import crease_normals
from streetscape.materials import M


@pytest.mark.parametrize('body', [*cars.CARS, 'van'])
@pytest.mark.parametrize('lod', [0, 1, 2])
def test_deposition_coordinates_preserve_shape_and_interpolate_affinely(body, lod):
    meshes = cars.van('white') if body == 'van' else cars.car(body, 'black')
    original = crease_normals(meshes[(0, 1, 3)[lod]].out())
    name = 'van_white' if body == 'van' else f'car_{body}_black'
    result = cars.paint_deposition(original, name)
    d = cars.VAN if body == 'van' else cars.CARS[body]
    rear = d['L'] / 2 - d['foh'] - d['wb']
    assert len(result) == len(original)
    paint = 0
    for before, after in zip(original, result):
        assert after['mat'] == before['mat']
        for key in ('V', 'N', 'T', 'UV'):
            assert np.array_equal(before[key], after[key]), key
        if not before['mat'].startswith('car_paint_'):
            assert 'UV1' not in after
            continue
        paint += 1
        uv = after['UV1']
        v = after['V']
        assert np.allclose(uv[:, 0], v[:, 2] - d['sill'])
        assert np.allclose(uv[:, 1], (v[:, 1] - rear) / d['wb'])
        # Include front/rear faces and large far-LOD triangles, not just side vertices.
        bary = np.array([.2, .3, .5])
        point = np.einsum('tvk,v->tk', v[after['T']], bary)
        interpolated = np.einsum('tvk,v->tk', uv[after['T']], bary)
        assert np.allclose(interpolated[:, 0], point[:, 2] - d['sill'])
        assert np.allclose(interpolated[:, 1], (point[:, 1] - rear) / d['wb'])
        half = np.einsum('tvk,v->tk', uv.astype(np.float16).astype(np.float32)[after['T']], bary)
        assert np.max(np.abs(half - interpolated)) < .001
    assert paint


def test_clean_set_only_routes_materials_with_instance_deposition():
    active = {name for name, definition in M.items() if name.startswith('car_paint_') and 'paint' in definition}
    assert len(active) == 7
    for name in active:
        assert M[name]['texture_set'] == 'car_grime_clean'
    for name in ('car_paint_green', 'car_paint_beige'):
        assert 'paint' not in M[name]
        assert M[name]['texture_set'] == 'car_grime'


def test_nonvehicle_export_adapter_leaves_primitives_unmodified():
    primitive = {'V': np.zeros((3, 3)), 'T': np.array([[0, 1, 2]]), 'UV': np.zeros((3, 2)), 'mat': 'steel'}
    original = [primitive]
    assert cars.paint_deposition(original, 'bench') is original
