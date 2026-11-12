"""Sixteen diagnostic C poses; no production camera writes and no world generation."""
from pathlib import Path
import copy,json,math,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/refs'))
import sbs_gate3 as sbs
OUT=Path(__file__).with_name('pose-diagnostic182');OUT.mkdir(exist_ok=True)
camera=next(c for c in sbs.read(sbs.REGION/'sbs_cameras.json')['cameras'] if c['id']=='sbs-g3-b-182011943700132')
ref=next(r for r in sbs.read(sbs.REGION/'sbs_references.json')['references'] if r['camera']==camera['id'])
origin=sbs.read(sbs.REGION/'generated/world_manifest.json')['origin_epsg2180'];ground=sbs.ground_sampler()
dx,dy,dz=[a-b for a,b in zip(camera['look_at'],camera['pos'])]
heading=math.degrees(math.atan2(dx,dy))%360;pitch=math.degrees(math.atan2(dz,math.hypot(dx,dy)))
base_h=.5+math.tan(math.radians(pitch))/(2*math.tan(math.radians(camera['fov_deg']/2)))
variants=[(0,0,0,None)]
variants += [(east,0,yaw,None) for east in (3,6,9) for yaw in (-10,0,10)]
variants += [(6,0,yaw,horizon) for horizon in (.52,.57) for yaw in (-10,0)]
variants += [(6,north,-10,None) for north in (-15,15)]
assert len(variants)==16
cameras=[];rows=[]
for index,(east,north,yaw,horizon) in enumerate(variants):
    c=copy.deepcopy(camera);c['id']=f'sbs-probe182-{index:02d}';c['pose_confidence']='C';c['pose_reason']='Diagnostic hypothesis only; not approved'
    if index:
        e=camera['pos'][0]+east;n=camera['pos'][1]+north;u=ground(e+origin['x'],n+origin['y'])+2.2
        p=pitch if horizon is None else math.degrees(math.atan((2*horizon-1)*math.tan(math.radians(c['fov_deg']/2))))
        c['pos']=[round(e,4),round(n,4),round(u,4)];c['look_at']=sbs.pose(e,n,u,(heading+yaw)%360,p)
    c['note']='WORKING_VALUE grid around nearby ground road. NMT+2.2m, no deck inference, no world write.'
    cameras.append(c);rows.append({'probe':c['id'],'east_delta_m':east,'north_delta_m':north,'heading_delta_deg':yaw,
        'horizon_y_fraction':base_h if horizon is None else horizon,'pos':c['pos'],'look_at':c['look_at']})
(OUT/'cameras.json').write_text(json.dumps({'schema':'kamion/sbs-cameras/1','frame':'E,N,absolute U','cameras':cameras},indent=2)+'\n',encoding='utf-8')
(OUT/'plan.json').write_text(json.dumps({'base_camera':camera['id'],'comparison_photo':ref.get('comparison_photo',ref['photo']),
    'comparison_sha256':ref['comparison_sha256'],'author':ref['author'],'license':ref['license'],'page_url':ref['page_url'],
    'diagnostic_only':True,'all_pose_confidence':'C','note':'XY and yaw around graph ground road; pitch samples are hypotheses, not horizon calibration. Source graph projection is not proof of generated carriageway.','probes':rows},indent=2)+'\n',encoding='utf-8')
print('Prepared 16 C-only diagnostic cameras; production inputs untouched')
