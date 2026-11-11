"""Artifact-only pinned PINE/generic-conifer proxy, never a measured spruce scan.

No production writes or B code import. Run with uv worldgen python.
"""
import hashlib
import json
import math
import runpy
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE=Path(__file__).resolve().parent
d=runpy.run_path(str(HERE/'shape_candidates.py'))
ROOT,OUT,g,MB=d['ROOT'],d['OUT'],d['g'],d['MB']
src=Path('C:/Users/matma/Documents/Claude/kamion/.claude/worktrees/gpt-s10-coordination/artifacts/s10/refs/pine_tree_01')
pins={'twig_diff.png':'d02c031de64b8ad671f3dd0da19870fa4783d912ae6674aeab0702871deeaeaa',
      'twig_alpha.png':'6f91aa99f2c27108d6f817f874954aa7df8bfbb4dea2673e9322555a6ae79d99'}
for name,digest in pins.items():assert hashlib.sha256((src/name).read_bytes()).hexdigest()==digest
crop=(5,26,220,450)
diff=np.array(Image.open(src/'twig_diff.png').convert('RGB').crop(crop))
alpha=np.array(Image.open(src/'twig_alpha.png').convert('RGB').getchannel('R').crop(crop))
labels,count=ndimage.label(alpha>32);sizes=np.bincount(labels.ravel());sizes[0]=0
keep=ndimage.binary_dilation(labels==sizes.argmax(),iterations=1)
clean=np.where(keep,alpha,0).astype('uint8')
twig=Image.fromarray(np.dstack([diff,clean]))
twig.save(OUT/'cc0-twig-component-filtered.png')
samples={}
for x,y in ((10,400),(20,360),(190,440)):
    samples[f'{x},{y}']={'raw_alpha':int(alpha[y-crop[1],x-crop[0]]),'filtered_alpha':int(clean[y-crop[1],x-crop[0]])}

# Independent audit of the exact B crop and actual processed B output. No B writes.
B=ROOT.parent/'gpt-vegetation-r2'
processed_path=B/'art-source/world/vegetation/leaves_pine.png'
actual=Image.open(processed_path).convert('RGBA')
audit=Image.new('RGB',(960,520),(236,236,236));dr=ImageDraw.Draw(audit)
for i,(name,im) in enumerate((('RAW diffuse; exact B crop',Image.fromarray(diff)),('RAW paired alpha',Image.fromarray(alpha).convert('RGB')),('B-style component alpha',Image.fromarray(clean).convert('RGB')))):
    audit.paste(im,(8+i*240,35));dr.text((8+i*240,8),name,fill='black')
    dr.rectangle((8+i*240,35+270,8+i*240+60,35+423),outline='red',width=2)
bg=Image.new('RGBA',actual.size,(225,225,225,255));bg.alpha_composite(actual)
audit.paste(bg.convert('RGB').resize((230,230)),(725,35));dr.text((725,8),'ACTUAL B processed card',fill='black')
dr.text((725,280),'Raw triangles: alpha253-255',fill='black')
dr.text((725,298),'B filter removes them.',fill='black')
dr.text((725,316),'NOT a B regression.',fill='black')
dr.text((8,480),'Red box: example bottom UV padding. Sample source pixels: (10,400),(20,360),(190,440).',fill='black')
audit.save(OUT/'B-crop-alpha-audit.jpg',quality=95)

# Reproducible root-connected compound bough: five rotations of the CLEAN twig.
# Root placement follows its measured crop stem x~.61; no B processor/code import.
fan=Image.new('RGBA',(512,512));stem=twig.copy();stem.thumbnail((205,405),Image.Resampling.LANCZOS)
base=Image.new('RGBA',fan.size);base.alpha_composite(stem,(round(256-.61*stem.width),round(480-stem.height)))
for angle in (-50,-25,0,25,50):
    fan.alpha_composite(base.rotate(angle,Image.Resampling.BICUBIC,center=(256,480)))
afan=np.array(fan);ys,xs=np.where(afan[:,:,3]>32)
fan=fan.crop((int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1))
fan.save(OUT/'cc0-compound-pine-proxy.png')
twig=fan

# Region is disjoint from every baseline alpha UV bounding box, including all3LODs.
rect=np.array([.30,.025,.43,.24]) # u0,v0,u1,v1. Retains >30px gap from lettering/number.
uv_audit={}
for lod in range(3):
    base=g['build'](lod);boxes=[]
    for mat,uv in zip(base.M,base.UV):
        if mat!=g['ALPHA']:continue
        a=np.array(uv);lo=a.min(0);hi=a.max(0)
        assert np.all(lo>=-1e-9) and np.all(hi<=1+1e-9),'Wrapped UV needs separate audit'
        overlap=min(hi[0],rect[2])>max(lo[0],rect[0]) and min(hi[1],rect[3])>max(lo[1],rect[1])
        assert not overlap,(lod,lo,hi)
        boxes.append([*lo,*hi])
    uv_audit[str(lod)]={'alpha_faces':len(boxes),'candidate_region_overlap_count':0}

