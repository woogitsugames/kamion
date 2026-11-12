import sys, json, math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import poselib as P
prod={c['id']:c for c in P.S.read(P.REGION/'sbs_cameras.json')['cameras']}
pr=json.load(open('C:/Users/matma/Documents/Claude/kamion/artifacts/biezenstwa-island/cams_sbs.json',encoding='utf-8'))['cameras']
pr={c['id']:c for c in pr}
a=prod['sbs-g3-a-482392746429891']; b=prod['sbs-g3-a-320326319617139']; c=pr['sbs-g3-a-p0128-320326319617139']
for x in (a,b,c):
    h=math.degrees(math.atan2(x['look_at'][0]-x['pos'][0],x['look_at'][1]-x['pos'][1]))%360
    print(x['id'],x['pos'],round(h,2))
# bearing ray of the blue board from 482392
e,n=a['pos'][:2]; h=math.radians(242.7+37.4)
ray={'pos':[e,n,0],'look_at':[e+40*math.sin(h),n+40*math.cos(h),0]}
P.draw_map('../maps/482392.png',[530,-688],35,[('482',a,'red',90),('320',b,'yellow',90),('p128',c,'cyan',90),('board',ray,'white',0.5)],scale=8)
