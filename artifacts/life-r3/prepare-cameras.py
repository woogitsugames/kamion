"""Additional inspection poses from actual instances; never edits placement data."""
import json, math, hashlib
from collections import defaultdict
from pathlib import Path
from shapely.geometry import shape, Polygon, LineString
from shapely.affinity import translate
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).parent
packet = json.loads((ROOT/'artifacts/life-r2/cameras.json').read_text(encoding='utf-8-sig'))
original_packet_ids = {c['id'] for c in packet['cameras']}
manifest = json.loads((ROOT/'Data/Regions/bialystok-industrial-c/generated/world_manifest.json').read_text())
vehicles = []
for chunk in manifest['chunks']:
    vehicles += [v for v in json.loads((ROOT/chunk['instances']['file']).read_text())['instances']
                 if v['p'].startswith(('car_', 'van_', 'trailer_', 'tractor_'))]
origin = manifest['origin_epsg2180']
obstacles = [translate(shape(f['geometry']), -origin['x'], -origin['y']) for f in
             json.loads((ROOT/'Data/Regions/bialystok-industrial-c/buildings.geojson').read_text())['features']]
building_count = len(obstacles)

def xy(v, x, y):
    c, s = math.cos(v['yaw']), math.sin(v['yaw'])
    return v['e']+c*x-s*y, v['n']+s*x+c*y

for v in vehicles:
    a,b,c,d = (-1.3,1.3,0,13.6) if v['p'].startswith('trailer_') else (
        (-1.25,1.25,-1.7,4.6) if v['p'].startswith('tractor_') else (-1.05,1.05,-2.5,2.5))
    obstacles.append(Polygon([xy(v,a,c),xy(v,b,c),xy(v,b,d),xy(v,a,d)]))
tree = STRtree(obstacles)

def hits(pos, target, ignored=()):
    return [int(i) for i in tree.query(LineString([pos[:2], target[:2]]), predicate='intersects')
            if int(i) not in ignored]

selected=[]
for proto, label in [('car_hatch_black','black'), ('car_estate_white','white')]:
    choices=[]
    for idx,v in enumerate(vehicles):
        if v['p'] != proto: continue
        cameras=[]
        for view,dx,dy,h in [('rear5',2.8,-6,1.3),('side5',6,0,1.3),('wheel2',3,1,0.5)]:
            options=[]
            for sign in (-1,1):
                x,y=xy(v,sign*dx,dy)
                tx,ty=xy(v,sign*.65 if view=='wheel2' else 0,1 if view=='wheel2' else -1.1 if view=='rear5' else 0)
                pos=[x,y,v['z']+h]; target=[tx,ty,v['z']+(.32 if view=='wheel2' else .75)]
                blocked=hits(pos,target,(building_count+idx,))
                options.append((len(blocked),sign,pos,target,blocked))
            n,sign,pos,target,blocked=min(options,key=lambda c:c[:2])
            cameras.append(dict(id=f'life3_{label}_{view}',type='persp',kind='inspection',seat='yard',
                                pos=pos,look_at=target,fov_deg=40 if view!='wheel2' else 35,
                                note=f"Actual {v['src']}; 2D obstacle count {n}; visual visibility and GPU dirt level UNVERIFIED",
                                target_instance=v,obstacle_count=n,target_distance_m=math.dist(pos,target)))
        score=sum(c['obstacle_count'] for c in cameras)
        choices.append((score,(v['e']-700)**2+(v['n']+450)**2,v,cameras))
    if not choices: raise RuntimeError(f'Missing prototype {proto}')
    _,_,v,cams=min(choices,key=lambda c:c[:2])
    selected.append(dict(role=label,instance=v,cameras=cams)); packet['cameras']+=cams

rows=defaultdict(list)
for idx,v in enumerate(vehicles):
    if v['p'].startswith(('car_','van_')):
        rows[v['src'].split('#')[0]].append((idx,v))
fleets=[]
for key,row in rows.items():
    if len(row)<6: continue
    center=dict(e=sum(v['e'] for _,v in row)/len(row),n=sum(v['n'] for _,v in row)/len(row),
                z=sum(v['z'] for _,v in row)/len(row),yaw=row[0][1]['yaw'])
    if max(math.hypot(v['e']-center['e'],v['n']-center['n']) for _,v in row)>22: continue
    ignored={building_count+i for i,_ in row}
    for direction in (-1,1):
        cams=[]; total=0
        for distance in (20,35,45):
            x,y=xy(center,0,direction*distance)
            pos=[x,y,center['z']+2.3]; target=[center['e'],center['n'],center['z']+.8]
            n=len(hits(pos,target,ignored)); total+=n
            cams.append(dict(id=f'sheet_far_{distance}',type='persp',kind='inspection',seat='yard',pos=pos,look_at=target,
                             fov_deg=40,note=f"Actual row {key}, {len(row)} cars/vans, horizontal distance {distance} m; 2D obstacles {n}; visual review required"))
        fleets.append((total,-len(row),key,direction,cams,row))
if not fleets: raise RuntimeError('No actual fleet row with at least six cars')
_,_,key,direction,cams,row=min(fleets,key=lambda x:x[:4])
packet['cameras']+=cams
assert len({c['id'] for c in packet['cameras']})==len(packet['cameras'])
route=json.loads((OUT/'route-camera-ids.json').read_text(encoding='utf-8-sig'))['ids']
assert original_packet_ids<={c['id'] for c in packet['cameras']}
# Most inherited route IDs live in the native scene rather than this additive
# packet. Capture validation requires the union and checks every route ID.
(OUT/'cameras.json').write_text(json.dumps(packet,indent=2),encoding='utf-8')
(OUT/'camera-targets.json').write_text(json.dumps(dict(selected=selected,fleet_row=key,fleet=[v for _,v in row],
    manifest_sha=hashlib.sha256((ROOT/'Data/Regions/bialystok-industrial-c/generated/world_manifest.json').read_bytes()).hexdigest(),
    camera_count=len(packet['cameras']),route_count=len(route),new_camera_count=9),indent=2),encoding='utf-8')
print(json.dumps(dict(cameras=len(packet['cameras']),route=len(route),fleet=len(row),selected=[s['instance']['src'] for s in selected])))
