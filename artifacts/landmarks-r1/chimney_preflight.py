"""Read-only audit of the actual exported EC chimney axes for the later round."""
import json
import struct
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
buf = (ROOT / 'art-source/world/props/street_props.glb').read_bytes()
json_len = struct.unpack_from('<I', buf, 12)[0]
doc = json.loads(buf[20:20+json_len])
data_offset = 20 + json_len + 8

def positions(index):
    a = doc['accessors'][index]
    view = doc['bufferViews'][a['bufferView']]
    assert a['componentType'] == 5126 and a['type'] == 'VEC3'
    return np.ndarray((a['count'],3), dtype='<f4', buffer=buf,
        offset=data_offset+view.get('byteOffset',0)+a.get('byteOffset',0),
        strides=(view.get('byteStride',12),4)).copy()

nodes = []
for node in doc['nodes']:
    if not node.get('name','').startswith('landmark_chimney_') or 'mesh' not in node:
        continue
    points = np.concatenate([positions(p['attributes']['POSITION'])
        for p in doc['meshes'][node['mesh']]['primitives']])
    centres = []
    for height in np.unique(points[:,1]):
        ring = points[points[:,1] == height][:,[0,2]]
        if len(ring) >= 8:
            centres.append((ring.min(0)+ring.max(0))/2)
    centre = np.array(centres)
    nodes.append({'node':node['name'], 'height_groups':len(centres),
        'horizontal_axis_drift_m':float(np.linalg.norm(centre.max(0)-centre.min(0))),
        'node_rotation':node.get('rotation',[0,0,0,1]),
        'node_matrix':node.get('matrix'),
        'height_bounds_m':[float(points[:,1].min()),float(points[:,1].max())]})
instances=[]
for path in (ROOT/'Data/raw/derived/bialystok-industrial-c/world').glob('instances_*.json'):
    for item in json.loads(path.read_text())['instances']:
        if item['p'].startswith('landmark_chimney_'):
            instances.append(item)
result={'scope':'CPU GLB and generated instance audit, not a Unity pose readback',
    'nodes':nodes,'instances':instances}
(Path(__file__).parent/'chimney-preflight.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
for node in nodes:
    print(node['node'], 'axis drift metres:', node['horizontal_axis_drift_m'])
print('instances:',len(instances))
