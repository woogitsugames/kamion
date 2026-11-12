"""Small JSON validation of actual Editor-imported materials and Half2 buffers."""
import json
from pathlib import Path
from validate_exact import validate, ROOT

result = {}
for condition in ('Low-clear', 'Low-overcast', 'High-clear', 'High-overcast'):
    _, models = validate('after-b-exact', condition)
    dump = json.loads((ROOT / 'after-b-exact' / condition / 'exact-stats.json').read_text())
    materials = dump['materials']
    tractors = [m for m in materials if m['name'].startswith('M_tractor_paint_')]
    cars = [m for m in materials if m['name'].startswith('M_car_paint_')]
    curtains = [m for m in materials if m['name'].startswith('M_trailer_curtain_')]
    plates = [m for m in materials if m['name'] == 'M_car_plate']
    assert len(tractors) == 6 and len(cars) == 7 and len(curtains) == 6 and len(plates) == 1
    for m in tractors + cars:
        assert m['shader'] == 'Kamion/World PBR' and m['carPaint'], m
        assert m['flake']['w'] == (2 if m in tractors else 1), m
        assert m['tile']['x'] == m['tile']['y'] == 4, m
        assert 'car_grime_clean' in m['baseMap'], m
    for m in curtains:
        assert not m['carPaint']
        assert abs(m['tile']['x'] - 4.8) < .001 and abs(m['tile']['y'] - 2.7) < .001, m
    p = plates[0]
    assert p['shader'] == 'Kamion/World Car Plate' and p['carPlate'] and p['motionVectors'] and p['xrMotionVectors'], p
    native_tractors = [m for m in models if m['name'].startswith('tractor_')]
    assert len(native_tractors) == 6
    for model in native_tractors:
        assert len(model['payloads']) == 2
        for payload in model['payloads']:
            assert payload['present'] and payload['vertices'] > 0, model
            assert payload['heightError'] < .002 and payload['axleError'] < .002, model
    result[condition] = dict(tractor_materials=len(tractors), car_materials=len(cars), curtain_materials=len(curtains),
                             native_cab_lods=12, payload_error_max=max(p[k] for m in native_tractors for p in m['payloads'] for k in ('heightError', 'axleError')),
                             plate_local_corners_and_motion_vectors=True)
(ROOT / 'native-b-validation.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
