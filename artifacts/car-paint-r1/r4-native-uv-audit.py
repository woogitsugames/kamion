"""Decode actual Unity serialized vertex buffers and their bound material Tile."""
from pathlib import Path
import hashlib
import json
import re
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
WORLD=ROOT/'game/Assets/_Generated/World/bialystok-industrial-c'
path=WORLD/'Instances.asset'
text=path.read_text()
documents=re.findall(r'^--- !u!(\d+) &(-?\d+)\n(.*?)(?=^---|\Z)',text,re.M|re.S)
meshes={key:body for kind,key,body in documents if kind=='43'}
main=next(body for kind,key,body in documents if kind=='114' and '\n  prototypes:\n' in body)
proto=re.search(r'^  prototypes:\n(.*?)(?=^  \w)',main,re.M|re.S).group(1)
materials=re.search(r'^  materials:\n(.*?)(?=^  \w|\Z)',main,re.M|re.S).group(1)
guids=re.findall(r'guid: ([a-f0-9]+)',materials)
bound={}
for p in (WORLD/'Materials').rglob('M_car_paint_*.mat'):
    meta=Path(str(p)+'.meta').read_text()
    guid=re.search(r'^guid: ([a-f0-9]+)',meta,re.M).group(1)
    s=p.read_text()
    t=re.search(r'_Tile: \{r: ([\d.eE+-]+), g: ([\d.eE+-]+), b: ([\d.eE+-]+),\s*a: ([\d.eE+-]+)\}',s)
    if t:bound[guid]=(p.stem,[float(v) for v in t.groups()])
rows=[]
native_samples=[]
for block in re.split(r'^  - name: ',proto,flags=re.M)[1:]:
    name=block.splitlines()[0]
    if not name.startswith(('car_','van_')):continue
    lodblock=block.split('    lods:\n',1)[1].split('    lodEndM:',1)[0]
    refs=re.findall(r'fileID: (-?\d+)',lodblock)
    starts=np.frombuffer(bytes.fromhex(re.search(r'materialStart: ([a-f0-9]+)',block).group(1)),dtype='<i4')
    for lod,key in enumerate(refs):
        mesh=meshes[key]
        n=int(re.search(r'm_VertexCount: (\d+)',mesh).group(1))
        raw=bytes.fromhex(re.search(r'_typelessdata: ([a-f0-9]+)',mesh).group(1))
        stride=len(raw)//n
        assert stride*n==len(raw)
        channels=re.findall(r'- stream: (\d+)\s+offset: (\d+)\s+format: (\d+)\s+dimension: (\d+)',mesh)
        channel=[int(v) for v in channels[4]]
        assert channel[0]==0 and channel[2:]==[1,2],channel
        uv=np.ndarray((n,2),dtype='<f2',buffer=raw,offset=channel[1],strides=(stride,2)).astype(np.float32)
        position=np.ndarray((n,3),dtype='<f4',buffer=raw,offset=0,strides=(stride,4))
        normal_offset=int(channels[1][1])
        normal=np.ndarray((n,3),dtype='i1',buffer=raw,offset=normal_offset,strides=(stride,1)).astype(np.float32)/127
        subblock=mesh.split('  m_SubMeshes:\n',1)[1].split('  m_Shapes:',1)[0]
        submeshes=re.findall(r'firstByte: (\d+)\s+indexCount: (\d+).*?baseVertex: (\d+)',subblock,re.S)
        rawindex=bytes.fromhex(re.search(r'm_IndexBuffer: ([a-f0-9]+)',mesh).group(1))
        indexbytes=2 if re.search(r'm_IndexFormat: (\d+)',mesh).group(1)=='0' else 4
        for sub,(offset,count,base) in enumerate(submeshes):
            binding=bound.get(guids[int(starts[lod])+sub])
            if binding is None:continue
            material,tile=binding
            idx=np.frombuffer(rawindex,dtype='<u2' if indexbytes==2 else '<u4',offset=int(offset),count=int(count))+int(base)
            sampled=uv[np.unique(idx)]
            tri=idx.reshape(-1,3)
            normals=normal[tri].mean(1)
            normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-8)
            native_samples.append(dict(prototype=name,lod=lod,material=material,tile=tile,
                uv=uv[tri].mean(1),position=position[tri].mean(1),normal=normals))
            v=sampled[:,1]/tile[1]
            assert v.min()>=0 and v.max()<1,'Unexpected texture-V wrap crossing'
            fraction=v-np.floor(v)
            source_v=fraction*2.5
            rows.append(dict(prototype=name,lod=lod,material=material,tile=tile,stride=stride,
                uv0_min=sampled.min(0).tolist(),uv0_max=sampled.max(0).tolist(),
                repeated_v_min=float(fraction.min()),repeated_v_max=float(fraction.max()),
                source_map_v_min_m=float(source_v.min()),source_map_v_max_m=float(source_v.max()),
                samples_legacy_gutter=bool(np.any(source_v<.05)),vertex_buffer_sha256=hashlib.sha256(raw).hexdigest()))
assert len(rows)==81,len(rows)
assert not any(r['samples_legacy_gutter'] for r in rows)
out=dict(method='Actual serialized native Instances.asset Float16 TexCoord0, index-selected paint submeshes and material GUID-bound Tile',
    instances_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),paint_lod_rows=len(rows),
    gutter_source_map_m=[0,.05],texture_v_wrap_crossings=0,
    native_tile_values=sorted({tuple(r['tile'][:2]) for r in rows}),
    all_vertex_and_affine_triangle_ranges_outside_gutter=True,
    note='Level0 coordinate range proof. Does not establish mip-identical filtering or fragment GPU binding; derivative/mip footprints can extend beyond a point sample.',rows=rows)
(ROOT/'artifacts/car-paint-r1/r4-native-uv0-tile-proof.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='rows'}))
