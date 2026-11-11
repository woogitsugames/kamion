"""CPU ONLY: current UV, root-centred content UV, and2/3rooted sprays from SAME pinned fir crop.
No production writes, no raw/palette/import-setting changes. Projection uses base alpha, not actual mips.
"""
import ast
import hashlib
import json
import math
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent/'bundle-candidates';OUT.mkdir(exist_ok=True)
src=ROOT/'tools/blender/world/landmarks/make_fire_station.py';spec=ROOT/'Data/Regions/bialystok-industrial-c/generated/landmarks/fire_station_jrg2.spec.json'
pins={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in(src,spec,ROOT/'art-source/world/textures/fire_station_alpha.png',ROOT/'art-source/world/landmarks/fire_station_jrg2/fire_station_jrg2.glb')}
tree=ast.parse(src.read_text());tree.body=[n for n in tree.body if not(isinstance(n,ast.Import) and any(a.name in('bpy','bmesh') for a in n.names) or isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='main')]
sys.argv=[str(src),'--','--spec',str(spec)];g={'__file__':str(src)};exec(compile(tree,str(src),'exec'),g)
layout=json.loads((ROOT/'art-source/world/landmarks/fire_station_jrg2/atlas_layout.json').read_text());cell=layout['alpha']['conifer_bough'];old_uv=cell['inner_uv'];atlas0=np.array(Image.open(ROOT/'art-source/world/textures/fire_station_alpha.png').convert('RGBA'));h,w=atlas0.shape[:2]
x0,x1=int(cell['u'][0]*w),int(cell['u'][1]*w);y0,y1=h-int(cell['v'][1]*h),h-int(cell['v'][0]*h);gap=16
ix0,ix1=round(old_uv[0]*w),round(old_uv[2]*w);iy0,iy1=round((1-old_uv[3])*h),round((1-old_uv[1])*h)
def lin(x):return np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4)
def encode(x):return np.where(x<=.0031308,x*12.92,1.055*np.maximum(x,0)**(1/2.4)-.055)
current=atlas0[iy0:iy1,ix0:ix1];target=lin(current[:,:,:3]/255)[current[:,:,3]>=128].mean(0)
manifest=json.loads((ROOT/'art-source/world/landmarks/fire_station_jrg2/conifer_source.json').read_text());images={}
for item in manifest['files']:
 p=ROOT/manifest['raw_dir']/item['file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'];images[item['map']]=Image.open(p).copy()
crop=tuple(manifest['crop_xyxy']);rgb=np.array(images['diff'].convert('RGB').crop(crop));alpha=np.array(images['alpha'].convert('RGB').getchannel('R').crop(crop));labels,count=ndimage.label(alpha>32);sizes=np.bincount(labels.ravel());sizes[0]=0;keep=ndimage.binary_dilation(labels==sizes.argmax(),iterations=1);alpha=np.where(keep,alpha,0).astype('uint8');base=Image.fromarray(np.dstack([rgb,alpha]))
def root_centre(im):
 a=np.array(im);yy,xx=np.where(a[:,:,3]>32);im=im.crop((int(xx.min()),int(yy.min()),int(xx.max())+1,int(yy.max())+1));a=np.array(im);rx=float(np.median(np.where(a[-3:,:,3]>32)[1]));half=int(math.ceil(max(rx,im.width-rx)));out=Image.new('RGBA',(half*2,im.height));out.alpha_composite(im,(round(half-rx),0));return out
