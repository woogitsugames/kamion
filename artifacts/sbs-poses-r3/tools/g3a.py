import json, math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import poselib as P
R,O=P.refs(),P.overrides()
cid='sbs-g3-a-320326319617139'
pr={c['id']:c for c in json.load(open('C:/Users/matma/Documents/Claude/kamion/artifacts/biezenstwa-island/cams_sbs.json',encoding='utf-8'))['cameras']}['sbs-g3-a-p0128-320326319617139']
print('current ov',json.dumps(O.get(cid)))
_,inf0=P.camera(R[cid],{k:v for k,v in O.get(cid,{}).items() if k!='heading_delta_deg'})
e,n,u=pr['pos']; la=pr['look_at']
hd=math.degrees(math.atan2(la[0]-e,la[1]-n))%360
pitch=math.degrees(math.atan2(la[2]-u,math.hypot(la[0]-e,la[1]-n)))
vf=pr['fov_deg']; hz=(math.tan(math.radians(pitch))/math.tan(math.radians(vf/2))+1)/2
print('probe heading',hd,'pitch',pitch,'hz',hz,'gps',inf0['gps_en'],'base heading',inf0['heading'])
for k in ('sbs-g3-a-482392746429891',):
    print(k, json.dumps({a:b for a,b in O.get(k,{}).items() if a not in('note',)}))
    _,i=P.camera(R[k],{}); print('gps',i['gps_en'],'heading',i['heading'], R[k]['captured_at'], R[k]['author'], R[k]['heading_original_deg'], R[k]['projection'].get('computed_geometry'), R[k]['projection'].get('geometry'))
r=R[cid]; print('320326', r['captured_at'], r['author'], r['projection'].get('computed_geometry'), r['projection'].get('geometry'))