atlas_path=ROOT/'art-source/world/textures/fire_station_alpha.png'
old=np.array(Image.open(atlas_path).convert('RGBA'));new=old.copy();hh,ww=old.shape[:2]
x0,y0,x1,y1=int(rect[0]*ww),int((1-rect[3])*hh),int(rect[2]*ww),int((1-rect[1])*hh)
patch=Image.new('RGBA',(x1-x0,y1-y0));pad=16
twig.thumbnail((patch.width-2*pad,patch.height-2*pad),Image.Resampling.LANCZOS)
px=(patch.width-twig.width)//2;py=(patch.height-twig.height)//2;patch.alpha_composite(twig,(px,py))
# Dilation inside the new cell only. Old neighboring RGB/A pixels are never changed.
pa=np.array(patch);empty=pa[:,:,3]==0;nearest=ndimage.distance_transform_edt(empty,return_distances=False,return_indices=True)
pa[:,:,:3][empty]=pa[nearest[0][empty],nearest[1][empty],:3]
new[y0:y1,x0:x1]=pa
outside=np.ones(old.shape[:2],dtype=bool);outside[y0:y1,x0:x1]=False
assert np.array_equal(new[outside],old[outside])
Image.fromarray(new).save(OUT/'fire_station_alpha-proxy.png')
inner=[(x0+px)/ww,1-(y0+py+twig.height)/hh,(x0+px+twig.width)/ww,1-(y0+py)/hh]

def alpha_spruce(mb,c,height,radius,key):
    #24 root-connected radial twig cards, no new runtime material name or node.
    # Existing alpha material is CullOff; no duplicate reverse-face geometry.
    uu0,vv0,uu1,vv1=inner
    for j,f in enumerate((.10,.25,.40,.55,.70,.85)):
        for i in range(4):
            a=key*.63+j*1.69+i*math.pi/2
            direction=np.array([math.cos(a),math.sin(a)])
            root=c+np.array([0,0,height*f])
            length=radius*(1-f)**.7*(.9+.3*d['h'](key,j,i))
            tip=c+np.r_[direction*length,height*(f-.04)]
            side=np.array([0,0,1.0])*min(length*.65,height*f*.90)
            mb.face([root-side,root+side,tip+side,tip-side],
                    [(uu0,vv0),(uu1,vv0),(uu1,vv1),(uu0,vv1)],g['ALPHA'])
    # Four overlapping opaque branch-core volumes, rooted around the trunk.
    # Outer needle silhouette is still carried by the clipped twig sprites.
    for f in (.12,.36,.61,.85):
        cc=c+np.array([0,0,height*f]);rr=radius*.58*(1-f)**.72
        half_h=min(height*.13,height*f*.95)
        for j in range(4):
            a=j*math.pi/2;b=(j+1)*math.pi/2
            p=cc+np.array([math.cos(a)*rr,math.sin(a)*rr,0])
            q=cc+np.array([math.cos(b)*rr,math.sin(b)*rr,0])
            mb.face([cc+[0,0,half_h],p,q],[(0,0)]*3,'spruce')
            mb.face([cc-[0,0,half_h],p,q],[(0,0)]*3,'spruce')
    d['tetra'](mb,[c+[-.045,-.045,0],c+[.045,-.045,0],c+[0,.045,0],c+[0,0,height]],'trunk')

plants=MB()
for e,n,z,height,r,key in g['SPEC']['ground']['thuja']:
    # All forms retain4rings and4sides (24tri) rather than sacrificing column/egg tips.
    habit=key%3;profile=d['PROFILES'][habit];profile=[profile[0],profile[2],profile[3],profile[-1]]
    if habit==1:profile=[profile[0],profile[1],profile[-1]]
    rings=[];c=g['en_to_uvz']([e,n,z])
    for j,(f,rr) in enumerate(profile):
        rings.append([c+np.array([math.cos(i*math.pi/2+key)*r*rr,math.sin(i*math.pi/2+key)*r*rr,height*f]) for i in range(4)])
    for j in range(len(rings)-1):
        for i in range(4):
            ii=(i+1)%4;plants.face([rings[j][i],rings[j][ii],rings[j+1][ii],rings[j+1][i]],[(0,0)]*4,'thuja')
