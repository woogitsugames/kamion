import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import poselib as P
R,O=P.refs(),P.overrides()
prod={c['id']:c for c in P.S.read(P.REGION/'sbs_cameras.json')['cameras']}
cid='sbs-g3-b-494288258686575'; c=prod[cid]
r=R[cid]; x,y=P.TR.transform(*r['projection']['geometry']['coordinates'])
og=[x-P.ORIGIN['x'],y-P.ORIGIN['y']]; print('orig gps',og)
oc={'pos':og+[0],'look_at':[og[0]-30,og[1]+25,0]}
P.draw_map('../maps/494288-wide.png', [-560,20], 150, [('prod',c,'red',41.8),('orig',oc,'yellow',41.8)], scale=3)
# list nearby edges
for pts,a in P.road_edges():
    if any(abs(p[0]+540)<80 and abs(p[1]-15)<60 for p in pts) and a.get('bridge'):
        print(a.get('name'),a.get('oneway'),a.get('lanes'),a.get('bridge'),[ (round(p[0],1),round(p[1],1)) for p in pts][:12])
