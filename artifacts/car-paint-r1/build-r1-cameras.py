"""Actual instance dirt cases and frozen old/partial-LOD cameras. Never changes world placements."""
from pathlib import Path
import json,math,sys
import numpy as np
import yaml
from shapely.geometry import Polygon,LineString,Point,shape
from shapely.affinity import translate
from shapely.strtree import STRtree

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'artifacts/car-paint-r1'
sys.path.insert(0,str(ROOT/'tools/worldgen'))
from streetscape import life_cars as LC
proof=json.loads((OUT/'instanced-film-gpu-proof.json').read_text())
assert len(proof['examples'])==4 and all(c['pass'] for c in proof['cases'])
region=ROOT/'Data/Regions/bialystok-industrial-c'
manifest=json.loads((region/'generated/world_manifest.json').read_text())
origin=yaml.safe_load((region/'region.yaml').read_text())['origin']
cars=[]
for c in manifest['chunks']:
    cars += [i for i in json.loads((ROOT/c['instances']['file']).read_text())['instances'] if i['p'].startswith(('car_','van_'))]
footprints=[]
for car in cars:
    d=LC.VAN if car['p'].startswith('van_') else LC.CARS[car['p'].split('_')[1]]
    right=np.array([math.cos(car['yaw']),math.sin(car['yaw'])]);front=np.array([-right[1],right[0]])
    centre=np.array([car['e'],car['n']])
    footprints.append(Polygon([centre+right*x*d['W']/2+front*y*d['L']/2 for x,y in [(-1,-1),(1,-1),(1,1),(-1,1)]]).buffer(.08))
buildings=[translate(shape(f['geometry']),-origin['x'],-origin['y']) for f in json.loads((region/'buildings.geojson').read_text())['features']]
tree=STRtree(footprints+buildings)
base=json.loads((OUT/'qa-cameras.json').read_text());entries={c['id']:c for c in base['cameras']}
for c in json.loads((OUT/'pearl-cameras.json').read_text())['cameras']:entries[c['id']]=c
cases=[]
for example in proof['examples']:
    index=min(range(len(cars)),key=lambda j:math.hypot(cars[j]['e']-example['e'],cars[j]['n']-example['n']))
    car=cars[index];assert car['p']==example['prototype'] and math.hypot(car['e']-example['e'],car['n']-example['n'])<.01
    centre=np.array([car['e'],car['n']]);d=LC.CARS[car['p'].split('_')[1]]
    right=np.array([math.cos(car['yaw']),math.sin(car['yaw'])]);front=np.array([-right[1],right[0]])
    samples=[centre]+[centre+right*x*d['W']*.35+front*y*d['L']*.4 for x in (-1,1) for y in (-1,1)]
    chosen=None
    for deg in [0]+[sign*delta for delta in range(5,181,5) for sign in (1,-1)]:
        theta=car['yaw']+math.radians(deg);eye=centre+5*np.array([math.cos(theta),math.sin(theta)])
        clear=True
        for sample in samples:
            ray=LineString([sample,eye])
            hits=tree.query(ray,predicate='intersects')
            if any(int(h)!=index for h in hits):clear=False;break
        if clear:chosen=eye;break
    if chosen is None:raise RuntimeError('No raw-footprint-clear camera for actual GPU example level'+str(example['level']))
    camera=dict(id=f"g_dirt_level_{example['level']}",type='persp',kind='photo_match',fov_deg=45,
        pos=[*map(float,chosen),car['z']+1.6],look_at=[car['e'],car['n'],car['z']+.7],
        note=f"WORKING_VALUE QA: actual GPU-proven paint film level{example['level']}/3; {car['p']}; {car['src']}. Raw vehicle/building footprints checked, visual review still required. No world placement edit.")
    entries[camera['id']]=camera;cases.append(dict(gpu=example,instance=car,camera=camera))
base['cameras']=list(entries.values());base['dirt_case_sources']=cases
base['note']='Original fixed cameras retained. Historical blocked views are regression-only. New far views claim visible rear/body ROI only; no whole-car claim. Four current dirt cases use actual GPU-proven same-prototype instances.'
(OUT/'r1-cameras.json').write_text(json.dumps(base,indent=2)+'\n',encoding='utf-8')
print('Prepared',len(entries),'additional-camera entries with4 actual same-prototype GPU dirt cases; visual review required.')
