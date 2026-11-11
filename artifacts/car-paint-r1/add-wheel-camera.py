"""QA-only source-derived camera; never changes vehicle placements."""
import json,math,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/worldgen'))
from streetscape import life_cars as LC
out=ROOT/'artifacts/car-paint-r1'
source=json.loads((out/'car_cams.json').read_text())
old=next(c for c in source['cameras'] if c['id']=='r10b_black_05')
manifest=json.loads((ROOT/'Data/Regions/bialystok-industrial-c/generated/world_manifest.json').read_text())
items=[]
for c in manifest['chunks']:
    items += [i for i in json.loads((ROOT/c['instances']['file']).read_text())['instances'] if i['p'].startswith('car_')]
target=min(items,key=lambda i:math.hypot(i['e']-old['look_at'][0],i['n']-old['look_at'][1]))
assert target['p']=='car_hatch_black' and math.hypot(target['e']-old['look_at'][0],target['n']-old['look_at'][1])<.05
d=LC.CARS['hatch'];sh=LC._Shell(d,0)
right=np.array([math.cos(target['yaw']),math.sin(target['yaw'])]);forward=np.array([-right[1],right[0]])
centre=np.array([target['e'],target['n']]);side=1 if np.dot(np.array(old['pos'][:2])-centre,right)>0 else -1
wheel=centre+right*(side*(d['W']/2+.01))+forward*sh.yfa
camera=wheel+right*(side*2)
entry=dict(id='g_current_black_wheel_02',type='persp',kind='photo_match',fov_deg=50,
    pos=[*map(float,camera),target['z']+d['r']+.15],look_at=[*map(float,wheel),target['z']+d['r']],
    note='WORKING_VALUE QA camera2m outside actual generated front wheel; no world placement changes; source '+target['src'])
result=dict(schema='truck-sim-pl/gate3-cameras/1',region='bialystok-industrial-c',cameras=[entry],source_instance=target,
            construction=dict(side=side,front_axle_y=float(sh.yfa),radius_m=d['r'],distance_horizontal_m=2.0))
(out/'wheel-cameras.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
