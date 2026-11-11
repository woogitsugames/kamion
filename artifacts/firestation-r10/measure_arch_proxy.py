"""Actual pixel occlusion proxy in fixed projected opening/head masks; NOT a depth-buffer measurement."""
import argparse,json,math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
p=argparse.ArgumentParser();p.add_argument('phase');args=p.parse_args();R=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent;S=json.loads((R/'Data/Regions/bialystok-industrial-c/generated/landmarks/fire_station_jrg2.spec.json').read_text());D=S['dims'];A=json.loads((R/'art-source/world/landmarks/fire_station_jrg2/atlas_layout.json').read_text())['atlas']['arch'];axis=D['axis'];origin=np.array(axis['origin_en']);u=np.array(axis['u']);u/=np.linalg.norm(u);v=np.array([-u[1],u[0]]);cam=next(c for c in json.loads((R/'Data/Regions/bialystok-industrial-c/generated/control_cameras.json').read_text())['cameras'] if c['id']=='fire_station_ref7197');eye=np.array(cam['pos']);fw=np.array(cam['look_at'])-eye;fw/=np.linalg.norm(fw);right=np.cross(fw,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,fw);w,h=2340,1080

def project(p):
 a=np.array(p);en=origin+a[:,:1]*u+a[:,1:2]*v;world=np.c_[en,a[:,2]+S['anchor'][2]];delta=world-eye;f=h/(2*math.tan(math.radians(cam['fov_deg'])/2));z=delta@fw;return np.c_[w/2+f*(delta@right)/z,h/2-f*(delta@up)/z]

masks={};polys={}
for i,c in enumerate(D['hall']['arch_windows_u']):
 sill=D['hall']['arch_window_sill_z'];spring=A['spring'];width=A['w'];rise=A['rise']
 curve=[[c+x,-.08,sill+spring+rise*math.sqrt(max(0,1-(2*x/width)**2))] for x in np.linspace(width/2,-width/2,100)]
 for name,z0 in [('whole_opening',sill),('upper_head_above_spring',sill+spring)]:
  poly=project([[c-width/2,-.08,z0],[c+width/2,-.08,z0]]+curve);im=Image.new('L',(w,h));ImageDraw.Draw(im).polygon([tuple(x) for x in poly],fill=255);key=f'arch{i}_{name}';masks[key]=np.array(im)>0;polys[key]=poly.tolist()
records={};out=O/(args.phase+'-arch');out.mkdir(exist_ok=True)
for tier in ('Low','High'):
 board=Image.new('RGB',(960,540),'white');bd=ImageDraw.Draw(board)
 for row,phase in enumerate(('before',args.phase)):
  path=O/phase/(tier+'-overcast')/'fire-station-ref7197.png'
  if not path.exists():continue
  im=Image.open(path).convert('RGB');rgb=np.array(im).astype(int);rr,gg,bb=[rgb[:,:,i] for i in range(3)];Y=rgb@np.array([.2126,.7152,.0722]);green=((gg-rr>=2)&(gg-bb>=1))|(Y<40);view=rgb.copy();record={}
  for k,mask in masks.items():
   occ=mask&green;record[k]={'pixels':int(mask.sum()),'green_or_dark_occluder_pixels':int(occ.sum()),'non_occluder_proxy_fraction':float(1-occ.sum()/mask.sum())};view[occ]=[255,50,40]
  vi=Image.fromarray(view.astype('uint8'));draw=ImageDraw.Draw(vi)
  for k,poly in polys.items():draw.line([tuple(q) for q in poly]+[tuple(poly[0])],fill=(255,220,0) if 'head' in k else (0,220,255),width=2)
  vi=vi.crop((1040,530,1430,810));vi.thumbnail((720,230));board.paste(vi,(5,row*260+20));bd.text((410,row*260+20),phase+' / '+tier+' / OVERCAST',fill='black')
  for j,(k,r) in enumerate(record.items()):bd.text((410,row*260+50+j*28),k+'='+str(round(r['non_occluder_proxy_fraction'],4)),fill='black')
  records[tier+'-'+phase]=record
 board.save(out/(tier+'-opening-head-proxy.jpg'),quality=95)
(out/'metrics.json').write_text(json.dumps({'method':'Fixed projected full arch-shaped opening including frame/mullions vs upper cap above sill+spring. Actual nativePNG green proxy=(G-R>=2 and G-B>=1) OR Y<40 retains dark foliage. Non-occluder fraction is a COLOR PROXY, not exact depth visibility; manual overlay validation required. Cyan=whole, yellow=head, red=green/dark occluder.','polygons':polys,'records':records},indent=2));print(json.dumps(records,indent=2))
