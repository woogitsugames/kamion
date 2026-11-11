from pathlib import Path
import sys,re,json,hashlib
import numpy as np
root=Path.cwd();art=root/'artifacts/car-paint-r1';source=(art/'r4-native-uv-audit.py').read_text()
def read(tag,path):
 sys.argv=['audit',tag]
 code=source.replace("path=WORLD/'Instances.asset'",'path=Path('+repr(str(path))+')')
 scope={'__file__':str(art/'r4-native-uv-audit.py'),'__name__':'native_plate_audit'}
 exec(compile(code,'native_plate_audit','exec'),scope)
 return scope
before=read('preplate',art/'r4-preplate-native/Instances.asset')
after=read('plate-current',root/'game/Assets/_Generated/World/bialystok-industrial-c/Instances.asset')
rows=[]
for key,oldprims in before['native_geometry'].items():
 newprims=after['native_geometry'][key]
 assert len(oldprims)==len(newprims)
 for a,b in zip(oldprims,newprims):
  assert a['material']==b['material']
  for field in ('position','normal','uv'):assert np.array_equal(a[field],b[field]),(key,field)
  if a['material']!='M_car_plate':assert np.array_equal(a['payload'],b['payload']),key
  else:
   local=b['payload'].reshape(-1,2);uv=b['uv'].reshape(-1,2)
   assert np.array_equal(np.unique(local,axis=0),[[0,0],[0,1],[1,0],[1,1]])
   assert np.allclose(uv,uv.min(0)+local*np.ptp(uv,axis=0),atol=1e-7)
   assert np.all(a['payload']==0)
   rows.append(dict(prototype=key[0],lod=key[1],corners=np.unique(local,axis=0).tolist(),geometry_uv0_unchanged=True))
assert len(rows)==54
assert [r['stride'] for r in after['rows']]==[24]*81
assert [r['geometry_normal_uv0_index_sha256'] for r in before['rows']]==[r['geometry_normal_uv0_index_sha256'] for r in after['rows']]
report=dict(native_plate_submeshes=54,car_lods=81,stride_before=24,stride_after=24,added_vertex_bytes=0,geometry_normal_uv0_index_exact=81,all_nonplate_uv1_exact=True,rows=rows)
(art/'r4-plate-native-parity.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='rows'}))
