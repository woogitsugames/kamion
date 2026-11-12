"""Canonical gate cameras plus close/transition views around actual parked vehicles."""
import json
import math
from pathlib import Path

root = Path(__file__).resolve().parents[2]
doc = json.loads((root / 'Data/Regions/bialystok-industrial-c/gate3_cameras.json').read_text())
items = []
for f in (root / 'Data/raw/derived/bialystok-industrial-c/world').glob('instances_*.json'):
    items.extend(i for i in json.loads(f.read_text())['instances'] if i['p'].startswith(('car_', 'van_', 'tractor_', 'trailer_')))
anchor = doc['cameras'][0]['pos'][:2]
targets = []
for family in ('car_hatch_white', 'car_suv_black', 'tractor_blue', 'trailer_curtain_0'):
    candidates = [i for i in items if i['p'] == family]
    if not candidates:
        raise ValueError(f'No actual instance: {family}')
    item = min(candidates, key=lambda i:math.hypot(i['e']-anchor[0], i['n']-anchor[1]))
    targets.append(item)
    distances = [8,15.9,16.1,37.4,37.6,42.4,42.6,127.4,127.6] if family.startswith('car_') else [8,19.9,20.1,49.9,50.1,59.9,60.1,149.9,150.1]
    yaw = item.get('yaw', 0)
    # Three-quarter view from the vehicle's front-right, consistently rotated with the actual instance.
    ux, uy = math.cos(yaw)*.8 - math.sin(yaw)*.6, math.sin(yaw)*.8 + math.cos(yaw)*.6
    for distance in distances:
        height = 1.6
        horizontal = math.sqrt(distance**2-height**2)
        doc['cameras'].append(dict(id=f"lod_{family}_{distance:05.1f}".replace('.','p'), kind='photo_match', seat='file',
                                  pos=[item['e']+ux*horizontal, item['n']+uy*horizontal, item['z']+height],
                                  look_at=[item['e'],item['n'],item['z']+.8], fov_deg=60,
                                  note=f"ADR0153 actual instance {item['src']}; origin distance {distance} m; WORKING_VALUE review pose"))
(Path(__file__).parent/'qa-cameras.json').write_text(json.dumps(doc,indent=2)+'\n',encoding='utf-8')
(Path(__file__).parent/'qa-targets.json').write_text(json.dumps(targets,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(additional_cameras=len(doc['cameras']),target_prototypes=[i['p'] for i in targets])))
