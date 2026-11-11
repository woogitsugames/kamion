"""Actual interior thuja ROI colors, same authored crown positions in Low/High; no source-only color PASS."""
import argparse,hashlib,json,math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
p=argparse.ArgumentParser();p.add_argument('phase');p.add_argument('--low-control',default=None);p.add_argument('--light',choices=['clear','overcast'],default='overcast');a=p.parse_args();R=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent;S=json.loads((R/'Data/Regions/bialystok-industrial-c/generated/landmarks/fire_station_jrg2.spec.json').read_text());axis=S['dims']['axis'];au=np.array(axis['u']);au/=np.linalg.norm(au);av=np.array([-au[1],au[0]]);cam=next(c for c in json.loads((R/'Data/Regions/bialystok-industrial-c/generated/control_cameras.json').read_text())['cameras'] if c['id']=='fire_station_ref7197');eye=np.array(cam['pos']);fw=np.array(cam['look_at'])-eye;fw/=np.linalg.norm(fw);right=np.cross(fw,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,fw);w,h=2340,1080
h01=lambda *k:int(hashlib.sha1(repr(k).encode()).hexdigest()[:8],16)/0xFFFFFFFF

def project(p):
 d=np.array(p)-eye;f=h/(2*math.tan(math.radians(cam['fov_deg'])/2));z=d@fw;return np.c_[w/2+f*(d@right)/z,h/2-f*(d@up)/z]

polys={}
for e,n,z,height,radius,key in S['ground']['thuja']:
 if height<3.8:continue
 lean=(au*(h01(key,'lx')-.5)+av*(h01(key,'ly')-.5))*.3
 points=[]
 for side,f in [(-1,.55),(1,.55),(1,.72),(-1,.72)]:
  en=np.array([e,n])+lean*f*f+right[:2]*radius*.15*side;points.append([*en,z+height*f])
 polys[str(key)]=project(points).tolist()
out=O/(a.phase+'-thuja'+('-clear' if a.light=='clear' else ''));out.mkdir(exist_ok=True);records={}
for tier in ('Low','High'):
 source_phase=a.low_control if tier=='Low' and a.low_control else a.phase
 path=O/source_phase/(tier+'-'+a.light)/'fire-station-ref7197.png'
 if not path.exists():continue
 im=Image.open(path).convert('RGB');rgb=np.array(im).astype(int);annotation=im.copy();dr=ImageDraw.Draw(annotation);row={}
 for key,poly in polys.items():
  mask=Image.new('L',(w,h));ImageDraw.Draw(mask).polygon([tuple(x) for x in poly],fill=255);keep=np.array(mask)>0;data=rgb[keep];lum=data@np.array([.2126,.7152,.0722]);leaf=((data[:,1]-data[:,0]>=2)&(data[:,1]-data[:,2]>=1))|(lum<40)
  if not leaf.any():continue
  Y=lum[leaf];row[key]={'habit':int(key)%3,'roi_pixels':len(data),'green_or_dark_coverage':float(leaf.mean()),'leaf_pixels':int(leaf.sum()),'RGB50':np.median(data[leaf],axis=0).tolist(),'Y10_50_90':np.percentile(Y,[10,50,90]).tolist()};dr.line([tuple(x) for x in poly]+[tuple(poly[0])],fill=(255,60,40),width=3);dr.text(tuple(poly[0]),key,fill=(255,255,0))
 annotation.thumbnail((960,960));annotation.save(out/(tier+'-roi.jpg'),quality=95);records[tier]=row
comparison={}
for key in records.get('Low',{}).keys()&records.get('High',{}).keys():
 low,high=records['Low'][key],records['High'][key]
 if min(low['green_or_dark_coverage'],high['green_or_dark_coverage'])>=.8:
  comparison[key]={'LowY50':low['Y10_50_90'][1],'HighY50':high['Y10_50_90'][1],'High_over_Low':high['Y10_50_90'][1]/low['Y10_50_90'][1]}
(out/'metrics.json').write_text(json.dumps({'lighting':a.light,'Low_control_phase':a.low_control,'method':'Fixed source crown interior at55-72%height, +/-15%radius, authored lean. Excludes shortplants<3.8m to avoid fence. Green-or-dark mask retains shadow; ROI is NOT exact leaf segmentation. Only>=80%coverage pairs compared; inspect annotations. Rendering profiles differ in shadows/resScale.','polygons':polys,'records':records,'comparison':comparison},indent=2));print(json.dumps(comparison,indent=2))
