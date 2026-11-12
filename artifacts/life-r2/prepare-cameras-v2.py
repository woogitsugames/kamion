import json,math,time
from pathlib import Path
from shapely.geometry import shape,Polygon,LineString
from shapely.affinity import translate
from shapely.strtree import STRtree
started=time.monotonic()
root=Path(__file__).resolve().parents[2]; out=Path(__file__).parent
packet=json.loads((root/'artifacts/life-r1/cameras.json').read_text(encoding='utf-8-sig'))
vehicles=[]
for p in sorted((root/'Data/raw/derived/bialystok-industrial-c/world').glob('instances_*.json')):
    vehicles.extend(i for i in json.loads(p.read_text())['instances'] if i['p'].startswith(('trailer_','tractor_','car_','van_')))
origin=json.loads((root/'Data/Regions/bialystok-industrial-c/generated/world_manifest.json').read_text())['origin_epsg2180']
obstacles=[translate(shape(f['geometry']),-origin['x'],-origin['y']) for f in json.loads((root/'Data/Regions/bialystok-industrial-c/buildings.geojson').read_text())['features']]
base=len(obstacles)
def xy(i,x,y):
    c,s=math.cos(i['yaw']),math.sin(i['yaw'])
    return i['e']+c*x-s*y,i['n']+s*x+c*y
for i in vehicles:
    if i['p'].startswith('trailer_'): box=(-1.3,1.3,0,13.6)
    elif i['p'].startswith('tractor_'): box=(-1.25,1.25,-1.7,4.6)
    else: box=(-1.05,1.05,-2.5,2.5)
    a,b,c,d=box; obstacles.append(Polygon([xy(i,a,c),xy(i,b,c),xy(i,b,d),xy(i,a,d)]))
tree=STRtree(obstacles); selected=[]; audit=[]
for proto in ('trailer_curtain_0','trailer_curtain_3','trailer_reefer_0','tractor_white','tractor_blue'):
    candidates=[]
    for index,i in enumerate(vehicles):
        if i['p']!=proto: continue
        cy=4.36 if proto.startswith('trailer') else 1.3
        cams=[]
        for name,dx,dy,h in [('side8',8,0,1.5),('side35',35,0,1.7),('rear34',9,-10,2.2),('front34',9,10,2.2)]:
            choices=[]
            for sign in (-1,1):
                pos=xy(i,sign*dx,cy+dy); target=xy(i,0,cy)
                ray=LineString([pos,target]); hits=[int(v) for v in tree.query(ray,predicate='intersects') if int(v)!=base+index]
                choices.append((len(hits),sign,pos,target,hits))
            hits,sign,pos,target,ids=min(choices,key=lambda v:v[0])
            cams.append(dict(id=f'yard_{proto}_{name}',type='persp',kind='inspection',seat='yard',pos=[round(v,4) for v in (*pos,i['z']+h)],look_at=[round(v,4) for v in (*target,i['z']+0.95)],fov_deg=60,note=f"Actual {i['src']}; 2D sightline obstacle count {hits}; render verification required",obstacle_count=hits))
        score=sum(c['obstacle_count']==0 for c in cams)
        distance=(i['e']-680)**2+(i['n']+510)**2
        candidates.append((-score,sum(c['obstacle_count'] for c in cams),distance,i,cams))
    if not candidates: continue
    best=min(candidates,key=lambda v:v[:3]); i,cams=best[3:]
    selected.append(i); packet['cameras'].extend(cams)
    audit.append(dict(proto=proto,clear_views=-best[0],candidates=len(candidates),poses=[dict(id=c['id'],obstacles=c['obstacle_count']) for c in cams]))
(out/'cameras-v2.json').write_text(json.dumps(packet,indent=2),encoding='utf-8')
(out/'yard-targets-v2.json').write_text(json.dumps(selected,indent=2),encoding='utf-8')
(out/'camera-selection-v2.json').write_text(json.dumps(dict(seconds=time.monotonic()-started,results=audit),indent=2),encoding='utf-8')
print(json.dumps(dict(seconds=round(time.monotonic()-started,2),results=[dict(proto=a['proto'],clear_views=a['clear_views']) for a in audit])))
