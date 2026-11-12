"""Digest decoded collision input geometry, not Unity subasset identifiers.

Invoked by heavy-task.ps1 inside the World job's acquired heavy slot.
"""
import hashlib
import json
import struct
from pathlib import Path
import numpy as np

here = Path(__file__).resolve().parent
root = here.parents[1]
world = root/'Data/raw/derived/bialystok-industrial-c/world'
manifest = json.loads((root/'Data/Regions/bialystok-industrial-c/generated/world_manifest.json').read_text())
materials = manifest['materials']
types = {5121:'<u1',5123:'<u2',5125:'<u4',5126:'<f4'}
widths = {'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}

def read_glb(path):
    data = path.read_bytes()
    magic,version,length = struct.unpack_from('<4sII',data)
    if magic!=b'glTF' or version!=2 or length!=len(data):
        raise ValueError('Invalid GLB header: '+str(path))
    cursor,doc,binary = 12,None,None
    while cursor<len(data):
        count,kind = struct.unpack_from('<I4s',data,cursor)
        cursor += 8
        if kind==b'JSON': doc=json.loads(data[cursor:cursor+count])
        if kind==b'BIN\0': binary=memoryview(data)[cursor:cursor+count]
        cursor += count
    if doc is None or binary is None:
        raise ValueError('Missing GLB JSON/BIN chunk')
    return doc,binary

def accessor(doc,binary,index):
    value = doc['accessors'][index]
    view = doc['bufferViews'][value['bufferView']]
    dtype = np.dtype(types[value['componentType']])
    width = widths[value['type']]
    if value.get('sparse') or view.get('buffer',0)!=0 or value.get('normalized'):
        raise ValueError('Unsupported collision accessor layout')
    if view.get('byteStride',width*dtype.itemsize)!=width*dtype.itemsize:
        raise ValueError('Strided collision accessor requires explicit support')
    offset = view.get('byteOffset',0)+value.get('byteOffset',0)
    return np.frombuffer(binary,dtype,count=value['count']*width,offset=offset).reshape(value['count'],width)

records,buffers = {},{}
for path in sorted(world.glob('chunk_*.low.glb')):
    doc,binary = read_glb(path)
    parents = {child:i for i,node in enumerate(doc['nodes']) for child in node.get('children',[])}
    nodes = {}
    for ni,node in enumerate(doc['nodes']):
        if node.get('name') not in ('road_collision','terrain_lod2'):
            continue
        digest = hashlib.sha256()
        chain,seen,at = [],set(),ni
        while at is not None:
            if at in seen: raise ValueError('Cyclic node transform graph')
            seen.add(at)
            pose = doc['nodes'][at]
            chain.append({k:pose[k] for k in ('name','matrix','translation','rotation','scale') if k in pose})
            at = parents.get(at)
        digest.update(json.dumps(chain,sort_keys=True).encode())
        digest.update(json.dumps(manifest['origin_epsg2180'],sort_keys=True).encode())
        triangles,primitives = 0,[]
        for pi,primitive in enumerate(doc['meshes'][node['mesh']]['primitives']):
            if primitive.get('mode',4)!=4:
                raise ValueError('Non-triangle collision primitive')
            position_accessor = doc['accessors'][primitive['attributes']['POSITION']]
            if position_accessor['componentType']!=5126 or position_accessor['type']!='VEC3':
                raise ValueError('Unsupported quantized collision positions')
            positions = accessor(doc,binary,primitive['attributes']['POSITION']).astype('<f4',copy=False)
            indices = accessor(doc,binary,primitive['indices']).astype('<u4').reshape(-1)
            if indices.size%3 or not np.isfinite(positions).all() or (indices.size and int(indices.max())>=len(positions)):
                raise ValueError('Invalid collision positions/indices')
            material = doc['materials'][primitive['material']]['name']
            surface = materials.get(material,{}).get('surface')
            prefix = path.stem.replace('.','_')+'__'+node['name']+'__'+str(pi)
            position_key,index_key = prefix+'_positions',prefix+'_indices'
            buffers[position_key] = positions.copy()
            buffers[index_key] = indices.copy()
            metadata = dict(material=material,surface=surface,vertices=len(positions),triangles=indices.size//3,
                            position_array=position_key,index_array=index_key)
            digest.update(json.dumps(metadata,sort_keys=True).encode())
            digest.update(positions.tobytes())
            digest.update(indices.tobytes())
            triangles += indices.size//3
            primitives.append(metadata)
        nodes[node['name']] = dict(sha256=digest.hexdigest(),triangles=triangles,primitives=primitives)
    if 'terrain_lod2' not in nodes:
        raise ValueError('Missing terrain collision input: '+path.name)
    records[path.name] = nodes
if len(records)!=64:
    raise SystemExit('Expected 64 Low chunk GLBs')
result = dict(chunk_count=len(records),chunks=records,
    method='Exact decoded float32 positions, uint32 triangle indices, material/surface names, transform ancestry and region origin for road_collision and terrain_lod2. Includes referenced buffers as exported; conservative about vertex ordering. Not a hash of Unity files or a PhysX/runtime test.')
(here/'collision-current.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
np.savez_compressed(here/'collision-current.npz',**buffers)
print('Collision input geometry digests:',len(records),'Low chunks')
