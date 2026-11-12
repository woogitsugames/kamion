from source_fields import ROOT,OUT,glb
import numpy as np,json,math
stops=json.loads((OUT/'busstop-raw-proof.json').read_text())['region_stop_positions'];manifest=json.loads((ROOT/'Data/Regions/bialystok-industrial-c/generated/world_manifest.json').read_text());rows=[]
for stop in stops:
 en=np.array(stop['local_en']);hits=[]
 for ch in manifest['chunks']:
  bounds=ch['bounds_local_m']
  if not(bounds['e_min']-1<=en[0]<=bounds['e_max']+1 and bounds['n_min']-1<=en[1]<=bounds['n_max']+1):continue
  d,acc=glb(ROOT/ch['file'])
  for node in d['nodes']:
   if node['name']not in ('road','paved'):continue
   for p in d['meshes'][node['mesh']]['primitives']:
    mat=d['materials'][p['material']]['name'];v=acc(p['attributes']['POSITION']).astype(float);ix=acc(p['indices']).reshape(-1,3);v[:,0]*=-1;q=v[:,[0,2]];t=q[ix];ab=t[:,1]-t[:,0];ac=t[:,2]-t[:,0];ap=en-t[:,0];det=ab[:,0]*ac[:,1]-ab[:,1]*ac[:,0];valid=abs(det)>1e-8;b=np.divide(ap[:,0]*ac[:,1]-ap[:,1]*ac[:,0],det,out=np.zeros(len(det)),where=valid);c=np.divide(ab[:,0]*ap[:,1]-ab[:,1]*ap[:,0],det,out=np.zeros(len(det)),where=valid);a=1-b-c
    for j in np.where(valid&(a>=-.0001)&(b>=-.0001)&(c>=-.0001))[0]:
     height=a[j]*v[ix[j,0],1]+b[j]*v[ix[j,1],1]+c[j]*v[ix[j,2],1];hits.append(dict(chunk=ch['id'],layer=node['name'],material=mat,road_height=float(height),triangle_enu=v[ix[j]][:,[0,2,1]].tolist(),source=ch['file'],sha256=ch['sha256']))
 rows.append(dict(osm_node=stop['osm_node'],ref=stop['tags'].get('ref'),local_en=stop['local_en'],hits=hits))
(OUT/'busstop-surface-proof.json').write_text(json.dumps(dict(note='Actualsourcepointcontainment only; entire9gon+sameheight/chunk continuity and photo bay match still required before placement.',stops=rows),indent=2)+'\n');print([(x['ref'],[(h['layer'],h['material']) for h in x['hits']]) for x in rows])
