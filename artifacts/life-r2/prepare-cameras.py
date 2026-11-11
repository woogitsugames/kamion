import json, math
from pathlib import Path
root=Path(__file__).resolve().parents[2]
out=Path(__file__).parent
packet=json.loads((root/'artifacts/life-r1/cameras.json').read_text(encoding='utf-8-sig'))
instances=[]
for p in sorted((root/'Data/raw/derived/bialystok-industrial-c/world').glob('instances_*.json')):
    instances.extend(json.loads(p.read_text())['instances'])
selected=[]
for prefix in ('trailer_curtain_0','trailer_curtain_3','trailer_reefer_0','tractor_white','tractor_blue'):
    group=[i for i in instances if i['p']==prefix]
    if not group: continue
    # Prefer near the existing inspection area; preserve exact identity and pose.
    i=min(group,key=lambda a:(a['e']-680)**2+(a['n']+510)**2)
    selected.append(i)
    def world(x,y,z):
        c,s=math.cos(i['yaw']),math.sin(i['yaw'])
        return [round(i['e']+c*x-s*y,4),round(i['n']+s*x+c*y,4),round(i['z']+z,4)]
    cy=4.36 if prefix.startswith('trailer') else 1.3
    for name,dx,dy,h in [('side8',8,0,1.5),('side35',35,0,1.7),('rear34',9,-10,2.2),('front34',9,10,2.2)]:
        packet['cameras'].append(dict(id=f'yard_{prefix}_{name}',type='persp',kind='inspection',seat='yard',pos=world(dx,cy+dy,h),look_at=world(0,cy,1.4),fov_deg=60,note=f"Actual instance {i['src']}; geometric inspection, not a photo-matched pose"))
packet['yard_note']='Actual static-vehicle instances; new views are inspection cameras, not geodetic photo matches. Exact poses frozen for before/after.'
(out/'cameras.json').write_text(json.dumps(packet,indent=2),encoding='utf-8')
(out/'yard-targets.json').write_text(json.dumps(selected,indent=2),encoding='utf-8')
print(json.dumps(dict(cameras=len(packet['cameras']),targets=[i['p'] for i in selected])))
