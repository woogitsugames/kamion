from source_fields import OUT,glb
import numpy as np,json
rows=[]
for file in sorted((OUT/'raw-before').glob('chunk_*.glb')):
 if'.low.'in file.name:continue
 d,acc=glb(file)
 for node in d['nodes']:
  if node['name']!='markings':continue
  for p in d['meshes'][node['mesh']]['primitives']:
   if d['materials'][p['material']]['name']!='marking_white':continue
   at=p['attributes'];v=acc(at['POSITION']);uv=acc(at['TEXCOORD_0']);u1=acc(at['TEXCOORD_1'])if'TEXCOORD_1'in at else None
   if u1 is None:continue
   ix=acc(p['indices']).reshape(-1,3);parent=np.arange(len(v))
   def find(a):
    while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
    return a
   for a,b,c in ix:r=find(a);parent[find(b)]=r;parent[find(c)]=r
   groups={}
   for i in np.unique(ix):groups.setdefault(int(find(i)),[]).append(int(i))
   for ids in groups.values():
    if len(ids)not in(7,12,15):continue
    coords=uv[ids];extent=coords.max(0)-coords.min(0)
    if abs(coords[:,0].min())>.01 or not(any(abs(extent[0]-x)<.01 for x in(5,7.5,3.62))):continue
    if not np.all(np.float32(1)-u1[ids,1]>1.5):continue
    vv=v[ids].astype(float);enu=vv[:,[0,2,1]];enu[:,0]*=-1
    rows.append(dict(file=file.name,vertices=len(ids),center_enu=enu.mean(0).tolist(),bounds_enu=[enu.min(0).tolist(),enu.max(0).tolist()],uv0_range=[coords.min(0).tolist(),coords.max(0).tolist()],lane_x_range=[float(u1[ids,0].min()),float(u1[ids,0].max())],source_exposure_range=[float((1-u1[ids,1]).min()),float((1-u1[ids,1]).max())]))
(OUT/'actual-arrow-candidates.json').write_text(json.dumps(dict(note='Readonlyarrow candidates from actualglyph-localUV0,7/12/15vertexring, knowntransverseUV1.y>1.5,5/7.5/3.62m sourceglyphlength. Inspect actualimage beforeP8claim.',rows=rows),indent=2)+'\n');print(len(rows));print(rows[:3])
