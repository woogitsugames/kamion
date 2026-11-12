"""Measure every asphalt centroid on the frozen original apron, under heavy."""
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
from unity_mesh_audit import read_meshes

HERE = Path(__file__).resolve().parent
phase = sys.argv[1]
if phase not in ('before', 'after'):
    raise ValueError('Expected frozen before or after')
marker = 'Baseline.ready' if phase == 'before' else 'After.ready'
if not (HERE/marker).exists():
    raise RuntimeError('Freeze phase evidence first')
path = HERE/f'{phase}-source'/'world_edge.asset'
mesh = read_meshes(path)['world_edge']
vertices = mesh['positions'].astype(float)
if len(mesh['triangles']) != 2 or not np.isfinite(vertices).all():
    raise RuntimeError('Expected finite grass/asphalt mesh')
road = mesh['triangles'][1]
if not len(road) or len(road) % 24:
    raise RuntimeError('Expected complete 24-triangle continuations')
base_vertices = int(road.min())-1
if base_vertices <= 0 or len(vertices) != base_vertices+len(road)//24*52:
    raise RuntimeError('Unexpected continuation vertex layout')
grass = mesh['triangles'][0]
ground = vertices[grass[np.all(grass < base_vertices, axis=1)]]
if not len(ground):
    raise RuntimeError('Empty original apron surface')
a = ground[:, 0]
b, c = ground[:, 1]-a, ground[:, 2]-a
det = b[:, 0]*c[:, 2]-b[:, 2]*c[:, 0]
valid = np.abs(det) > 1e-7
a, b, c, det = a[valid], b[valid], c[valid], det[valid]


def ground_at(p):
    delta = p-a
    u = (delta[:, 0]*c[:, 2]-delta[:, 2]*c[:, 0])/det
    v = (b[:, 0]*delta[:, 2]-b[:, 2]*delta[:, 0])/det
    inside = (u >= -1e-5) & (v >= -1e-5) & (u+v <= 1.00001)
    return float(np.max((a[:, 1]+u*b[:, 1]+v*c[:, 1])[inside])) if np.any(inside) else None


rows = []
for stub_index in range(len(road)//24):
    samples = []
    for triangle in road[stub_index*24:(stub_index+1)*24]:
        p = vertices[triangle].mean(axis=0)
        ground_y = ground_at(p)
        if ground_y is None:
            raise RuntimeError(f'Uncovered asphalt centroid: stub {stub_index}, triangle {triangle}')
        samples.append(float(p[1]-ground_y))
    start = vertices[base_vertices+stub_index*52:base_vertices+stub_index*52+4].mean(axis=0)
    rows.append(dict(stub=stub_index, start_en=[float(start[0]), float(start[2])],
                     min_clearance_m=min(samples), samples_m=samples))
minimum = min(row['min_clearance_m'] for row in rows)
result = dict(phase=phase, asset_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
              vertex_count=mesh['count'], stride=mesh['stride'],
              vertex_bytes=mesh['count']*mesh['stride'], index_bytes=mesh['indices'].nbytes,
              grass_triangles=len(grass), asphalt_triangles=len(road),
              original_ground_triangles=len(ground), ground_vertices=base_vertices,
              measured_centroids=sum(len(row['samples_m']) for row in rows),
              min_clearance_m=minimum, stubs=rows,
              minimum_required_m=0.039,
              tolerance_note='0.04 m source clearance with 0.001 m numerical allowance; not driving collision validation.',
              sampling='Every asphalt centroid against original frozen apron triangles; excludes road shoulders')
(HERE/f'mesh-clearance-{phase}.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps({key: value for key, value in result.items() if key != 'stubs'}))
if minimum < result['minimum_required_m']:
    raise RuntimeError(f'Asphalt clearance regression: {minimum} m')
