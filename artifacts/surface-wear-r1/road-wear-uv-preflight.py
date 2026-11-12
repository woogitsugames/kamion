"""Read-only preflight: active lane wear UV coverage in current main's generated GLBs."""
import json,struct,hashlib
from pathlib import Path
from collections import defaultdict
import numpy as np
repo=Path(__file__).resolve().parents[2]
manifest=repo/'Data/Regions/bialystok-industrial-c/generated/world_manifest.json'
m=json.loads(manifest.read_text(encoding='utf-8'))
mismatches=[]
missing=[]
result=defaultdict(lambda:dict(primitives=0,vertices=0,active_lane_vertices=0,missing_uv1_primitives=0))
for c in m['chunks']:
 for tier,key in [('High',None),('Low','low')]:
  item=c if key is None else c[key]
  path=repo/item['file'];data=path.read_bytes()
  if hashlib.sha256(data).hexdigest()!=item['sha256']:mismatches.append(str(path))
  jl=struct.unpack_from('<I',data,12)[0];g=json.loads(data[20:20+jl]);offset=20+jl;bl,bt=struct.unpack_from('<II',data,offset);binary=memoryview(data)[offset+8:offset+8+bl]
  for mesh in g.get('meshes',[]):
   for p in mesh['primitives']:
    name=g['materials'][p['material']].get('name','')
    if name not in ('road_asphalt','road_asphalt_new'):continue
    r=result[tier+'/'+name];r['primitives']+=1
    n=g['accessors'][p['attributes']['POSITION']]['count'];r['vertices']+=n
    ai=p['attributes'].get('TEXCOORD_1')
    if ai is None:
     r['missing_uv1_primitives']+=1;missing.append({'tier':tier,'file':item['file'],'material':name,'vertices':n,'attributes':list(p['attributes'])});continue
    a=g['accessors'][ai];v=g['bufferViews'][a['bufferView']]
    assert a['componentType']==5126 and a['type']=='VEC2',(path,a)
    start=v.get('byteOffset',0)+a.get('byteOffset',0)
    uv=np.ndarray((a['count'],2),np.float32,buffer=binary,offset=start,strides=(v.get('byteStride',8),4))
    r['active_lane_vertices']+=int((uv[:,0]>-.5).sum())
for r in result.values():r['active_vertex_percent']=round(100*r['active_lane_vertices']/max(1,r['vertices']),3)
out={'scope':'vertex coverage, not area/pixel coverage; read-only own D baseline products','manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),'coverage':dict(result),'glb_manifest_mismatches':mismatches,'missing_uv1':missing}
Path('artifacts/surface-wear-r1/road-wear-uv-preflight.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
