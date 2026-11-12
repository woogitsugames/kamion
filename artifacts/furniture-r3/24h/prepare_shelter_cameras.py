"""Metadata-only diagnostic cameras from generated instances, not photo-matched poses."""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EV = Path(__file__).resolve().parent
region = ROOT / 'Data/Regions/bialystok-industrial-c/generated'
manifest = json.loads((region / 'world_manifest.json').read_text(encoding='utf-8-sig'))
origin = manifest['origin_epsg2180']
sources = json.loads((region / 'streetscape_sources.json').read_text(encoding='utf-8-sig'))
stops = {node['osm_node']: node for node in sources['osm']['nodes']}
instances = []
inputs = []
for chunk in manifest['chunks']:
    path = ROOT / chunk['instances']['file']
    raw = path.read_bytes()
    inputs.append(dict(file=path.relative_to(ROOT).as_posix(), sha256=hashlib.sha256(raw).hexdigest()))
    instances.extend(i for i in json.loads(raw)['instances'] if i['p'] == 'bus_shelter')
base = json.loads((ROOT / 'artifacts/furniture-r2/24h/cameras.json').read_text(encoding='utf-8-sig'))
evidence = []
for node_id, label, photo in [(5802408812, 'anders-1000', '1911352299378570'),
                              (5802408814, 'factory', '5726790167361670')]:
    node = stops[node_id]
    e, n = node['geometry']['coordinates']
    e, n = e-origin['x'], n-origin['y']
    nearest = min(instances, key=lambda i: (i['e']-e)**2+(i['n']-n)**2)
    distance = math.hypot(nearest['e']-e, nearest['n']-n)
    assert distance < 25, (node_id, 'No existing nearby shelter; inspect source instead', distance)
    yaw = nearest['yaw']
    right = (math.cos(yaw), math.sin(yaw))
    front = (-math.sin(yaw), math.cos(yaw))
    for name, forward, lateral in [('front', 8.0, 0.0), ('corner', 6.0, 5.0)]:
        camera = dict(id=f'furniture-shelter-{label}-{name}', type='persp', fov_deg=45,
            pos=[round(nearest['e']+front[0]*forward+right[0]*lateral, 3),
                 round(nearest['n']+front[1]*forward+right[1]*lateral, 3), round(nearest['z']+1.65, 3)],
            look_at=[nearest['e'], nearest['n'], round(nearest['z']+1.2, 3)],
            note='Diagnostic pose WORKING_VALUE from generated instance; not a matched photograph')
        base['cameras'].append(camera)
    evidence.append(dict(osm_node=node_id, source_tags=node['tags'], selected_instance=nearest,
                         source_distance_m=round(distance, 3), reference_photo=photo,
                         caveat='Nearest-source association and camera offsets WORKING_VALUE; inspect images before model change'))
(EV / 'cameras.json').write_text(json.dumps(base, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
(EV / 'shelter-camera-evidence.json').write_text(json.dumps(dict(instances_inputs=inputs, selected=evidence), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(f'{len(base["cameras"])} cameras, including four shelter diagnostics; no photo pose claim')
