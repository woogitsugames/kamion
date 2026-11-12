"""Audit actual imported curtain bases against the actual original apron.

Source glTF V=1 must match imported Unity V=0 for bases; V=0/1 tops
must remain in place. Run under heavy against frozen baseline/After files.
This is geometry evidence only, not alpha coverage or road visibility.
"""
import hashlib
import json
import struct
import sys
from pathlib import Path

import numpy as np
import shapely
from shapely import STRtree

from unity_mesh_audit import read_meshes

HERE = Path(__file__).resolve().parent
phase = sys.argv[1]
if phase not in ('before', 'after'):
    raise ValueError('Expected before or after')
marker = 'Baseline.ready' if phase == 'before' else 'After.ready'
if not (HERE / marker).exists():
    raise RuntimeError(f'Freeze complete {phase} first')
folder = HERE / f'{phase}-source'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_forests(path):
    data = path.read_bytes()
    size = struct.unpack_from('<I', data, 12)[0]
    doc = json.loads(data[20:20+size])
    binary = 28 + size

    def accessor(index, dimension):
        item = doc['accessors'][index]
        view = doc['bufferViews'][item['bufferView']]
        if item['componentType'] != 5126 or item.get('normalized', False):
            raise RuntimeError('Expected float32 source positions/UVs')
        return np.ndarray((item['count'], dimension), dtype='<f4', buffer=data,
                          offset=binary+view.get('byteOffset', 0)+item.get('byteOffset', 0),
                          strides=(view.get('byteStride', dimension*4), 4))

    result = {}
    for node in doc['nodes']:
        if 'mesh' not in node:
            continue
        if any(key in node for key in ('matrix', 'translation', 'rotation', 'scale')):
            raise RuntimeError('Unexpected source node transform')
        primitives = doc['meshes'][node['mesh']]['primitives']
        for slot, primitive in enumerate(primitives):
            if doc['materials'][primitive['material']]['name'] != 'forest_edge_mixed':
                continue
            attrs = primitive['attributes']
            pos = accessor(attrs['POSITION'], 3).copy()
            pos[:, 0] *= -1  # GlbReader handedness: imported X is region E.
            uv = accessor(attrs['TEXCOORD_0'], 2)
            if node['name'] in result:
                raise RuntimeError('Duplicate forest primitive')
            result[node['name']] = dict(slot=slot, submeshes=len(primitives),
                                       bases=pos[uv[:, 1] == 1], tops=pos[uv[:, 1] == 0])
    if len(result) != 4:
        raise RuntimeError('Expected four populated forest sectors')
    return result


apron_path = folder / 'world_edge.asset'
apron = read_meshes(apron_path)['world_edge']
first_stub_vertex = int(apron['triangles'][1].min()) - 1
triangles = apron['triangles'][0]
triangles = triangles[np.all(triangles < first_stub_vertex, axis=1)]
ground = apron['positions'][triangles].astype(float)
if not len(ground) or not np.isfinite(ground).all():
    raise RuntimeError('Original apron surface is empty or nonfinite')
en = ground[:, :, [0, 2]]
tree = STRtree(shapely.polygons(en))


def ground_at(e, n):
    values = []
    for index in tree.query(shapely.Point(e, n)):
        a, b, c = en[index]
        ab, ac, ap = b-a, c-a, np.array([e, n])-a
        det = ab[0]*ac[1] - ab[1]*ac[0]
        if abs(det) < 1e-8:
            continue
        u = (ap[0]*ac[1] - ap[1]*ac[0]) / det
        v = (ab[0]*ap[1] - ab[1]*ap[0]) / det
        if u >= -1e-5 and v >= -1e-5 and u+v <= 1.00001:
            heights = ground[index, :, 1]
            values.append(float(heights[0]+u*(heights[1]-heights[0])+v*(heights[2]-heights[0])))
    return max(values) if values else None


result = dict(phase=phase, apron_sha256=sha(apron_path), original_ground_triangles=len(ground),
              numerical_tolerance_m=0.05, tolerance_status='WORKING_VALUE', tiers={},
              note='Actual imported curtain base vertices, not trees. Alpha coverage and photo/road visibility UNVERIFIED.')
for tier, filename in (('Low', 'far_field.low.glb'), ('High', 'far_field.glb')):
    raw_path = folder / filename
    mesh_path = folder / f'world_edge_far-{tier}.asset'
    forests = source_forests(raw_path)
    meshes = read_meshes(mesh_path)
    rows, counts, uncovered = [], [], 0
    for sector, source in forests.items():
        name = f'{sector}_{tier}'
        mesh = meshes[name]
        if len(mesh['triangles']) != source['submeshes']:
            raise RuntimeError('Imported submesh/material order differs')
        ids = np.unique(mesh['triangles'][source['slot']])
        base_ids = ids[mesh['uv0'][ids, 1] == 0]
        top_ids = ids[mesh['uv0'][ids, 1] == 1]
        bases, tops = mesh['positions'][base_ids], mesh['positions'][top_ids]
        if len(base_ids)+len(top_ids) != len(ids) or not np.isfinite(bases).all() or not np.isfinite(tops).all():
            raise RuntimeError('Unexpected intermediate forest UV row or nonfinite geometry')
        if len(bases) != len(source['bases']) or len(tops) != len(source['tops']) or not len(bases):
            raise RuntimeError('UV base/top selection does not match raw source inventory')
        if not np.allclose(bases[:, [0, 2]], source['bases'][:, [0, 2]], atol=1e-3, rtol=0):
            raise RuntimeError('Imported base XZ differs from raw source')
        if not np.allclose(tops, source['tops'], atol=1e-3, rtol=0):
            raise RuntimeError('Imported forest tops differ from raw source')
        if phase == 'before' and not np.allclose(bases, source['bases'], atol=1e-3, rtol=0):
            raise RuntimeError('Baseline import already changes source bases; inspect before attributing a fix')
        counts.append(dict(sector=sector, base_vertices=len(bases), top_vertices=len(tops),
                           raw_base_glTF_v=1, imported_base_Unity_v=0,
                           max_base_source_delta_m=float(np.max(np.abs(bases-source['bases'])))))
        for index, p in zip(base_ids, bases):
            e, y, n = map(float, p)
            actual = ground_at(e, n)
            if actual is None:
                uncovered += 1
            else:
                rows.append(dict(mesh=name, vertex=int(index), e=e, n=n, base_y=y,
                                 ground_y=actual, clearance_m=y-actual))
    if not rows or uncovered:
        raise RuntimeError(f'{tier}: missing apron coverage: {uncovered}')
    clearance = np.array([row['clearance_m'] for row in rows])
    result['tiers'][tier] = dict(base_vertices=len(rows), uncovered=uncovered,
        min_clearance_m=float(clearance.min()), max_clearance_m=float(clearance.max()),
        above_0_05m=int((clearance > 0.05).sum()), sectors=counts,
        worst_vertices=sorted(rows, key=lambda row: row['clearance_m'], reverse=True)[:30],
        raw_sha256=sha(raw_path), unity_sha256=sha(mesh_path))
(HERE / f'contact-{phase}.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps({tier: {k: v for k, v in row.items() if k not in ('sectors', 'worst_vertices')}
                  for tier, row in result['tiers'].items()}))