base=root_centre(base)
def pack_bundle(count):
 canvas=Image.new('RGBA',(1200,900));layer=Image.new('RGBA',canvas.size);rx,ry=600,840;layer.alpha_composite(base,(round(rx-base.width/2),ry-base.height))
 for angle in ((-26,26) if count==2 else (-28,0,28)):
  canvas.alpha_composite(layer.rotate(angle,Image.Resampling.BICUBIC,center=(rx,ry)))
 full=np.array(canvas);assert not (full[0,:,3]>32).any() and not(full[-1,:,3]>32).any() and not(full[:,0,3]>32).any() and not(full[:,-1,3]>32).any(),'Clipped bundle'
 twig=root_centre(canvas);twig.save(OUT/f'bundle{count}-unpacked.png');twig.thumbnail((x1-x0-gap*2,y1-y0-gap*2),Image.Resampling.LANCZOS)
 patch=Image.new('RGBA',(x1-x0,y1-y0));patch.alpha_composite(twig,((patch.width-twig.width)//2,patch.height-gap-twig.height));pa=np.array(patch);cov=pa[:,:,3]>=128;linear=lin(pa[:,:,:3]/255);linear*=target/np.maximum(linear[cov].mean(0),1e-6);pa[:,:,:3]=np.clip(np.rint(encode(linear)*255),0,255).astype('uint8');empty=pa[:,:,3]==0;nearest=ndimage.distance_transform_edt(empty,return_distances=False,return_indices=True);pa[:,:,:3][empty]=pa[nearest[0][empty],nearest[1][empty],:3]
 atlas=atlas0.copy();atlas[y0:y1,x0:x1]=pa;outside=np.ones(atlas.shape[:2],bool);outside[y0:y1,x0:x1]=False;assert np.array_equal(atlas[outside],atlas0[outside]);return atlas
def content_uv(atlas):
 pa=atlas[y0:y1,x0:x1];yy,xx=np.where(pa[:,:,3]>=32);bottom=int(yy.max());stem=np.where(pa[max(0,bottom-2):bottom+1,:,3]>=32)[1];root=float(np.median(stem))+.5;half=math.ceil(max(root-xx.min(),xx.max()+1-root)+2)
 left,right=math.floor(root-half),math.ceil(root+half);top=max(0,int(yy.min())-2)
 # Root V is unchanged, with the packed sprite bottom aligned to the original inner edge.
 uv=[(x0+left)/w,old_uv[1],(x0+right)/w,(h-y0-top)/h]
 return uv,{'root_pixel_x':root,'content_rect_local_xyxy':[left,top,right,round((1-old_uv[1])*h)-y0],'alpha32_bbox':[int(xx.min()),int(yy.min()),int(xx.max())+1,bottom+1]}
cases={'current':(atlas0,old_uv,{}),'content_uv':(atlas0,*content_uv(atlas0))}
for number in (2,3):
 a=pack_bundle(number);uv,info=content_uv(a);cases[f'bundle{number}']=(a,uv,info)

text=(OUT.parent/'shape_candidates.py').read_text();a=text.index('def project(');b=text.index('\ndef combine',a);project=text[a:b].replace('for face,mat in zip(mb.F,mb.M):','for face,mat,faceuv in zip(mb.F,mb.M,mb.UV):')
project=project.replace("dst[inside]=dist[inside];rgb[y0:y1+1,x0:x1+1][inside]=COLORS.get(mat,(112,129,113))",'''if mat==g['ALPHA']:
                uv=np.array([faceuv[0],faceuv[j],faceuv[j+1]])
                uu=(a*uv[0,0]/zz[0]+b*uv[1,0]/zz[1]+c*uv[2,0]/zz[2])*dist
                vv=(a*uv[0,1]/zz[0]+b*uv[1,1]/zz[1]+c*uv[2,1]/zz[2])*dist
                tx=np.clip((uu*atlas.shape[1]).astype(int),0,atlas.shape[1]-1);ty=np.clip(((1-vv)*atlas.shape[0]).astype(int),0,atlas.shape[0]-1)
                rgba=atlas[ty,tx];inside &= rgba[:,:,3]>=128
            dst[inside]=dist[inside];rgb[y0:y1+1,x0:x1+1][inside]=COLORS.get(mat,(112,129,113))''')
env={'np':np,'math':math,'Image':Image,'g':g,'COLORS':{'fire_station':(47,79,43),'fire_station_alpha':(47,79,43)}};exec(compile(project,'artifact_alpha_projection','exec'),env)
camera=next(c for c in json.loads((ROOT/'Data/Regions/bialystok-industrial-c/generated/control_cameras.json').read_text())['cameras'] if c['id']=='fire_station_ref7197');sheet=Image.new('RGB',(960,700),'white');dr=ImageDraw.Draw(sheet);metrics={};texture_sheet=Image.new('RGB',(960,840),'white');td=ImageDraw.Draw(texture_sheet)
for index,(name,(atlas,uv,info)) in enumerate(cases.items()):
 g['ALAY']['conifer_bough']['inner_uv']=uv;mb=g['MB']()
 for e,n,z,height,radius,key in g['SPEC']['ground']['spruce']:g['build_conifer'](mb,g['en_to_uvz']([e,n,z]),height,radius,key,1)
 env['atlas']=atlas;im=env['project'](mb,camera,size=(2340,1080)).crop((1300,420,1660,830));im.thumbnail((450,280));xx=index%2*480;yy=index//2*330;sheet.paste(im,(xx,yy+35));dr.text((xx+8,yy+8),name+' / CORE.55R /unlit basealpha, NOT actualmips',fill='black')
 ax0,ax1=round(uv[0]*w),round(uv[2]*w);ay0,ay1=round((1-uv[3])*h),round((1-uv[1])*h);tile=atlas[ay0:ay1,ax0:ax1];covered=tile[:,:,3]>=128;rgb_mean=lin(tile[:,:,:3]/255)[covered].mean(0)
 metrics[name]={'uv':uv,'geometry_conifer_triangles':sum(len(f)-2 for f in mb.F),'info':info,'mapped_size':[tile.shape[1],tile.shape[0]],'mapped_coverage128':float(covered.mean()),'mapped_mean_linear_rgb':rgb_mean.tolist(),'target_existing_mean_linear_rgb':target.tolist(),'old_alpha_regions_base_pixel_exact':True}
 bg=Image.new('RGBA',(tile.shape[1],tile.shape[0]),(200,200,200,255));bg.alpha_composite(Image.fromarray(tile));bg=bg.convert('RGB');bg.thumbnail((460,360));texture_sheet.paste(bg,(xx+5,index//2*420+40));td.text((xx+8,index//2*420+10),name+' coverage '+str(round(covered.mean()*100,2))+'%',fill='black');Image.fromarray(atlas).save(OUT/(name+'-atlas.png'))
sheet.save(OUT/'Low-matched-silhouettes.jpg',quality=95);texture_sheet.save(OUT/'packed-sprays.jpg',quality=95)
for rel,sha in pins.items():assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==sha
(OUT/'proof.json').write_text(json.dumps({'status':'ARTIFACT_ONLY_NOT_RUNTIME_ACCEPTANCE','source_sha256':pins,'source_raw_unchanged':True,'palette_parameters_unchanged':True,'no_tris_or_material_changes':True,'definitions':'Vradialroot-tip;Umostlyvertical. Root-centredcontentUV+2pxfilterpadding,16pxpackedoutergutter. Bundles2±26deg,3-28/0/+28deg fromsamecrop, no clipping.','cases':metrics},indent=2));print(json.dumps(metrics,indent=2))