for e,n,z,height,r,key in g['SPEC']['ground']['spruce']:
    c=g['en_to_uvz']([e,n,z]);c[0]+=4 if key<2 else 0
    alpha_spruce(plants,c,height,r,key)
assert d['tri_count'](plants)<=888

# Use the same CPU depth projection, now evaluating exact paired texture alpha at0.5.
text=(HERE/'shape_candidates.py').read_text();start=text.index('def project(');end=text.index('\ndef combine',start)
project_src=text[start:end].replace('for face,mat in zip(mb.F,mb.M):','for face,mat,faceuv in zip(mb.F,mb.M,mb.UV):')
project_src=project_src.replace("dst[inside]=dist[inside];rgb[y0:y1+1,x0:x1+1][inside]=COLORS.get(mat,(112,129,113))",'''if mat == g['ALPHA']:
                uv=np.array([faceuv[0],faceuv[j],faceuv[j+1]])
                u=(a*uv[0,0]/zz[0]+b*uv[1,0]/zz[1]+c*uv[2,0]/zz[2])*dist
                v=(a*uv[0,1]/zz[0]+b*uv[1,1]/zz[1]+c*uv[2,1]/zz[2])*dist
                tx=np.clip((u*ww).astype(int),0,ww-1);ty=np.clip(((1-v)*hh).astype(int),0,hh-1)
                sampled=active_atlas[ty,tx];inside &= sampled[:,:,3]>=128
                dst[inside]=dist[inside];rgb[y0:y1+1,x0:x1+1][inside]=sampled[:,:,:3][inside]
            else:
                dst[inside]=dist[inside];rgb[y0:y1+1,x0:x1+1][inside]=COLORS.get(mat,(112,129,113))''')
env=dict(d);env.update(active_atlas=new,ww=ww,hh=hh)
exec(compile(project_src,'artifact_alpha_projection','exec'),env)
sheet=Image.new('RGB',(960,370),'white');dr=ImageDraw.Draw(sheet)
for col,(label,mb,atlas) in enumerate((('opaque baseline Low',d['baseline_plants'](1),old),('PINE/GENERIC proxy Low: alpha+root core',plants,new))):
    env['active_atlas']=atlas
    im=env['project'](d['combine'](d['building'],mb),d['camera'])
    sheet.paste(im,(10+480*col,55));dr.text((10+480*col,32),label+f' /{d["tri_count"](mb)}plant tris',fill='black')
dr.text((10,8),'ARTIFACT ONLY: exact source alpha; unlit proxy, NOT a spruce scan or Unity acceptance.',fill='black')
sheet.save(OUT/'alpha-proxy-low.jpg',quality=95)

proof={'status':'ARTIFACT_ONLY_PINE_GENERIC_CONIFER_PROXY_NOT_SPRUCE_SCAN',
       'source_sha256':pins,'crop':crop,'raw_alpha_components':count,'largest_component_pixels':int(sizes.max()),
       'padding_pixel_audit':samples,'B_actual_processed_sha256':hashlib.sha256(processed_path.read_bytes()).hexdigest(),
       'B_finding':'separate padding components are removed; no B regression',
       'candidate_atlas_region_uv':rect.tolist(),'pixel_box_xyxy':[x0,y0,x1,y1],'inner_image_uv':inner,
       'old_pixels_outside_region_exactly_preserved':True,'baseline_alpha_uv_audit_all_lods':uv_audit,
       'plant_triangles':{'old_low':888,'candidate_low':d['tri_count'](plants)},
       'compound_bough':'five clean twig rotations -50,-25,0,25,50deg about a common stem root; root connected and bbox-cropped',
       'batching_source_contract':{'prototype':'landmark_fire_station_jrg2','lod':'same existing .lod1 node',
        'material':'same existing fire_station_alpha slot/submesh; no extra node or primitive material',
        'runtime':'InstanceImporter.ProtoMaterial returns r.Materials[name]; WorldInstances draws same prototype/LOD mesh submesh with existing materialStart, gameObject.layer and shadow policy',
        'limitation':'source contract predicts no added material batch; actual imported submeshes, bounds and route stats remain PENDING'},
       'risks':['Pine/generic conifer proxy, not species-verified spruce.',
                'Alpha source texel coverage is not screen coverage; thin needle loss/shimmer and overdraw require actual profile captures/temporal QA.',
                '16px inner padding protects first4mips locally; farther global atlas mips may mix neighboring cells.',
                'Unlit photo RGB cannot establish final Low/High source palette or lighting match.']}
(OUT/'alpha-proxy-proof.json').write_text(json.dumps(proof,indent=2))
print('ALPHA_PROXY_ARTIFACT_ONLY',d['tri_count'](plants),uv_audit)
