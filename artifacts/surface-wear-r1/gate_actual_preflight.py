from source_fields import ROOT,OUT,glb
import sys,json,importlib.util
import numpy as np
from types import SimpleNamespace
from shapely.geometry import Polygon
sys.path.insert(0,str(ROOT/'tools/worldgen'))
from roads import pipeline
from streetscape import gate as GT
spec=importlib.util.spec_from_file_location('streetscape.gate_wear_candidate',OUT/'gate_wear_candidate.py');G=importlib.util.module_from_spec(spec);spec.loader.exec_module(G)
net,graph,overrides,_=pipeline.build_network('bialystok-industrial-c');o=next(x for x in overrides if x.get('kind')=='depot_gate');nd=next(n for n in graph['nodes']if n['id']==o['node']);origin=np.array([777995,596223]);xy=np.array([nd['x'],nd['y']])-origin
lanes=[GT._chain_at_node(net,xy,w)for w in(o['entry_way'],o['exit_way'])];(_,ce,se,ge),(_,cx,sx,gx)=lanes;dd=np.arange(3.,70.,.5);pe=ce.line.offset_point(se+ge*dd,0.);px=cx.line.offset_point(sx+gx*dd,0.);hwe=ce.hw_at(se+ge*dd);hwx=cx.hw_at(sx+gx*dd);gap=np.hypot(*(pe-px).T)-hwe-hwx-2*GT.S.KERB_TOP_W;ok=np.nonzero(gap>=o.get('median_min_w',.8))[0];k=min(ok[0]+int(o.get('barrier_past_nose_m',3.)/.5),len(dd)-1);cases=[]
for(c,s0,g),name in zip(((ce,se,ge),(cx,sx,gx)),('entry','exit')):
 s=s0+g*dd[k];t=c.line.frame(s)[0]*g;travel=t if name=='exit'else-t;cases.append(dict(chain=c,station=s,travel=travel,name=name,src='override:'+o['id']))
class Buf:
 def __init__(self):self.parts=[]
 def add(self,layer,mat,V,UV,T,UV1=None,src=None):self.parts.append(SimpleNamespace(layer=layer,mat=mat,V=V,T=T,UV=UV,UV1=UV1,src=src))
buf=Buf();d,acc=glb(OUT/'raw-before/chunk_6_6.glb');forbidden=[]
for node in d['nodes']:
 if node['name']not in('road','markings','paved'):continue
 for p in d['meshes'][node['mesh']]['primitives']:
  v=acc(p['attributes']['POSITION']).astype(float);enu=v[:,[0,2,1]];enu[:,0]*=-1;ix=acc(p['indices']).reshape(-1,3);mat=d['materials'][p['material']]['name'];buf.parts.append(SimpleNamespace(layer=node['name'],mat=mat,V=enu,T=ix))
  if node['name']=='paved'and mat not in('yard_asphalt','yard_concrete','yard_concrete_worn'):
   for tri in enu[ix]:
    if np.linalg.norm(tri[:,:2].mean(0)-[617.86,-601.81])<15:
     pg=Polygon(tri[:,:2])
     if pg.area>1e-8:forbidden.append(pg)
count=len(buf.parts);report=G.emit(buf,cases,1024,forbidden,{});report['candidate_only']=True;report['actual_added_triangles']=sum(len(p.T)for p in buf.parts[count:]);report['actual_added_vertices']=sum(len(p.V)for p in buf.parts[count:]);report['source']='immutable raw-before/chunk_6_6.glb +canonicalbuild_network finalcentreline/width/gate station recipe';report['footprints']=[dict(src=p.src,bounds=[p.V.min(0).tolist(),p.V.max(0).tolist()])for p in buf.parts[count:]]
(OUT/'gate-actual-preflight.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
