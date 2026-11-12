"""Small JSON validation of actual Editor-imported materials and Half2 buffers."""
import json
import hashlib
import sys
from pathlib import Path
from validate_exact import validate, ROOT

result = {}
stage = sys.argv[1] if len(sys.argv) > 1 else 'b'
assert stage in ('b', 'c')
folder = f'after-{stage}-exact'
plate_baseline = json.loads((ROOT.parent / 'life-r1' / 'plate-state-after-capture.json').read_text(encoding='utf-8-sig'))
plate_path = ROOT.parents[1] / 'game/Assets/_Generated/World/bialystok-industrial-c/Materials/M_car_plate.mat'
assert hashlib.sha256(plate_path.read_bytes()).hexdigest() == plate_baseline['native_material_sha256'].lower()
for condition in ('Low-clear', 'Low-overcast', 'High-clear', 'High-overcast'):
    _, models = validate(folder, condition)
    dump = json.loads((ROOT / folder / condition / 'exact-stats.json').read_text())
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
    assert p['shader'] == 'Kamion/World Car Plate' and p['carPlate'], p
    # R1 intentionally preserved ordinary Lit's disabled MotionVectors pass.
    # This is a preservation check, not a requirement to enable another pass.
    assert p['motionVectors'] == (not plate_baseline['motion_vectors_disabled']) and p['xrMotionVectors'], p
    native_tractors = [m for m in models if m['name'].startswith('tractor_')]
    assert len(native_tractors) == 6
    for model in native_tractors:
        assert len(model['payloads']) == 2
        for payload in model['payloads']:
            assert payload['present'] and payload['vertices'] > 0, model
            assert payload['heightError'] < .002 and payload['axleError'] < .002, model
    result[condition] = dict(tractor_materials=len(tractors), car_materials=len(cars), curtain_materials=len(curtains),
                             native_cab_lods=12, payload_error_max=max(p[k] for m in native_tractors for p in m['payloads'] for k in ('heightError', 'axleError')),
                             plate_local_corners=True, plate_motion_vectors_preserved=True, native_plate_material_unchanged=True, motion_vectors_enabled=p['motionVectors'])
(ROOT / f'native-{stage}-validation.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
