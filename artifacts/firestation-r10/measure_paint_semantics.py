"""Material/UV/geometry masks from the exact locked baseline GLB; conservative alpha occlusion.
No window, clinker, foliage, trim or letter pixels are classified as clean plaster.
"""
import hashlib
import json
import math
import struct
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
path=OUT/'baseline-hero.glb';raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()=='98e6b4aedbaca830078f831d1696af05bc81318c34f4eba353976310d1ad406d'
n=struct.unpack_from('<I',raw,12)[0];meta=json.loads(raw[20:20+n]);blob=raw[28+n:]
def access(i):
 a=meta['accessors'][i];v=meta['bufferViews'][a['bufferView']];dt=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']]);nc={'SCALAR':1,'VEC2':2,'VEC3':3}[a['type']]
 return np.ndarray((a['count'],nc),dtype=dt,buffer=blob,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',nc*dt.itemsize),dt.itemsize)).copy()
spec=json.loads((ROOT/'Data/Regions/bialystok-industrial-c/generated/landmarks/fire_station_jrg2.spec.json').read_text());axis=spec['dims']['axis'];origin=np.array(axis['origin_en']);u=np.array(axis['u']);u/=np.linalg.norm(u);v=np.array([-u[1],u[0]]);anchor=np.array(spec['anchor'])
cameras=json.loads((ROOT/'Data/Regions/bialystok-industrial-c/generated/control_cameras.json').read_text())['cameras'];cam=next(c for c in cameras if c['id']=='fire_station_ref7197');eye=np.array(cam['pos']);fw=np.array(cam['look_at'])-eye;fw/=np.linalg.norm(fw);right=np.cross(fw,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,fw)
w,h=2340,1080;focal=h/(2*math.tan(math.radians(cam['fov_deg'])/2));records={};names={1:'gable',2:'wing',3:'tower'}
for tier,lod in [('Low',1),('High',0)]:
 node=next(n for n in meta['nodes'] if n.get('name')=='landmark_fire_station_jrg2'+('' if not lod else '.lod1'))
 depth=np.full((h,w),np.inf);label=np.zeros((h,w),np.uint8);height=np.zeros((h,w),np.float32)
 for prim in meta['meshes'][node['mesh']]['primitives']:
  mat=meta['materials'][prim['material']]['name'];pos=access(prim['attributes']['POSITION']);uv=access(prim['attributes']['TEXCOORD_0']);uv[:,1]=1-uv[:,1]
  en=anchor[:2]+np.c_[-pos[:,0],pos[:,2]];p3=np.c_[(en-origin)@u,(en-origin)@v,pos[:,1]];world=np.c_[en,pos[:,1]+anchor[2]];delta=world-eye;zz=delta@fw
  xy=np.c_[w/2+focal*(delta@right)/zz,h/2-focal*(delta@up)/zz]
  for indices in access(prim['indices']).reshape(-1,3):
   p=xy[indices];z=zz[indices];local=p3[indices];uvv=uv[indices,1];kind=0
   if mat=='fire_station' and np.ptp(local[:,1])<.015:
    vm=float(local[:,1].mean());umin,umax=local[:,0].min(),local[:,0].max()
    if abs(vm)<.015 and umin>36.35 and umax<48.45:kind=1
    elif min(abs(vm-.2),abs(vm-1.75))<.015 and umin>18.45 and umax<36.45:kind=2
    elif abs(vm-6)<.015 and umin>18.45 and umax<31.45:kind=3
   x0=max(0,int(np.floor(p[:,0].min())));x1=min(w-1,int(np.ceil(p[:,0].max())));y0=max(0,int(np.floor(p[:,1].min())));y1=min(h-1,int(np.ceil(p[:,1].max())))
   if x1<x0 or y1<y0 or min(z)<=0:continue
   den=(p[1,1]-p[2,1])*(p[0,0]-p[2,0])+(p[2,0]-p[1,0])*(p[0,1]-p[2,1])
   if abs(den)<1e-9:continue
   xx,yy=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
   a=((p[1,1]-p[2,1])*(xx-p[2,0])+(p[2,0]-p[1,0])*(yy-p[2,1]))/den;b=((p[2,1]-p[0,1])*(xx-p[2,0])+(p[0,0]-p[2,0])*(yy-p[2,1]))/den;c=1-a-b;dist=1/(a/z[0]+b/z[1]+c/z[2]);dst=depth[y0:y1+1,x0:x1+1];inside=(a>=0)&(b>=0)&(c>=0)&(dist<dst)
   vv=(a*uvv[0]/z[0]+b*uvv[1]/z[1]+c*uvv[2]/z[2])*dist;hz=(a*local[0,2]/z[0]+b*local[1,2]/z[1]+c*local[2,2]/z[2])*dist
   clean=(vv>=1.2)&(vv<=2.6)&(hz>=2)
   dst[inside]=dist[inside];label[y0:y1+1,x0:x1+1][inside]=np.where(clean,kind,0)[inside];height[y0:y1+1,x0:x1+1][inside]=hz[inside]
 np.savez_compressed(OUT/f'before-roi/{tier}-paint-material-masks.npz',label=label,height=height)
 for lighting in ('clear','overcast'):
  im=Image.open(OUT/f'before/{tier}-{lighting}/fire-station-ref7197.png').convert('RGB');rgb=np.array(im);overlay=rgb.copy();row={}
  for k,name in names.items():
   masks={'all_clean_above2m':label==k,'matched_z2to5':(label==k)&(height>=2)&(height<5),'matched_z5to8':(label==k)&(height>=5)&(height<8)}
   row[name]={}
   for band,keep in masks.items():
    data=rgb[keep]
    if not len(data):continue
    row[name][band]={'pixels':len(data),'median_rgb_srgb':np.median(data,axis=0).tolist(),'mean_rgb_srgb':data.mean(0).tolist(),'median_luma_srgb':float(np.median(data@np.array([.2126,.7152,.0722])))}
   color={1:[255,0,0],2:[0,255,0],3:[255,0,255]}[k];keep=label==k;overlay[keep]=(.5*overlay[keep]+.5*np.array(color)).astype('uint8')
  view=Image.fromarray(overlay);view.thumbnail((960,960));sheet=Image.new('RGB',(960,650),'white');sheet.paste(view,(0,0));dr=ImageDraw.Draw(sheet);dr.text((8,450),tier+' '+lighting+' / material+UV clean-plaster masks; alpha objects conservatively opaque',fill='black')
  for i,(name,bands) in enumerate(row.items()):dr.text((8,475+i*45),name+': '+str(bands),fill='black')
  sheet.save(OUT/f'before-roi/{tier}-{lighting}-paint-material.jpg',quality=95);records[tier+'-'+lighting]=row
(OUT/'before-roi/paint-material-measurements.json').write_text(json.dumps({'method':'exact baselineGLB SHA, material=fire_station, front plane, atlasUVv1.2..2.6, z>=2m; alpha primitives conservatively opaque; runtime verticalFOV. Needs overlay validation.','results':records},indent=2))
print(json.dumps(records,indent=2))
