"""Project explicit semantic building ROIs using Unity VERTICAL FOV, then inspect/measure real PNGs.
Masks are geometry proposals: annotated overlays must confirm they exclude trees/windows/pillars.
"""
import argparse
import json
import math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

parser=argparse.ArgumentParser();parser.add_argument('--phase',default='before');args=parser.parse_args()
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
spec=json.loads((ROOT/'Data/Regions/bialystok-industrial-c/generated/landmarks/fire_station_jrg2.spec.json').read_text())
d=spec['dims'];origin=np.array(d['axis']['origin_en']);u=np.array(d['axis']['u']);u/=np.linalg.norm(u);v=np.array([-u[1],u[0]]);floor=spec['anchor'][2]
cameras=json.loads((ROOT/'Data/Regions/bialystok-industrial-c/generated/control_cameras.json').read_text())['cameras']
cam=next(c for c in cameras if c['id']=='fire_station_ref7197');eye=np.array(cam['pos']);fw=np.array(cam['look_at'])-eye;fw/=np.linalg.norm(fw);right=np.cross(fw,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,fw)
def project(points,w,h):
    a=np.array(points);en=origin+a[:,:1]*u+a[:,1:2]*v;world=np.c_[en,a[:,2]+floor];delta=world-eye
    focal=h/(2*math.tan(math.radians(cam['fov_deg'])/2));depth=delta@fw
    return np.c_[w/2+focal*(delta@right)/depth,h/2-focal*(delta@up)/depth]
def box(u0,u1,v0,z0,z1):return [[u0,v0,z0],[u1,v0,z0],[u1,v0,z1],[u0,v0,z1]]
regions={
 'P1_gable_paint':{'type':'plaster','points':box(37.0,38.15,-.03,6.15,7.75)},
 'P2_wing_paint':{'type':'plaster','points':box(19.4,21.0,.17,6.05,6.40)},
 'P3_tower_paint':{'type':'plaster','points':box(22.05,22.65,5.97,8.7,9.4)},
 'P4_wing_lower_paint':{'type':'plaster_check_tree_occlusion','points':box(27.0,27.4,.17,3.0,3.8)},
 'P5_gable_lower_paint':{'type':'plaster_check_tree_occlusion','points':box(42.15,42.65,-.03,4.2,4.8)},
 'R1_round_glass':{'type':'round_glass','points':box(41.35,41.85,-.08,7.6,8.05)},
 'G1_left_glass_upper':{'type':'glass','points':box(39.05,39.85,-.08,4.45,4.85)},
 'G2_left_glass_mid':{'type':'glass','points':box(39.05,39.85,-.08,2.75,3.25)},
 'G3_right_glass_upper':{'type':'glass_may_be_occluded_before','points':box(44.95,45.75,-.08,4.45,4.85)},
 'G4_right_glass_mid':{'type':'glass_may_be_occluded_before','points':box(44.95,45.75,-.08,2.75,3.25)},
}
records={};out=OUT/(args.phase+'-roi');out.mkdir(exist_ok=True)
colors=[(255,60,40),(255,180,0),(230,0,230),(255,80,180),(200,120,255),(255,255,0),(0,255,255),(0,200,255),(150,255,0),(0,255,130)]
for tier in ('Low','High'):
 for light in ('clear','overcast'):
    path=OUT/args.phase/f'{tier}-{light}'/'fire-station-ref7197.png'
    if not path.exists():continue
    im=Image.open(path).convert('RGB');rgb=np.array(im);h,w=rgb.shape[:2]
    annotation=im.copy();dr=ImageDraw.Draw(annotation);row={}
    for (name,region),color in zip(regions.items(),colors):
        poly=project(region['points'],w,h);mask=Image.new('L',(w,h));ImageDraw.Draw(mask).polygon([tuple(p) for p in poly],fill=255)
        keep=np.array(mask)>0;data=rgb[keep];assert len(data)>0
        lum=data@np.array([.2126,.7152,.0722]);srgb=data/255;linear=np.where(srgb<=.04045,srgb/12.92,((srgb+.055)/1.055)**2.4)
        row[name]={'type':region['type'],'native_polygon':poly.tolist(),'pixels':len(data),'median_rgb_srgb':np.median(data,axis=0).tolist(),
                   'mean_rgb_srgb':data.mean(0).tolist(),'p10_p50_p90_luminance_srgb':np.percentile(lum,[10,50,90]).tolist(),'mean_linear_luminance':float((linear@np.array([.2126,.7152,.0722])).mean()),
                   'validity':'PROPOSED mask; verify annotated overlay before using as semantic evidence'}
        dr.line([tuple(p) for p in poly]+[tuple(poly[0])],fill=color,width=5);dr.text(tuple(poly[0]),name[:2],fill=color,stroke_width=1,stroke_fill='black')
        mask.save(out/f'{tier}-{light}-{name}.png')
    annotation.thumbnail((960,960));sheet=Image.new('RGB',(960,690),'white');sheet.paste(annotation,(0,0));sd=ImageDraw.Draw(sheet)
    sd.text((8,450),args.phase+' '+tier+' '+light+' / Unity vertical FOV; proposed semantic ROIs, manual verification REQUIRED',fill='black')
    for i,(name,data) in enumerate(row.items()):sd.text((8,472+i*18),name+': '+str(data['median_rgb_srgb'])+' Y50='+str(round(data['p10_p50_p90_luminance_srgb'][1],2)),fill='black')
    sheet.save(out/f'{tier}-{light}-semantic.jpg',quality=95);records[f'{tier}-{light}']=row
(out/'measurements.json').write_text(json.dumps({'camera':cam,'fov_convention':'Unity vertical; native2340x1080','definitions':regions,'results':records},indent=2))
print(json.dumps({k:{n:{'RGB50':r['median_rgb_srgb'],'Y50':r['p10_p50_p90_luminance_srgb'][1]} for n,r in v.items()} for k,v in records.items()},indent=2))
