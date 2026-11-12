import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import poselib as P
R,O=P.refs(),P.overrides()
prod={c['id']:c for c in P.S.read(P.REGION/'sbs_cameras.json')['cameras']}
for k,half in (('494288258686575',60),('810896133189484',60),('837235577143499',60)):
    cid='sbs-g3-b-'+k; c=prod[cid]; cam,inf=P.camera(R[cid],O[cid])
    gps,_=P.camera(R[cid],{})
    print(k, 'pos',c['pos'],'gps',[round(v,2) for v in inf['gps_en']],'head',round(inf['heading'],2),'hfov',round(inf['hfov'],2),'axis',P.road_axis(c['pos'][:2]))
    P.draw_map(f'../maps/{k[:6]}-prod.png', c['pos'][:2], half, [('prod',c,'red',inf['hfov']),('gps',gps,'yellow',inf['hfov'])])
