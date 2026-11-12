import sys, math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import poselib as P
e0,n0,rad=map(float,sys.argv[1:4])
for pts,a in P.road_edges():
    best=min(((math.hypot(p[0]-e0,p[1]-n0),i) for i,p in enumerate(pts)))
    # segment distance
    dm=1e9
    for p,q in zip(pts,pts[1:]):
        vx,vy=q[0]-p[0],q[1]-p[1]; L=vx*vx+vy*vy or 1e-9
        t=max(0,min(1,((e0-p[0])*vx+(n0-p[1])*vy)/L)); x,y=p[0]+t*vx,p[1]+t*vy
        d=math.hypot(e0-x,n0-y)
        if d<dm: dm=d; side=(vx*(n0-p[1])-vy*(e0-p[0]))/math.sqrt(L); hd=math.degrees(math.atan2(vx,vy))%360
    if dm<rad: print(round(dm,1),'side(+left)',round(side,1),'hd',round(hd,1),a.get('name'),a.get('highway'),'ow',a.get('oneway'),'ln',a.get('lanes'),'br',a.get('bridge'),'layer',a.get('layer'),'w',a.get('width'))
