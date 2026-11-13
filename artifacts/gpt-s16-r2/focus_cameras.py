"""Closer street views of actual changed fronts and nearby measured garden-crown positions."""
import json,sys
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import Point,LineString
root=Path(__file__).resolve().parents[2];r=Path(__file__).parent
sys.path.insert(0,str(root/'tools/worldgen'))
from roads import profile
from streetscape import plots as PLT
region=root/'Data/Regions/bialystok-industrial-c'
q=json.loads((r/'baseline-streetscape-qa.json').read_text());m=json.loads((r/'baseline-world-manifest.json').read_text());o=np.array([m['origin_epsg2180'][k] for k in ('x','y')]);hf=profile.load_heightfield(json.loads((region/'terrain.json').read_text()),root,o)
graph=json.loads((region/'roads.graph.json').read_text());edges=[(LineString(np.array(e['geometry'])-o),e) for e in graph['edges']]
fronts={p['plot'] for p in json.loads((r/'after-streetscape-qa.json').read_text())['garden_fronts']['list']}
trees=[t for t in json.loads((r/'baseline-world-audit.json').read_text())['gardens'] if t['p']!='tree_pine']
original=json.loads((r/'street-views.json').read_text());cameras=json.loads((region/'gate3_cameras.json').read_text())['cameras'];selected=[]
for index,old in enumerate(original):
 name=old['street'];merged=shapely.line_merge(shapely.union_all([line for line,e in edges if e['attrs'].get('name',{}).get('v')==name]));components=list(getattr(merged,'geoms',[merged]));candidates=[]
 for p in q['plots']['list']:
  front=np.array(p['gate']['m'] if p['gate'] else p['wicket']['m'] if p['wicket'] else p['access']['q'] if p.get('access') else p['c'])
  _,e=min(edges,key=lambda x:x[0].distance(Point(front)))
  _,ec=min(edges,key=lambda x:x[0].distance(Point(p['c'])))
  if e['attrs'].get('name',{}).get('v')!=name and ec['attrs'].get('name',{}).get('v')!=name:continue
  near=[t for t in trees if t['src'].startswith('plot:'+p['id']+':') or np.linalg.norm(np.array([t['e'],t['n']])-np.array(p['c']))<25]
  if not near:continue
  score=4*(p['id'] in fronts)+2*min(3,len(near))+(p['front'] in PLT.SEE_THROUGH)
  candidates.append((score,p,front,near))
 if not candidates:raise ValueError(name)
 _,p,front,near=max(candidates,key=lambda c:(c[0],c[1]['id']))
 line=min(components,key=lambda l:l.distance(Point(front)));station=line.project(Point(front))
 tree=min(near,key=lambda t:np.linalg.norm(np.array([t['e'],t['n']])-np.array(p['c'])))
 target=.35*front+.65*np.array([tree['e'],tree['n']]);lookz=float(tree['z'])+float(tree['h'])*.55
 ids=[]
 for side,delta in [('a',-20),('b',20)]:
  at=np.array(line.interpolate(np.clip(station+delta,1,max(1,line.length-1))).coords[0]);cid=f'garden_focus_{index+1:02d}_{side}';ids.append(cid)
  cameras.append({'id':cid,'kind':'photo_match','seat':'file','pos':[float(at[0]),float(at[1]),float(hf.sample(*at))+2.2],'look_at':[float(target[0]),float(target[1]),lookz],'fov_deg':45,'note':f'ADR0154 WORKING_VALUE closer street pose; {name}; actual plot/crown; typological photo only'})
 selected.append({**old,'plot':p['id'],'age':p['age'],'front':p['front'],'cameras':ids,'new_hedge':p['id'] in fronts,'crown_target':tree,'reference_relation':'typological only, different location and pose'})
(r/'focus-cameras.json').write_text(json.dumps({'cameras':cameras},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(r/'focus-streets.json').write_text(json.dumps(selected,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print([(p['street'],p['new_hedge'],p['crown_target']['p']) for p in selected])
