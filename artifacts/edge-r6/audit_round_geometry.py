"""Validate the ring-220 candidate against frozen imported Before/After meshes.

Run under heavy after both phases are complete. Unchanged far-field buffers
protect footprints, source heights, forest crowns, UVs and material flags.
"""
import hashlib
import json
import re
from pathlib import Path

import numpy as np

from unity_mesh_audit import read_meshes

HERE = Path(__file__).resolve().parent
if not all((HERE/name).exists() for name in ('Baseline.ready', 'After.ready')):
    raise RuntimeError('Both frozen phases required')
folders = [HERE/f'{phase}-source' for phase in ('before', 'after')]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def buffers(path):
    result = {}
    text = path.read_text(encoding='utf-8-sig')
    for document in re.split(r'^--- !u!43 &[^\r\n]+\r?\n', text, flags=re.M)[1:]:
        count = int(re.search(r'm_VertexCount: (\d+)', document)[1])
        if not count:
            continue
        name = re.search(r'^  m_Name: (.+)$', document, re.M)[1].strip()
        vertex = bytes.fromhex(re.search(r'_typelessdata: ([0-9a-fA-F]+)', document)[1])
        index = bytes.fromhex(re.search(r'm_IndexBuffer: ([0-9a-fA-F]+)', document)[1])
        if name in result:
            raise RuntimeError('Duplicate imported buffer name')
        result[name] = dict(vertex_bytes=len(vertex), index_bytes=len(index),
                            vertex_sha256=hashlib.sha256(vertex).hexdigest(),
                            index_sha256=hashlib.sha256(index).hexdigest())
    if not result:
        raise RuntimeError('No populated mesh buffers')
    return result


raw = {}
for name in ('far_field.glb', 'far_field.low.glb', 'far_field_apron.json', 'far_field_gis_cache.json'):
    hashes = [digest(folder/name) for folder in folders]
    if hashes[0] != hashes[1]:
        raise RuntimeError(f'Ring-only geometry contract changed generator data: {name}')
    raw[name] = hashes[0]
far = {}
for tier in ('Low', 'High'):
    old, new = [buffers(folder/f'world_edge_far-{tier}.asset') for folder in folders]
    if old != new or len(old) != 4:
        raise RuntimeError(f'{tier}: far-field vertex/index buffers changed')
    far[tier] = old

old, new = [read_meshes(folder/'world_edge.asset')['world_edge'] for folder in folders]
if old['count'] != new['count'] or old['stride'] != new['stride']:
    raise RuntimeError('Apron vertex count or layout grew')
if not np.array_equal(old['indices'], new['indices']):
    raise RuntimeError('Apron topology changed')
if len(old['triangles']) != 2 or any(not np.array_equal(a, b) for a, b in zip(old['triangles'], new['triangles'])):
    raise RuntimeError('Apron material submesh ranges changed')
if not np.array_equal(old['uv1'], new['uv1']):
    raise RuntimeError('Apron material flags changed')
base = int(old['triangles'][1].min())-1
if base <= 0 or base % 9:
    raise RuntimeError('Expected existing nine-ring apron layout')
ring = np.arange(5, base, 9)
boundary = np.arange(1, base, 9)
other = np.setdiff1d(np.arange(base), ring)
fixed_normals = np.array([i for i in range(base) if i % 9 not in (4, 5, 6)])
if not np.array_equal(old['normals'][fixed_normals], new['normals'][fixed_normals]):
    raise RuntimeError('Normals changed outside relocated-ring neighbours or road stubs')
if not np.isfinite(new['normals']).all():
    raise RuntimeError('Nonfinite recalculated normals')
p0, p1 = old['positions'], new['positions']
if not np.array_equal(p0[other], p1[other]):
    raise RuntimeError('A retained original apron ring moved')
displacement = p1[:, [0, 2]]-p0[:, [0, 2]]
xz_changed = np.flatnonzero(np.any(displacement != 0, axis=1))
if not np.array_equal(xz_changed, ring):
    raise RuntimeError('XZ changed outside the single relocated ring')
expected = (p0[ring][:, [0, 2]]-p0[boundary][:, [0, 2]])*(-60.0/280.0)
if not np.allclose(displacement[ring], expected, atol=0.001, rtol=0):
    raise RuntimeError('Relocated ring is not 280 -> 220 m')
for channel in ('colors', 'uv0'):
    unchanged = np.setdiff1d(np.arange(old['count']), ring)
    if not np.array_equal(old[channel][unchanged], new[channel][unchanged]):
        raise RuntimeError(f'{channel} changed outside the moved apron ring')
before, after = [buffers(folder/'world_edge.asset')['world_edge'] for folder in folders]
if any(before[key] != after[key] for key in ('vertex_bytes', 'index_bytes', 'index_sha256')):
    raise RuntimeError('Apron buffers grew or topology changed')
result = dict(raw_sources_identical=raw, far_field_buffers_identical=far,
              apron_before=before, apron_after=after,
              vertex_count=old['count'], original_ground_vertices=base,
              relocated_ring_vertices=len(ring),
              original_ring_distance_m=280, replacement_ring_distance_m=220,
              total_positions_changed=int(np.any(p0 != p1, axis=1).sum()),
              total_y_changed=int(np.count_nonzero(p0[:, 1] != p1[:, 1])),
              recalculated_normals_changed=int(np.any(old['normals'] != new['normals'], axis=1).sum()),
              source_height_or_forest_changes=False,
              note='Ring-only geometry contract; no alpha visibility or phone GPU claim.')
(HERE/'round-geometry-audit.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps({key: value for key, value in result.items() if key not in ('far_field_buffers_identical', 'raw_sources_identical')}))
