"""Small, single-thread CPU measurements of the six imported representative meshes.

Counts are diagnostics, not a topology or appearance PASS. Intended holes, hard edges,
and narrow metal parts can be valid; compare the matching rendered probes.
"""
import os
for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[key] = '1'
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np

root = Path(__file__).resolve().parent
path = Path(sys.argv[1]) if len(sys.argv) > 1 else root/'wheel-mesh-before.json'
start = time.perf_counter()
data = json.loads(path.read_text(encoding='utf-8-sig'))

def vectors(values, names):
    return np.asarray([[v[name] for name in names] for v in values], dtype=np.float64)

rows = []
for mesh in data['rows']:
    points = vectors(mesh['vertices'], 'xyz')
    normals = vectors(mesh['normals'], 'xyz')
    uv = vectors(mesh['uv'], 'xy')
    row = {'asset':mesh['asset'],'node':mesh['node'],'runtime_readable':mesh['runtimeReadable'],
           'vertices':len(points),'normals':len(normals),'uv_vertices':len(uv),'submeshes':[]}
    semantic = hashlib.sha256()
    geometry = hashlib.sha256()
    for i, group in enumerate(mesh['submeshes']):
        if group['topology'] != 'Triangles':
            raise ValueError(f'Unexpected topology {mesh["node"]}: {group["topology"]}')
        indices = np.asarray(group['values'],dtype=np.int64).reshape(-1,3)
        if indices.size == 0:
            row['submeshes'].append({'index':i,'triangles':0})
            continue
        if indices.min() < 0 or indices.max() >= len(points):
            raise ValueError('Out-of-range index')
        a,b,c = (points[indices[:,k]] for k in range(3))
        cross = np.cross(b-a,c-a)
        twice_area = np.linalg.norm(cross,axis=1)
        longest = np.maximum.reduce([np.linalg.norm(a-b,axis=1),np.linalg.norm(b-c,axis=1),np.linalg.norm(c-a,axis=1)])
        slenderness = longest**2/np.maximum(twice_area,1e-30)
        result = {'index':i,'triangles':len(indices),'area_below_1e_minus12':int((twice_area<2e-12).sum()),
                  'area_m2_sum':float(twice_area.sum()/2),'slenderness_over_100':int((slenderness>100).sum())}
        # Stable triangle content hash, independent of imported vertex/triangle ordering.
        # Normals + UV record the shading inputs; winding is checked separately.
        corner = np.concatenate([points, normals, uv],axis=1) if len(normals)==len(points) and len(uv)==len(points) else points
        records=[]
        for tri in indices:
            corners = sorted(tuple(np.round(corner[j],6)) for j in tri)
            records.append(tuple(value for entry in corners for value in entry))
        semantic.update(np.asarray(sorted(records),dtype='<f8').tobytes())
        semantic.update(str(i).encode('ascii'))
        shape = np.concatenate([points,normals],axis=1) if len(normals)==len(points) else points
        shape_records = [tuple(value for corner in sorted(tuple(np.round(shape[j],6)) for j in tri) for value in corner)
                         for tri in indices]
        geometry.update(np.asarray(sorted(shape_records),dtype='<f8').tobytes())
        geometry.update(str(i).encode('ascii'))
        if len(normals)==len(points):
            avg = normals[indices].mean(axis=1)
            length = np.linalg.norm(avg,axis=1)
            valid = (length>1e-6)&(twice_area>2e-12)
            dots = np.sum(cross[valid]*avg[valid],axis=1)/(twice_area[valid]*length[valid])
            result.update(normal_winding_dot_below_minus_005=int((dots<-.05).sum()),valid_normal_faces=int(valid.sum()))
        if len(uv)==len(points):
            u = uv[indices]
            span = u.max(axis=1)-u.min(axis=1)
            result.update(uv_span_above_025=int((span.max(axis=1)>.25).sum()),uv_span_max=float(span.max()))
        row['submeshes'].append(result)
    row['semantic_triangle_sha256_1e6'] = semantic.hexdigest()
    row['geometry_normal_sha256_1e6'] = geometry.hexdigest()
    rows.append(row)
summary = {'input':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
           'note':'Imported local geometry before shader flattening. Measurements alone do not distinguish intended holes, collapsed geometry, UV artifacts or shading defects; compare actual probes. No automatic PASS.',
           'seconds':time.perf_counter()-start,'rows':rows}
out = path.with_name(path.stem+'-metrics.json')
out.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'meshes':len(rows),'seconds':summary['seconds'],'output':str(out)},ensure_ascii=False))
