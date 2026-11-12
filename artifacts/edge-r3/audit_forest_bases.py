"""Measure actual far-forest curtain base vertices against frozen Before and live After apron.

Geometry only: texture alpha coverage and visibility from a road/photo pose are not evaluated.
"""
import hashlib
import json
import runpy
import struct
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if not (HERE/'After.complete').exists():
    raise RuntimeError('Complete the after matrix first')


def forest_bases(path):
    data = path.read_bytes()
    size = struct.unpack_from('<I', data, 12)[0]
    doc = json.loads(data[20:20+size])
    binary = 20+size+8
    dtypes = {5120:'i1', 5121:'u1', 5122:'<i2', 5123:'<u2', 5125:'<u4', 5126:'<f4'}

    def accessor(index):
        item = doc['accessors'][index]
        view = doc['bufferViews'][item['bufferView']]
        components = {'VEC2':2, 'VEC3':3}[item['type']]
        dtype = np.dtype(dtypes[item['componentType']])
        offset = binary+view.get('byteOffset',0)+item.get('byteOffset',0)
        return np.ndarray((item['count'],components), dtype=dtype, buffer=data, offset=offset,
                          strides=(view.get('byteStride',dtype.itemsize*components),dtype.itemsize))

    points = []
    for node in doc['nodes']:
        if 'mesh' not in node:
            continue
        if any(key in node for key in ('matrix','translation','rotation','scale')):
            raise RuntimeError('Unexpected node transform')
        for primitive in doc['meshes'][node['mesh']]['primitives']:
            if doc['materials'][primitive['material']]['name'] != 'forest_edge_mixed':
                continue
            attributes = primitive['attributes']
            if doc['accessors'][attributes['POSITION']]['componentType'] != 5126:
                raise RuntimeError('Expected unquantized source positions')
            position = accessor(attributes['POSITION'])
            uv = accessor(attributes['TEXCOORD_0'])
            # glTF writer stores v = 1 - source_v; curtain bottoms have source_v=0.
            # UV accessors are float32, not normalized integer attributes.
            if doc['accessors'][attributes['TEXCOORD_0']]['componentType'] != 5126:
                raise RuntimeError('Expected float32 source UVs')
            for index in np.flatnonzero(uv[:,1] == 1):
                p = position[index]
                points.append((node['name'], float(-p[0]), float(p[2]), float(p[1])))
    if not points:
        raise RuntimeError('No curtain base vertices found; do not report an empty pass')
    return points


points_by_tier = {}
files = {}
for tier, name in (('High','far_field.glb'), ('Low','far_field.low.glb')):
    frozen = HERE/'before-source'/name
    current = ROOT/'Data/raw/derived/bialystok-industrial-c/world'/name
    old_hash = hashlib.sha256(frozen.read_bytes()).hexdigest()
    new_hash = hashlib.sha256(current.read_bytes()).hexdigest()
    if old_hash != new_hash:
        raise RuntimeError(f'{tier} source mesh changed; cannot isolate the apron fix')
    files[tier] = dict(before_sha256=old_hash, after_sha256=new_hash)
    points_by_tier[tier] = forest_bases(frozen)

result = dict(source_meshes=files, numerical_tolerance_m=0.05,
              tolerance_status='WORKING_VALUE',
              note='Curtain base vertices, not trees. Computed after the change from frozen Before '
                   'geometry and live After. Texture alpha and camera visibility UNVERIFIED.')
for phase in ('before','after'):
    sys.argv = [str(HERE/'audit_ground_alignment.py'), phase]
    context = runpy.run_path(str(HERE/'audit_ground_alignment.py'))
    ground_at = context['ground_at']
    tiers = {}
    for tier, points in points_by_tier.items():
        rows = []
        uncovered = 0
        for sector,e,n,y in points:
            ground = ground_at(e,n)
            if ground is None:
                uncovered += 1
                continue
            rows.append(dict(sector=sector, e=e, n=n, base_y=y, ground_y=ground, clearance_m=y-ground))
        if not rows:
            raise RuntimeError(f'No apron coverage for {phase}/{tier}')
        clearance = np.array([row['clearance_m'] for row in rows])
        tiers[tier] = dict(base_vertices=len(points), sampled=len(rows), uncovered=uncovered,
                           min_clearance_m=float(clearance.min()), max_clearance_m=float(clearance.max()),
                           above_0_05m=int((clearance > 0.05).sum()),
                           worst_vertices=sorted(rows,key=lambda row:row['clearance_m'],reverse=True)[:10])
    result[phase] = dict(apron_sources=context['result']['source_sha256'],tiers=tiers)
(HERE/'forest-base-clearance.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({phase:{tier:{k:v for k,v in row.items() if k != 'worst_vertices'}
                         for tier,row in result[phase]['tiers'].items()}
                  for phase in ('before','after')}))
