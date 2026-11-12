import json,runpy,math
from pathlib import Path
from shapely.geometry import LineString
out=Path(__file__).parent
s=runpy.run_path(str(out/'prepare-cameras-v2.py'))
vehicles,tree,base,xy=s['vehicles'],s['tree'],s['base'],s['xy']
packet=json.loads((out/'cameras.json').read_text(encoding='utf-8-sig'))
packet['cameras']=[c for c in packet['cameras'] if not c['id'].endswith('_lod22')]
selected=[]
for proto in ('tractor_white','tractor_blue'):
    choices=[]
    for index,i in enumerate(vehicles):
        if i['p']!=proto:continue
        for sign in (-1,1):
            pos=xy(i,sign*22,1.4)
            # The centre ray can miss an occluder hiding the cab. Test the
            # cab centre and both axle ends as well as the chassis centre.
            hits=0
            for x,y in ((0,1.4),(0,3.5),(-1,-.55),(1,-.55),(-1,3.15),(1,3.15)):
                ray=LineString([pos,xy(i,x,y)])
                hits+=sum(int(v)!=base+index for v in tree.query(ray,predicate='intersects'))
            choices.append((hits,(i['e']-680)**2+(i['n']+510)**2,i,pos))
    hits,_,i,pos=min(choices,key=lambda v:v[:2])
    assert hits==0,(proto,hits)
    target=xy(i,0,1.4)
    packet['cameras'].append(dict(id=f'yard_{proto}_lod22',type='persp',kind='inspection',seat='file',pos=[*pos,i['z']+2.2],look_at=[*target,i['z']+1.25],fov_deg=60,note=f"Actual {i['src']}; 22 m, six clear rays across cab and axles; validate PNG"))
    selected.append(i)
(out/'cameras-v3.json').write_text(json.dumps(packet,indent=2),encoding='utf-8')
(out/'tractor-lod-targets.json').write_text(json.dumps(selected,indent=2),encoding='utf-8')
print(json.dumps(dict(packet_cameras=len(packet['cameras']),clear_tractor_probes=len(selected))))
