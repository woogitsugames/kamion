"""Match one source building's generated triangles to the frozen production GLB.

The screen overlay establishes geometry identity, not photographic identity.
Run only under the heavy slot after Baseline.ready, before editing far_field.py.
"""
import collections
import hashlib
import json
import re
import struct
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT/'tools/worldgen'))
from streetscape import far_field as FF

if not (HERE/'Baseline.ready').exists():
    raise RuntimeError('Complete and freeze the baseline first')
building_id = '2BE4B431-C061-1BF0-E053-CC2BA8C0D140'
cache = json.loads((ROOT/'Data/raw/derived/bialystok-industrial-c/world/far_field_gis_cache.json').read_text())
matches = [b for b in cache['buildings'] if b['id'] == building_id]
if len(matches) != 1:
    raise RuntimeError('Source candidate missing or ambiguous')
building = matches[0]
apron = json.loads((HERE/'before-source/far_field_apron.json').read_text())
border = apron['border_z']
elev = FF.BorderElevation(apron['half_m'], *(border[s] for s in ('south','east','north','west')))
exclusion = FF.region_building_exclusion('bialystok-industrial-c', *cache['origin_epsg2180'], apron['half_m'])


def glb_triangles(path):
    data = path.read_bytes()
    size = struct.unpack_from('<I', data, 12)[0]
    doc = json.loads(data[20:20+size])
    start = 20+size+8
    def acc(index):
        a = doc['accessors'][index]
        v = doc['bufferViews'][a['bufferView']]
        dtype = np.dtype({5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']])
        dim = {'SCALAR':1,'VEC3':3}[a['type']]
        return np.ndarray((a['count'],dim), dtype=dtype, buffer=data,
                          offset=start+v.get('byteOffset',0)+a.get('byteOffset',0),
                          strides=(v.get('byteStride',dtype.itemsize*dim),dtype.itemsize))
    for node in doc['nodes']:
        if 'mesh' not in node:
            continue
        if any(k in node for k in ('matrix','translation','rotation','scale')):
            raise RuntimeError('Unexpected GLB node transform')
        for p in doc['meshes'][node['mesh']]['primitives']:
            if doc['materials'][p['material']]['name'] != 'far_field_buildings':
                continue
            positions = acc(p['attributes']['POSITION']).astype(float)
            positions = positions[:,[0,2,1]] * [-1,1,1]  # local E,N,U
            yield node['name'], positions[acc(p['indices']).reshape(-1,3)]


def triangle_key(triangle):
    return tuple(sorted(tuple(p) for p in np.rint(triangle*1000).astype(np.int64)))


result = dict(building=building, note='Exact source-to-production triangle match; no photographic identity claim.',tiers={})
high_triangles = None
for tier, filename in (('High','far_field.glb'),('Low','far_field.low.glb')):
    sectors = {name:FF.SectorBuilder(name) for name in FF.SECTORS}
    FF._add_building(sectors, building, elev, apron['half_m'], tier, exclusion=exclusion)
    expected = []
    colors = []
    for sector in sectors.values():
        for primitive in sector.primitives():
            if primitive['mat'] != 'far_field_buildings':
                continue
            expected.extend(np.asarray(primitive['V'])[np.asarray(primitive['T'])])
            colors.extend(primitive['COL'])
    if not expected:
        raise RuntimeError(f'{tier}: candidate produced no geometry')
    path = HERE/'before-source'/filename
    actual = collections.Counter(triangle_key(t) for _, triangles in glb_triangles(path) for t in triangles)
    expected_counts = collections.Counter(triangle_key(t) for t in expected)
    missing = list((expected_counts-actual).elements())
    if missing:
        raise RuntimeError(f'{tier}: {len(missing)} candidate triangles absent from frozen GLB')
    result['tiers'][tier] = dict(triangles=len(expected), matched=len(expected),
                               source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                               colors=np.unique(np.round(np.asarray(colors),5),axis=0).tolist())
    if tier == 'High':
        high_triangles = np.asarray(expected)

scene_path = ROOT/'game/Assets/_Generated/World/bialystok-industrial-c/WorldC_High.unity'
scene = scene_path.read_text(encoding='utf-8-sig')
documents = re.split(r'^--- !u!',scene,flags=re.M)[1:]
go = [d for d in documents if d.startswith('1 &') and re.search(r'^  m_Name: QA_edge-south\s*$',d,re.M)]
if len(go) != 1:
    raise RuntimeError('Camera GameObject not unique')
go_id = re.match(r'1 &(-?\d+)',go[0])[1]
transforms = [d for d in documents if d.startswith('4 &') and f'm_GameObject: {{fileID: {go_id}}}' in d]
if len(transforms) != 1:
    raise RuntimeError('Camera Transform not unique')
transform = transforms[0]
def vector(text,key,fields):
    payload = re.search(rf'{key}: \{{([^}}]+)\}}',text)[1]
    return np.array([float(re.search(rf'\b{field}: ([\d.eE+\-]+)',payload)[1]) for field in fields])
position = vector(transform,'m_LocalPosition','xyz')
if not np.allclose(vector(transform,'m_LocalScale','xyz'),1):
    raise RuntimeError('Scaled camera transform unsupported')
qx,qy,qz,qw = vector(transform,'m_LocalRotation','xyzw')
rotation = np.array([[1-2*(qy*qy+qz*qz),2*(qx*qy-qz*qw),2*(qx*qz+qy*qw)],
                     [2*(qx*qy+qz*qw),1-2*(qx*qx+qz*qz),2*(qy*qz-qx*qw)],
                     [2*(qx*qz-qy*qw),2*(qy*qz+qx*qw),1-2*(qx*qx+qy*qy)]])
parent_id = re.search(r'm_Father: \{fileID: (-?\d+)\}',transform)[1]
parent = [d for d in documents if d.startswith(f'4 &{parent_id}\n') or d.startswith(f'4 &{parent_id}\r\n')]
if len(parent) != 1 or not np.allclose(vector(parent[0],'m_LocalPosition','xyz'),0) or not np.allclose(vector(parent[0],'m_LocalRotation','xyzw'),[0,0,0,1]) or not np.allclose(vector(parent[0],'m_LocalScale','xyz'),1):
    raise RuntimeError('Nonidentity camera parent; resolve full transform before overlay')
if re.search(r'm_Father: \{fileID: (-?\d+)\}',parent[0])[1] != '0':
    raise RuntimeError('Nested camera parent unsupported')
anchor_z = float(re.search(r'^  anchorZ: ([\d.\-]+)',scene,re.M)[1])
region_docs = [d for d in documents if re.search(r'^  anchorZ:',d,re.M)]
if len(region_docs) != 1:
    raise RuntimeError('Region root ambiguous')
region_go = re.search(r'm_GameObject: \{fileID: (-?\d+)\}',region_docs[0])[1]
region_transform = [d for d in documents if d.startswith('4 &') and f'm_GameObject: {{fileID: {region_go}}}' in d]
if len(region_transform) != 1 or not np.allclose(vector(region_transform[0],'m_LocalPosition','xyz'),[0,-anchor_z,0]) or not np.allclose(vector(region_transform[0],'m_LocalRotation','xyzw'),[0,0,0,1]) or not np.allclose(vector(region_transform[0],'m_LocalScale','xyz'),1):
    raise RuntimeError('Region root transform differs from expected local ENU contract')
camera_docs = [d for d in documents if d.startswith('20 &') and f'm_GameObject: {{fileID: {go_id}}}' in d]
fov = float(re.search(r'field of view: ([\d.]+)',camera_docs[0])[1])
width,height = 2340,1080
focal = height/(2*np.tan(np.deg2rad(fov)/2))
world = high_triangles[:,:,[0,2,1]].copy()
world[:,:,1] -= anchor_z
view = (world-position) @ rotation
if np.any(view[:,:,2] <= 0):
    raise RuntimeError('Candidate triangle crosses camera plane')
screen = np.stack((width/2+view[:,:,0]/view[:,:,2]*focal,
                   height/2-view[:,:,1]/view[:,:,2]*focal),axis=-1)
draw = '\n'.join('polyline '+ ' '.join(f'{x:.3f},{y:.3f}' for x,y in np.vstack((t,t[0]))) for t in screen)
subprocess.run(['magick','-limit','thread','1',str(HERE/'before/High-clear/edge-south.png'),
                '-fill','none','-stroke','#00ff80','-strokewidth','2','-draw',draw,
                '-resize','960x',str(HERE/'hall-identified-overlay.jpg')],check=True)
result['camera'] = dict(position=position.tolist(),rotation_xyzw=[qx,qy,qz,qw],fov_deg=fov,
                        anchor_z=anchor_z,scene_sha256=hashlib.sha256(scene_path.read_bytes()).hexdigest(),
                        projected_bounds_px=[screen.reshape(-1,2).min(axis=0).tolist(),screen.reshape(-1,2).max(axis=0).tolist()])
(HERE/'hall-identification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({tier:{k:v for k,v in value.items() if k != 'colors'} for tier,value in result['tiers'].items()}))
