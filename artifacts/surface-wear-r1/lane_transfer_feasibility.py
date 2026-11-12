"""Conservative readonly feasibility of reusing existing lane field for constant-half paint."""
from pathlib import Path
import json,math
import numpy as np
from source_fields import ROOT,OUT,glb
CELL=8.
def main():
 m=json.loads((ROOT/'Data/Regions/bialystok-industrial-c/generated/world_manifest.json').read_text());report=[]
 for ch in m['chunks']:
  d,acc=glb(ROOT/ch['file']);road=[];paint=[]
  for n in d['nodes']:
   if n['name'] not in ('road','markings'):continue
   for p in d['meshes'][n['mesh']]['primitives']:
    mat=d['materials'][p['material']]['name'];at=p['attributes']
    if 'TEXCOORD_1' not in at:continue
    v=acc(at['POSITION']).astype(float);uv=acc(at['TEXCOORD_1']).astype(float);ix=acc(p['indices']).reshape(-1,3)
    if n['name']=='road' and mat in ('road_asphalt','road_asphalt_new'):
     for t in ix:
      if np.all(uv[t,0]>=-.5):road.append((v[t],uv[t,0]))
    if n['name']=='markings' and mat.startswith('marking_'):paint.append((v,uv,ix,mat))
  grid={}
  for j,(tri,u) in enumerate(road):
   p=tri[:,[0,2]];a=np.floor(p.min(axis=0)/CELL).astype(int);b=np.floor(p.max(axis=0)/CELL).astype(int)
   for x in range(a[0],b[0]+1):
    for y in range(a[1],b[1]+1):grid.setdefault((x,y),[]).append(j)
  def query(p):
   values=[]
   for j in grid.get(tuple(np.floor(p[[0,2]]/CELL).astype(int)),[]):
    t,u=road[j];a=t[0,[0,2]];ab=t[1,[0,2]]-a;ac=t[2,[0,2]]-a;delta=p[[0,2]]-a;det=ab[0]*ac[1]-ab[1]*ac[0]
    if abs(det)<1e-8:continue
    b=(delta[0]*ac[1]-delta[1]*ac[0])/det;c=(ab[0]*delta[1]-ab[1]*delta[0])/det;w=np.array([1-b-c,b,c])
    if w.min()<-.0001 or abs(w@t[:,1]-p[1])>.035:continue
    values.append(float(w@u))
   if not values:return None,'outside_or_height'
   if max(values)-min(values)>.02:return None,'ambiguous_overlap'
   return sum(values)/len(values),'ok'
  stats=dict(chunk=ch['id'],constant_triangles=0,accepted_triangles=0,accepted_area_m2=0.,rejected={})
  for v,uv,ix,mat in paint:
   for ids in ix:
    if not np.all(np.abs(uv[ids,0]-.5)<1e-5):continue
    stats['constant_triangles']+=1;t=v[ids];samples=np.vstack([t,(t[0]+t[1])/2,(t[1]+t[2])/2,(t[2]+t[0])/2,t.mean(axis=0)])
    results=[query(p) for p in samples];reason=next((r for val,r in results if val is None),None)
    if reason is None:
     values=np.array([x[0] for x in results]);pred=np.array([(values[0]+values[1])/2,(values[1]+values[2])/2,(values[2]+values[0])/2,values[:3].mean()])
     if np.max(np.abs(pred-values[3:]))>.025:reason='nonlinear_or_lane_discontinuity'
    if reason:stats['rejected'][reason]=stats['rejected'].get(reason,0)+1
    else:stats['accepted_triangles']+=1;stats['accepted_area_m2']+=float(np.linalg.norm(np.cross(t[1]-t[0],t[2]-t[0]))*.5)
  if stats['constant_triangles']:report.append(stats)
 packet=dict(note='Feasibility only, NOT production transfer. Uses actual road lane field only; no nearest-road extrapolation.7samples/triangle,3.5cm height tolerance WORKING, overlap disagreement>.02lane rejected, midpoint nonlinearity>.025lane rejected. Shared vertices/component closure still must be enforced in production, so accepted area is upper bound.',chunks=report)
 (OUT/'lane-transfer-feasibility.json').write_text(json.dumps(packet,indent=2)+'\n');print(json.dumps(dict(constant_triangles=sum(x['constant_triangles'] for x in report),accepted_triangles=sum(x['accepted_triangles'] for x in report),upper_bound_area_m2=sum(x['accepted_area_m2'] for x in report))))
if __name__=='__main__':main()
