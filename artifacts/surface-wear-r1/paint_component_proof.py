from source_fields import ROOT,OUT,glb
import numpy as np,json
m=json.loads((ROOT/'Data/Regions/bialystok-industrial-c/generated/world_manifest.json').read_text());rows=[]
for ch in m['chunks']:
 d,acc=glb(ROOT/ch['file'])
 for n in d['nodes']:
  if n['name']!='markings':continue
  for p in d['meshes'][n['mesh']]['primitives']:
   mat=d['materials'][p['material']]['name'];at=p['attributes']
   if not mat.startswith('marking_') or 'TEXCOORD_1'not in at:continue
   v=acc(at['POSITION']);uv=acc(at['TEXCOORD_1']);ix=acc(p['indices']).reshape(-1,3);parent=np.arange(len(v))
   def find(a):
    while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
    return a
   for a,b,c in ix:r=find(a);parent[find(b)]=r;parent[find(c)]=r
   before=len({find(int(i)) for i in ix.reshape(-1)});seen={};merges=0
   for i,point in enumerate(v):
    key=tuple(float(x) for x in point)+(float(uv[i,1]),)
    if key in seen:
     a=find(i);b=find(seen[key])
     if a!=b:parent[a]=b;merges+=1
    else:seen[key]=i
   after=len({find(int(i)) for i in ix.reshape(-1)})
   rows.append(dict(chunk=ch['id'],material=mat,indexed_components=before,coincident_same_age_components=after,metadata_unions=merges))
(OUT/'paint-component-proof.json').write_text(json.dumps(dict(note='Metadata grouping only; exact float32 positions+exactUV1.y, no geometry/index welding.',rows=rows),indent=2)+'\n');print(json.dumps(dict(indexed=sum(x['indexed_components']for x in rows),coincident_same_age=sum(x['coincident_same_age_components']for x in rows),unions=sum(x['metadata_unions']for x in rows))))
