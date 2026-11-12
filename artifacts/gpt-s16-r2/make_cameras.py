"""Twelve repeatable street poses around six actual OSM house streets; photos are typological references."""
import json,sys
from pathlib import Path
import numpy as np
from shapely.geometry import LineString,Point
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/worldgen'))
from roads import pipeline,profile
r=Path(__file__).parent;region=ROOT/'Data/Regions/bialystok-industrial-c'
qa=json.loads((r/'baseline-streetscape-qa.json').read_text())
manifest=json.loads((r/'baseline-world-manifest.json').read_text());o=np.array([manifest['origin_epsg2180'][k] for k in ('x','y')])
hf=profile.load_heightfield(json.loads((region/'terrain.json').read_text()),ROOT,o)
graph=json.loads((region/'roads.graph.json').read_text())
edges=[(LineString(np.asarray(e['geometry'])-o),e) for e in graph['edges']]
canonical=json.loads((region/'gate3_cameras.json').read_text());cameras=list(canonical['cameras']);selected=[]
streets=[('Skidelska','P08'),('Racławicka','P10'),('Grodzieńska','P07'),('Wileńska','P12'),('Brzeska','P14'),('Wołkowyska','P17')]
for index,(name,ref) in enumerate(streets):
 candidates=[]
 for p in qa['plots']['list']:
  if not p['gate']:continue
  gate=np.asarray(p['gate']['m']);line,e=min(edges,key=lambda x:x[0].distance(Point(gate)))
  if e['attrs'].get('name',{}).get('v')==name:
   # A longer road gives two regular street views, away from end caps.
   station=line.project(Point(gate));margin=min(station,line.length-station)
   candidates.append((margin,p,line,e))
 if not candidates: raise ValueError('No gated house on '+name)
 _,p,line,e=max(candidates,key=lambda c:c[0]);gate=np.asarray(p['gate']['m']);normal=np.asarray(p['gate']['n'])
 station=line.project(Point(gate));target=gate-normal*6
 poses=[]
 for side,delta in [('a',-32),('b',32)]:
  at=np.asarray(line.interpolate(np.clip(station+delta,1,max(1,line.length-1))).coords[0])
  if np.linalg.norm(at-target)<12:raise ValueError('Street view too close: '+name)
  entry=dict(id=f'garden_{index+1:02d}_{side}',kind='photo_match',seat='file',pos=[float(at[0]),float(at[1]),float(hf.sample(*at))+2.2],look_at=[float(target[0]),float(target[1]),float(hf.sample(*target))+6.0],fov_deg=75,note=f'ADR0154 WORKING_VALUE street pose; OSM {name}; plot {p["id"]}; {ref} is typological, NOT matched location/pose')
  cameras.append(entry);poses.append(entry['id'])
 selected.append(dict(street=name,plot=p['id'],age=p['age'],front=p['front'],osm_edge=e['id'],reference=ref,cameras=poses,reference_relation='typological; other location, see docs/refs/posesje-bialystok.md'))
(r/'qa-cameras.json').write_text(json.dumps({'cameras':cameras},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(r/'street-views.json').write_text(json.dumps(selected,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'gate3_and_extra':len(cameras),'house_streets':len(selected),'new_poses':12,'streets':[x['street'] for x in selected]},ensure_ascii=False))
