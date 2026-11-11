"""Add frozen historical fleet views and one CPU-proposed R4 level3 control.

No old camera file, world placement or source geometry is changed.
"""
from pathlib import Path
import importlib.util
import json
import math
import sys
import numpy as np
import yaml
from shapely.geometry import Polygon, LineString, shape
from shapely.affinity import translate
from shapely.strtree import STRtree

ROOT=Path(__file__).resolve().parents[2]
ART=ROOT/'artifacts/car-paint-r1'
sys.path.insert(0,str(ROOT/'tools/worldgen'))
from streetscape import life_cars as LC
spec=importlib.util.spec_from_file_location('r4_model',ART/'r4-model.py')
model=importlib.util.module_from_spec(spec);spec.loader.exec_module(model)
manifest=json.loads((ROOT/'Data/Regions/bialystok-industrial-c/generated/world_manifest.json').read_text())
cars=[i for c in manifest['chunks'] for i in json.loads((ROOT/c['instances']['file']).read_text())['instances']
      if i['p'].startswith(('car_','van_'))]
footprints=[]
for car in cars:
    d=LC.VAN if car['p'].startswith('van_') else LC.CARS[car['p'].split('_')[1]]
    right=np.array([math.cos(car['yaw']),math.sin(car['yaw'])]);front=np.array([-right[1],right[0]])
    centre=np.array([car['e'],car['n']])
    footprints.append(Polygon([centre+right*x*d['W']/2+front*y*d['L']/2
                              for x,y in [(-1,-1),(1,-1),(1,1),(-1,1)]]).buffer(.08))
region=ROOT/'Data/Regions/bialystok-industrial-c'
origin=yaml.safe_load((region/'region.yaml').read_text())['origin']
buildings=[translate(shape(f['geometry']),-origin['x'],-origin['y'])
           for f in json.loads((region/'buildings.geojson').read_text())['features']]
tree=STRtree(footprints+buildings)
levels,phase=model.film_hash(np.array([[i['e'],i['n']] for i in cars]),[-1024,-1024])
doc=json.loads((ART/'r1-cameras.json').read_text())
entries={c['id']:c for c in doc['cameras']}
for c in json.loads((ART/'r4-historical-far-cameras.json').read_text())['cameras']:
    entries.setdefault(c['id'],c)
reference=np.array([716.39,-446.808])
candidates=sorted((j for j,c in enumerate(cars) if c['p']=='car_hatch_black' and levels[j]==3),
                  key=lambda j:np.linalg.norm(np.array([cars[j]['e'],cars[j]['n']])-reference))
chosen=None
for index in candidates:
    car=cars[index];centre=np.array([car['e'],car['n']]);d=LC.CARS['hatch']
    right=np.array([math.cos(car['yaw']),math.sin(car['yaw'])]);front=np.array([-right[1],right[0]])
    samples=[centre]+[centre+right*x*d['W']*.35+front*y*d['L']*.4 for x in (-1,1) for y in (-1,1)]
    for deg in [0]+[sign*delta for delta in range(5,181,5) for sign in (1,-1)]:
        theta=car['yaw']+math.radians(deg)
        eye=centre+5*np.array([math.cos(theta),math.sin(theta)])
        if all(not any(int(h)!=index for h in tree.query(LineString([sample,eye]),predicate='intersects')) for sample in samples):
            chosen=dict(instance=car,cpu_expected_r4_level=3,
                camera=dict(id='r4_dirt_candidate_3',type='persp',kind='photo_match',fov_deg=45,
                    pos=[float(eye[0]),float(eye[1]),car['z']+1.6],
                    look_at=[car['e'],car['n'],car['z']+.7],
                    note='WORKING_VALUE QA camera: CPU-proposed R4 level3 on actual car_hatch_black. GPU binding and fresh visibility not yet verified. No world placement change.'))
            break
    if chosen:break
assert chosen is not None
entries[chosen['camera']['id']]=chosen['camera']
doc['cameras']=list(entries.values())
doc['r4_additional_target']=chosen
doc['r4_note']='Old camera poses unchanged. Add historical grey20/blue20 and one CPU-proposed R4 level3 target. Old g_dirt_level IDs name historical R3 cases; actual R4 levels require GPU readback. Wall/trailer views remain regression-only.'
(ART/'r4-baseline-cameras.json').write_text(json.dumps(doc,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(artifact_cameras=len(entries),additional_target=chosen)))
