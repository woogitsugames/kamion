"""Supplemental QA poses: reject sight lines crossing source buildings or other parked vehicles.

Collision alone omits some rendered walls. These are working QA poses, always
checked visually afterwards; no map/content modifications are made.
"""
import json
import math
import sys
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import LineString, Polygon
import yaml

root = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/'tools/worldgen'))
from streetscape import buildings_mesh as BM, life_cars as LC, life_props as LP
from roads import pipeline

rid = 'bialystok-industrial-c'
region = root/'Data/Regions'/rid
config = yaml.safe_load((region/'region.yaml').read_text(encoding='utf-8'))
origin = np.array([config['origin']['x'],config['origin']['y']])
buildings = BM.load(json.loads((region/'buildings.geojson').read_text()),origin,pipeline.load_overrides(rid))
obstacles = [b['poly'].buffer(.35) for b in buildings]
items = []
for f in (root/'Data/raw/derived'/rid/'world').glob('instances_*.json'):
    items.extend(i for i in json.loads(f.read_text())['instances'] if i['p'].startswith(('car_','van_','tractor_','trailer_')))

def rotate(item,v):
    c,s=math.cos(item.get('yaw',0)),math.sin(item.get('yaw',0))
    return np.array([c*v[0]-s*v[1],s*v[0]+c*v[1]])

def footprint(item):
    p=item['p']
    if p.startswith('car_'):
        spec=LC.CARS[p.split('_')[1]]; w,L=spec['W'],spec['L']; a,b=-L/2,L/2
    elif p.startswith('van_'):
        w,L=LC.VAN['W'],LC.VAN['L'];a,b=-L/2,L/2
    elif p.startswith('trailer_'):
        w,a,b=LP.TRAILER_W,0,LP.TRAILER_L
    else:
        t=LP.TRACTOR;w=t['W'];a=-t['fw_ahead']-t['rear_oh'];b=-t['fw_ahead']+t['wb']+t['fh']
    center=np.array([item['e'],item['n']])
    return Polygon([center+rotate(item,v) for v in [(-w/2,a),(w/2,a),(w/2,b),(-w/2,b)]]).buffer(.05)

vehicle_offset=len(obstacles)
obstacles += [footprint(i) for i in items]
tree=shapely.STRtree(obstacles)
terrain=json.loads((region/'terrain.json').read_text())
raw=np.fromfile(root/terrain['encoding']['file'],dtype='<u2').reshape(2049,2049)
z=terrain['encoding']['offset_m']+raw*terrain['encoding']['scale_m_per_unit']

def ground(p):
    col=np.clip(p[0]+1024,0,2048);row=np.clip(1024-p[1],0,2048)
    i,j=int(col),int(row);i1,j1=min(i+1,2048),min(j+1,2048)
    u,v=col-i,row-j
    return float(z[j,i]*(1-u)*(1-v)+z[j,i1]*u*(1-v)+z[j1,i]*(1-u)*v+z[j1,i1]*u*v)

result=[];decisions=[]
for family in ['car_hatch_white','car_suv_black','tractor_blue','trailer_curtain_0','trailer_reefer_0']:
    candidates=sorted(((index,item) for index,item in enumerate(items) if item['p']==family and max(abs(item['e']),abs(item['n']))<900),key=lambda t:math.hypot(t[1]['e']-720,t[1]['n']+411))
    for tier in ['Low','High']:
        bounds=([16,42.5] if tier=='Low' else [37.5,127.5]) if family.startswith('car_') else ([20,50] if tier=='Low' else [60,150])
        for boundary in bounds:
            choice=None
            for index,item in candidates:
                center=np.array([item['e'],item['n']]); longitudinal=14.025 if family=='trailer_reefer_0' else 6.8 if family.startswith('trailer_') else 1.3 if family.startswith('tractor_') else 0
                look=center+rotate(item,[0,longitudinal]);lookz=item['z']+(3.32 if family=='trailer_reefer_0' else 2 if family.startswith(('tractor_','trailer_')) else .8)
                for angle in np.arange(48)*2*math.pi/48+math.atan2(.6,.8):
                    direction=np.array([math.cos(angle),math.sin(angle)])
                    if family=='trailer_reefer_0' and direction[1]<.8:continue
                    direction=rotate(item,direction);poses=[]
                    for distance in [boundary-.1,boundary+.1]:
                        horizontal=distance
                        for _ in range(5):
                            p=center+direction*horizontal;h=ground(p)+2.5-item['z']
                            if abs(h)>=distance:break
                            horizontal=math.sqrt(distance*distance-h*h)
                        p=center+direction*horizontal;camera_z=ground(p)+2.5
                        if max(abs(p))>950 or abs(camera_z-item['z'])>=distance:break
                        line=LineString([p,look])
                        hits=tree.query(line,predicate='intersects')
                        if any(hit!=vehicle_offset+index for hit in hits):break
                        poses.append((distance,p,camera_z))
                    if len(poses)==2:
                        choice=(item,look,lookz,poses);break
                if choice:break
            if choice is None:raise RuntimeError(f'No clear source-footprint pose for {family} {tier} {boundary}')
            item,look,lookz,poses=choice
            decisions.append(dict(prototype=family,tier=tier,boundary=boundary,source=item,obstacle_method='source building polygons + other vehicle footprints; terrain height at camera; visual verification required'))
            for distance,p,camera_z in poses:
                result.append(dict(id=f'clear_{family}_{tier}_{distance:05.1f}'.replace('.','p'),kind='photo_match',seat='file',pos=[float(p[0]),float(p[1]),camera_z],look_at=[float(look[0]),float(look[1]),lookz],fov_deg=60,note='ADR0153 actual instance, source-footprint sightline clear, camera 2.5m above NMT. WORKING_VALUE QA pose, not a calibrated photo pose.'))
out=Path(__file__).parent
(out/'clear-cameras.json').write_text(json.dumps({'cameras':result},indent=2)+'\n',encoding='utf-8')
(out/'clear-view-decisions.json').write_text(json.dumps(decisions,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(cameras=len(result),building_obstacles=vehicle_offset,vehicle_obstacles=len(items))))
