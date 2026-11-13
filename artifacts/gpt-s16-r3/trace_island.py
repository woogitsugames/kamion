"""Read-only geometric sun-ray diagnostic of the SMALL NORTH NOSE, NOT the main circle island. Excludes hero instances. Does not simulate shadow maps or bias."""
import sys,json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from shapely.geometry import Point,Polygon
from shapely.ops import unary_union
root=Path(__file__).resolve().parents[2];out=Path(__file__).resolve().parent
sys.path.insert(0,str(out.parent/'gpt-s16-r1'))
from audit_glb import load
parts=[];island=[];hashes={}
for fn in ['chunk_6_6.glb','chunk_5_6.glb']:
 f=root/'Data/raw/derived/bialystok-industrial-c/world'/fn
 hashes[str(f.relative_to(root))]=hashlib.sha256(f.read_bytes()).hexdigest()
 nodes=load(f)
 for p in nodes.get('road',[]):
  if p['material']=='island_gravel':
   v=p['POSITION'].copy();v[:,0]*=-1
   island.extend(v[p['indices'].reshape(-1,3)])
 for p in nodes.get('bridge',[]):
  v=p['POSITION'].copy();v[:,0]*=-1
  normals=p['NORMAL'].copy();normals[:,0]*=-1
  inds=p['indices'].reshape(-1,3);t=v[inds]
  keep=(t[:,:,0].max(1)>510)&(t[:,:,0].min(1)<580)&(t[:,:,2].max(1)>-750)&(t[:,:,2].min(1)<-670)
  parts.append((t[keep],normals[inds][keep].mean(1)))
island=np.array(island);shape=unary_union([Polygon(t[:,[0,2]]) for t in island if np.ptp(t[:,1])<.5])
t=np.concatenate([a for a,b in parts]);norm=np.concatenate([b for a,b in parts]);a=t[:,0];e1=t[:,1]-a;e2=t[:,2]-a
el=np.deg2rad(42);az=np.deg2rad(200)
d=np.array([np.cos(el)*np.sin(az),np.sin(el),np.cos(el)*np.cos(az)])
h=np.cross(d,e2);det=np.einsum('ij,ij->i',e1,h);inv=np.divide(1,det,out=np.zeros_like(det),where=np.abs(det)>1e-8)
mn=np.floor(island[:,:,[0,2]].min((0,1)));mx=np.ceil(island[:,:,[0,2]].max((0,1)))
xs=np.arange(mn[0],mx[0],.25);zs=np.arange(mn[1],mx[1],.25)
im=Image.new('RGB',(len(xs),len(zs)),(190,190,190));rows=[]
for ix,E in enumerate(xs):
 for iz,N in enumerate(zs):
  if not shape.covers(Point(E,N)):continue
  # Interpolate actual gravel triangle height at E/N rather than assuming a flat receiver.
  U=None
  for tri in island:
   a2,b2,c2=tri[:,[0,2]];mat=np.column_stack((b2-a2,c2-a2))
   if abs(np.linalg.det(mat))<1e-9:continue
   uv=np.linalg.solve(mat,np.array([E,N])-a2)
   if uv.min()>=-1e-5 and uv.sum()<=1.00001:U=tri[0,1]+uv[0]*(tri[1,1]-tri[0,1])+uv[1]*(tri[2,1]-tri[0,1]);break
  if U is None:continue
  o=np.array([E,U+.05,N]);s=o-a;u=np.einsum('ij,ij->i',s,h)*inv;q=np.cross(s,e1);v=q@d*inv;dist=np.einsum('ij,ij->i',e2,q)*inv
  hit=(abs(det)>1e-8)&(u>=0)&(v>=0)&(u+v<=1)&(dist>0)&(dist<30)
  front=hit&((norm@d)>0)
  kind='blocked' if front.any() else 'backface-only' if hit.any() else 'open'
  im.putpixel((ix,len(zs)-1-iz),{'blocked':(35,35,35),'backface-only':(230,180,25),'open':(240,90,60)}[kind])
  rows.append({'E':float(E),'N':float(N),'U':float(U),'kind':kind})
counts={k:sum(r['kind']==k for r in rows) for k in ['blocked','backface-only','open']}
report={'method':'LIMITED: small north nose only, hero instances excluded. Exact triangle intersections of two local bridge chunks, actual gravel receivers +0.05m; no raster shadow map/bias simulation. Light-facing stored normals used as diagnostic.', 'sun_elevation_deg':42,'sun_azimuth_deg':200,'sample_step_m':.25,'glb_sha256':hashes,'counts':counts,'samples':rows}
(out/'island-rays.json').write_text(json.dumps(report,indent=2)+'\n')
canvas=Image.new('RGB',(640,640),'white');im.thumbnail((580,560));scale=min(580/im.width,560/im.height);im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST);canvas.paste(im,((640-im.width)//2,60));dr=ImageDraw.Draw(canvas);dr.text((12,8),'Putry: north up, 0.25m gravel grid; clear 42 / 200',fill='black');dr.text((12,26),'dark=blocked / red=open / yellow=backface only',fill='black');dr.text((12,44),str(counts),fill='black');canvas.save(out/'island-rays.jpg',quality=90)
print(counts)
