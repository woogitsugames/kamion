"""Plate migration preserves legacy geometry/UV0 and needs no additional channel."""
import numpy as np
import pytest
from streetscape import life_cars as cars
from streetscape.export import crease_normals

FLEET = [(body, color) for body in cars.CARS for color in cars.CAR_COLOURS]
FLEET += [('van', color) for color in cars.VAN_COLOURS]


@pytest.mark.parametrize('body,color', FLEET)
def test_all_27_fleet_prototypes_preserve_legacy_binding_and_add_four_corners(body, color):
    meshes = cars.van(color) if body == 'van' else cars.car(body, color)
    name = f'van_{color}' if body == 'van' else f'car_{body}_{color}'
    seen = 0
    for lod, mesh in enumerate((meshes[0], meshes[1], meshes[3])):
        before = crease_normals(mesh.out())
        after = cars.paint_deposition(before, name)
        # Existing paint payload already requires Half2 on every car LOD; no new channel.
        assert any(p['mat'].startswith('car_paint_') and 'UV1' in p for p in after)
        plates = [p for p in after if p['mat'] == 'car_plate']
        assert len(plates) == (0 if lod == 2 else 1)
        for a, b in zip(before, after):
            assert a['mat'] == b['mat']
            for key in ('V', 'N', 'T', 'UV'):
                assert np.array_equal(a[key], b[key]), (name, lod, key)
        for plate in plates:
            assert len(plate['V']) == 8 and plate['T'].size == 12
            corners, count = np.unique(plate['UV1'], axis=0, return_counts=True)
            assert np.array_equal(corners, [[0, 0], [0, 1], [1, 0], [1, 1]])
            assert np.array_equal(count, [2, 2, 2, 2])
            uv = plate['UV']
            restored = uv.min(axis=0) + plate['UV1'] * np.ptp(uv, axis=0)
            assert np.allclose(uv, restored, atol=1e-8)
            # Generator->glTF->Unity double V conversion retains these exact integer corners.
            exported = plate['UV1'].copy()
            exported[:, 1] = 1 - exported[:, 1]
            exported[:, 1] = 1 - exported[:, 1]
            assert np.array_equal(exported.astype(np.float16), plate['UV1'])
            seen += 1
    assert seen == 2
