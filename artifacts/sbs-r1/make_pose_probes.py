"""Reproducible J2 XY, J1 metadata/horizon and early-route Commons pose probes."""
import copy,sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/refs'))
import sbs_gate3 as s
SHIFT={'1259231227807789','751431972202262','500263111404933','209622370971977','810525063224609','468026894483428','4312632558767412','1528935774382039'}
J1={'810896133189484','339463879238809','962702164479831','182011943700132','326454015490067','1406533339711789'}
refs={r['camera']:r for r in s.read(s.REGION/'sbs_references.json')['references']}
alternatives={r['camera']:r for r in s.read(s.ROOT/'artifacts/sbs-r1/calibration-candidates.json')['j1_metadata_alternatives']}
probes=[];mapping=[]
def add(camera,dx=0,dy=0,dh=0,horizon=None,hfov=None,label=''):
    ref=refs[camera['id']];c=copy.deepcopy(camera);c['id']+=f'-probe-{len([p for p in mapping if p["camera"]==camera["id"]]):02d}'
    for field in ('pos','look_at'):c[field][0]+=dx;c[field][1]+=dy
    vfov=s.vfov(hfov,ref['width']/ref['height']) if hfov is not None else camera['fov_deg']
    hy=ref['horizon_y_fraction'] if horizon is None else horizon
    pitch=math.degrees(math.atan((2*hy-1)*math.tan(math.radians(vfov)/2)))
    e,n,u=c['pos'];c['look_at']=s.pose(e,n,u,ref['heading_grid_deg']+dh,pitch);c['fov_deg']=vfov
    probes.append(c)
    mapping.append({'probe':c['id'],'camera':camera['id'],'east_delta_m':round(dx,4),'north_delta_m':round(dy,4),'heading_delta_deg':round(dh,4),'horizon':hy,'horizontal_fov_deg':hfov,'label':label or f'E {dx:+.1f} N {dy:+.1f} H {dh:+.1f}','width':ref['width'],'height':ref['height']})
for camera in s.read(s.REGION/'sbs_cameras.json')['cameras']:
    sid=camera['id'].rsplit('-',1)[-1];ref=refs[camera['id']]
    if sid in SHIFT:
        for dx in (-5.5,0,5.5):
            for dy in (-5.5,0,5.5):add(camera,dx,dy)
    elif sid in ('cm109685822','cm92458760'):
        for dh in (-12,0,12):
            for hfov in (60,70,80):add(camera,dh=dh,hfov=hfov,label=f'heading {dh:+d} deg, HFOV {hfov}')
    elif sid in ('962702164479831','810896133189484','1406533339711789'):
        original=alternatives[camera['id']]['original_heading_delta_deg']
        headings=(0,35,original) if abs(original)>20 else (-30,0,30)
        direction=math.radians(ref['heading_grid_deg']+original)
        for dh in headings:
            for lateral in (-3,0,3):add(camera,math.cos(direction)*lateral,-math.sin(direction)*lateral,dh)
    elif sid=='326454015490067':
        for dh in (-5,0,5):
            for hy in (ref['horizon_y_fraction'],0.84,0.8911804):add(camera,dh=dh,horizon=hy,label=f'heading {dh:+d} deg, horizon {hy:.3f}')
    elif sid in ('339463879238809','182011943700132'):
        alt=alternatives[camera['id']];dx=alt['original_gps_east_delta_from_current_m'];dy=alt['original_gps_north_delta_from_current_m']
        for dh in (0,alt['original_heading_delta_deg'],15):
            for scale in (0,0.5,1):add(camera,dx*scale,dy*scale,dh,label=f'original GPS x{scale:.1f}, heading {dh:+.1f}')
s.write(s.REGION/'sbs_pose_probes.json',{'schema':'kamion/sbs-cameras/1','frame':'E,N,absolute U','cameras':probes})
s.write(s.ROOT/'artifacts/sbs-r1/pose-probes.json',{'probes':mapping,'note':'Diagnostic candidates only, altitude fixed. No accepted pose corrections. At most nine candidates per source photo.'})
print('Prepared',len(probes),'pose probes for',len({p['camera'] for p in mapping}),'photos')
