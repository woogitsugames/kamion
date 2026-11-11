"""Reproducible J2 XY pose-only sweep, without world edits."""
import copy,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/refs'))
import sbs_gate3 as s
SHIFT={'1259231227807789','751431972202262','500263111404933','209622370971977','810525063224609','468026894483428','4312632558767412','1528935774382039'}
refs={r['camera']:r for r in s.read(s.REGION/'sbs_references.json')['references']}
probes=[];mapping=[]
for camera in s.read(s.REGION/'sbs_cameras.json')['cameras']:
    if camera['id'].rsplit('-',1)[-1] not in SHIFT: continue
    for dx in (-5.5,0,5.5):
        for dy in (-5.5,0,5.5):
            c=copy.deepcopy(camera);c['id']+=f'-xy-{dx:+g}-{dy:+g}'
            for field in ('pos','look_at'):c[field][0]+=dx;c[field][1]+=dy
            probes.append(c);ref=refs[camera['id']]
            mapping.append({'probe':c['id'],'camera':camera['id'],'east_delta_m':dx,'north_delta_m':dy,'width':ref['width'],'height':ref['height']})
s.write(s.REGION/'sbs_pose_probes.json',{'schema':'kamion/sbs-cameras/1','frame':'E,N,absolute U','cameras':probes})
s.write(s.ROOT/'artifacts/sbs-r1/pose-probes.json',{'probes':mapping,'note':'XY grid at -5.5/0/+5.5m, altitude and heading fixed. WORKING_VALUE candidates, not accepted corrections.'})
print('Prepared',len(probes),'XY probes')
