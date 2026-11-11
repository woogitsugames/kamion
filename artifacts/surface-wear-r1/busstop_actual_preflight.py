from source_fields import ROOT,OUT,glb
from types import SimpleNamespace
import sys,json,numpy as np
sys.path.insert(0,str(ROOT/'tools/worldgen'))
from streetscape import bus_stop_wear as B
class Buf:
 def __init__(self):self.parts=[]
 def add(self,layer,mat,V,UV,T,src=None,UV1=None):self.parts.append(SimpleNamespace(layer=layer,mat=mat,V=V,T=T,UV=UV,UV1=UV1,src=src))
buf=Buf();path=ROOT/'Data/raw/derived/bialystok-industrial-c/world/chunk_4_5.glb';d,acc=glb(path)
for n in d['nodes']:
 if n['name']not in('road','markings'):continue
 for p in d['meshes'][n['mesh']]['primitives']:
  v=acc(p['attributes']['POSITION']).astype(float);enu=v[:,[0,2,1]];enu[:,0]*=-1;ix=acc(p['indices']).reshape(-1,3)
  buf.parts.append(SimpleNamespace(layer=n['name'],mat=d['materials'][p['material']]['name'],V=enu,T=ix))
source=next(x for x in json.loads((OUT/'busstop-raw-proof.json').read_text())['region_stop_positions']if x['osm_node']==2367445386)
metadata=dict(osm_node=source['osm_node'],ref=source['tags']['ref'],bus=source['tags']['bus'],local_en=[round(x,2)for x in source['local_en']],half_m=1024)
count=len(buf.parts);report=B.emit(buf,[metadata],{});report['source_glb']=path.relative_to(ROOT).as_posix();report['raw_source_node']=source;report['added_parts']=len(buf.parts)-count;report['note']='Productionemitter against actualpinnedrawroad+markingfootprints BEFOREworldgeneration. Photo verifies bay context, oil/radius authoredWORKING_VALUE, not measuredphotooil. Native/runtimeproofpending.'
(OUT/'busstop-actual-preflight.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
