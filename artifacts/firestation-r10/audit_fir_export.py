"""Read actual baseline/proxy GLBs, verify primitives and every baseline alpha UV triangle."""
import hashlib
import json
import struct
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent/'shape-candidates'
def read(path):
    data=path.read_bytes();length,kind=struct.unpack_from('<II',data,12)
    assert kind==0x4e4f534a
    meta=json.loads(data[20:20+length]);off=20+length;blen,bkind=struct.unpack_from('<II',data,off)
    assert bkind==0x004e4942
    blob=data[off+8:off+8+blen]
    def accessor(index):
        a=meta['accessors'][index];v=meta['bufferViews'][a['bufferView']]
        dtype=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1',5122:'<i2',5120:'i1'}[a['componentType']])
        n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
        return np.ndarray((a['count'],n),dtype=dtype,buffer=blob,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',n*dtype.itemsize),dtype.itemsize)).copy()
    return meta,accessor

baseline=ROOT/'art-source/world/landmarks/fire_station_jrg2/fire_station_jrg2.glb'
proxy=OUT/'fir-proxy-artifact.glb'
rect=np.array([.30,.025,.43,.24]);audit={};uvs={}
for label,path in [('baseline',baseline),('proxy',proxy)]:
    meta,access=read(path);audit[label]={}
    for node in meta['nodes']:
        if 'mesh' not in node:continue
        mesh=meta['meshes'][node['mesh']];materials=[];triangles=0;tested=0
        for prim in mesh['primitives']:
            material=meta['materials'][prim['material']]['name'];materials.append(material)
            indices=access(prim['indices']).ravel();triangles+=len(indices)//3
            if material=='fire_station_alpha' and label=='baseline':
                uv=access(prim['attributes']['TEXCOORD_0'])
                uv[:,1]=1-uv[:,1] # EXACT GlbReader.ReadVec2(...,true) runtime convention
                assert uv.min()>=-1e-7 and uv.max()<=1+1e-7
                tris=uv[indices.reshape(-1,3)];lo=tris.min(axis=1);hi=tris.max(axis=1)
                overlap=(np.minimum(hi[:,0],rect[2])>np.maximum(lo[:,0],rect[0]))&(np.minimum(hi[:,1],rect[3])>np.maximum(lo[:,1],rect[1]))
                assert not overlap.any(),node['name']
                tested=len(tris)
        audit[label][node['name']]={'primitive_count':len(mesh['primitives']),'material_names':materials,'triangles':triangles}
        if label=='baseline':uvs[node['name']]={'tested_alpha_UV_triangles':tested,'overlaps':0}
for name,record in audit['baseline'].items():
    assert audit['proxy'][name]['material_names']==record['material_names']
    assert audit['proxy'][name]['primitive_count']==record['primitive_count']
assert [audit['proxy'][n]['triangles'] for n in audit['proxy']]==[9944,2744,164]
proof=json.loads((OUT/'fir-alpha-proxy-proof.json').read_text())
proof['actual_GLBS']=audit;proof['actual_baseline_GLTF_alpha_UV_triangles']=uvs
proof['actual_GLBS_sha256']={label:hashlib.sha256(path.read_bytes()).hexdigest() for label,path in [('baseline',baseline),('proxy',proxy)]}
proof['batching_source_contract']['offline_export']='actual GLB primitive/material slot contract preserved4/2/1; no node/prototype/LOD count changes'
proof['batching_source_contract']['runtime_key']='WorldInstances.Flush slot=m_BatchOffset[proto]+lod; mesh.subMesh s; materialStart[lod]+s; same gameObject.layer, receiveShadows, shadowLodMask, reflection/lightProbe usage'
proof['runtime_source_sha256']={rel:hashlib.sha256((ROOT/rel).read_bytes()).hexdigest() for rel in (
    'game/Assets/_Project/World/Runtime/WorldInstances.cs',
    'game/Assets/_Project/World/Import/InstanceImporter.cs',
    'game/Assets/_Project/World/Import/GlbReader.cs')}
(OUT/'fir-alpha-proxy-proof.json').write_text(json.dumps(proof,indent=2))
print(json.dumps({'GLB':audit,'baseline_alpha_uv':uvs},indent=2))
