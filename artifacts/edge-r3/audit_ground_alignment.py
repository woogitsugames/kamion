"""Read-only feasibility audit for the next round: Python ground vs serialized Unity apron."""
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np
import shapely
from shapely import STRtree

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools/worldgen'))
from streetscape import far_field as FF

REGION = 'bialystok-industrial-c'
phase = sys.argv[1] if len(sys.argv) > 1 else 'after'
if phase not in ('before', 'after', 'prototype'):
    raise ValueError('Expected before, after or prototype')
mesh_path = ROOT / f'game/Assets/_Generated/World/{REGION}/Meshes/world_edge.asset'
if phase == 'before' and (HERE/'before-source/world_edge.asset').exists():
    mesh_path = HERE/'before-source/world_edge.asset'
source = mesh_path.read_text()
vertex_count = int(re.search(r'm_VertexCount: (\d+)', source)[1])
data = bytes.fromhex(re.search(r'_typelessdata: ([0-9a-fA-F]+)', source)[1])
channels = re.findall(r'- stream: (\d+)\s+offset: (\d+)\s+format: (\d+)\s+dimension: (\d+)', source)
sizes = {0:4, 1:2, 2:1, 3:1, 4:1, 5:1, 6:2, 7:2, 8:4, 9:4, 10:4, 11:4}
stride = max(int(offset)+sizes[int(fmt)]*int(dim) for stream,offset,fmt,dim in channels if stream == '0')
vertices = np.ndarray((vertex_count,3), dtype='<f4', buffer=data, strides=(stride,4)).astype(float)
index_format = int(re.search(r'm_IndexFormat: (\d+)', source)[1])
index_size = 2 if index_format == 0 else 4
indices = np.frombuffer(bytes.fromhex(re.search(r'm_IndexBuffer: ([0-9a-fA-F]+)', source)[1]),
                        dtype='<u2' if index_size == 2 else '<u4')
submeshes = re.findall(r'firstByte: (\d+)\s+indexCount: (\d+)', source)


def triangles(submesh):
    byte, count = map(int, submeshes[submesh])
    return indices[byte//index_size:byte//index_size+count].reshape(-1,3)


# Road shoulders are appended to grass; retain only the original apron surface.
base_vertices = int(triangles(1).min()) - 1
ground_indices = triangles(0)
ground = vertices[ground_indices[np.all(ground_indices < base_vertices, axis=1)]]
en = ground[:, :, [0,2]]
polygons = shapely.polygons(en)
tree = STRtree(polygons)


def ground_at(e, n):
    point = shapely.Point(e, n)
    for index in sorted(tree.query(point)):
        a, b, c = en[index]
        ab, ac, ap = b-a, c-a, np.array([e,n])-a
        det = ab[0]*ac[1]-ab[1]*ac[0]
        if abs(det) < 1e-8:
            continue
        u = (ap[0]*ac[1]-ap[1]*ac[0])/det
        v = (ab[0]*ap[1]-ab[1]*ap[0])/det
        if u >= -1e-5 and v >= -1e-5 and u+v <= 1.00001:
            heights = ground[index, :, 1]
            return float(heights[0]+u*(heights[1]-heights[0])+v*(heights[2]-heights[0]))
    return None


apron_path = ROOT / f'Data/raw/derived/{REGION}/world/far_field_apron.json'
if phase == 'before' and (HERE/'before-source/far_field_apron.json').exists():
    apron_path = HERE/'before-source/far_field_apron.json'
apron = json.loads(apron_path.read_text())
border = apron['border_z']
elev = FF.BorderElevation(1024.0, border['south'], border['east'], border['north'], border['west'])
rows = []
# Both straight sides and corner fans; no inference from a photographic pose.
for along in np.linspace(-1024, 1024, 129):
    for distance in (1, 8, 30, 60, 100, 160, 220, 280, 440, 600, 660):
        for e, n in ((along,-1024-distance), (1024+distance,along),
                     (along,1024+distance), (-1024-distance,along)):
            actual = ground_at(e,n)
            if actual is not None:
                predicted = elev.z_at_eff(e,n)
                rows.append(dict(e=float(e), n=float(n), outside_m=distance,
                                 unity_ground_m=actual, python_ground_m=predicted,
                                 delta_m=predicted-actual))
delta = np.array([r['delta_m'] for r in rows])
worst = sorted(rows, key=lambda r: abs(r['delta_m']), reverse=True)[:20]
result = dict(phase=phase, samples=len(rows), min_delta_m=float(delta.min()), max_delta_m=float(delta.max()),
              p95_absolute_delta_m=float(np.percentile(np.abs(delta),95)),
              above_building_skirt_0_8m=int((delta > 0.8).sum()), worst_samples=worst,
              source_sha256={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest()
                             for path in (mesh_path, apron_path)},
              note='Diagnostic only. Python ground minus actual original apron triangles; '
                   'does not prove a visible seam or alter production geometry/fog.')
(HERE/f'ground-alignment-{phase}.json').write_text(json.dumps(result,indent=2), encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k != 'worst_samples'}))
