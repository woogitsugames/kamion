"""Artifact-only pinned FIR/short-needle conifer proxy, never a measured spruce scan.

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
src=Path('C:/Users/matma/Documents/Claude/kamion/.claude/worktrees/gpt-s10-coordination/artifacts/s10/refs/fir_tree_01')
pins={'twig_diff.png':'76f6d0c0044d76bac08fbbd3d2ac1c9b66bb046de7d0b1a22aa9b319308f3833',
      'twig_alpha.png':'3f399629337e7ac3af27a01b08ffb9c0d60224a9dd374a1427761a5c2eea9d6e'}
for name,digest in pins.items():assert hashlib.sha256((src/name).read_bytes()).hexdigest()==digest
crop=(295,400,650,805)
diff=np.array(Image.open(src/'twig_diff.png').convert('RGB').crop(crop))
alpha=np.array(Image.open(src/'twig_alpha.png').convert('RGB').getchannel('R').crop(crop))
labels,count=ndimage.label(alpha>32);sizes=np.bincount(labels.ravel());sizes[0]=0
keep=ndimage.binary_dilation(labels==sizes.argmax(),iterations=1)
clean=np.where(keep,alpha,0).astype('uint8')
twig=Image.fromarray(np.dstack([diff,clean]))
twig.save(OUT/'fir-component-filtered.png')
# Single already-branched short-needle spray. Centre the bottom stem on u=.5
# before packing; card root alpha physically meets the trunk/branch origin.
a=np.array(twig);yy,xx=np.where(a[:,:,3]>32);twig=twig.crop((int(xx.min()),int(yy.min()),int(xx.max())+1,int(yy.max())+1))
a=np.array(twig);rows=np.where(a[-3:,:,3]>32)[1];root_x=float(np.median(rows))
half=int(math.ceil(max(root_x,twig.width-root_x)))
centred=Image.new('RGBA',(half*2,twig.height));centred.alpha_composite(twig,(int(round(half-root_x)),0));twig=centred
# No claim of verified Picea species. Official page identifies fir/conifer.
twig.save(OUT/'fir-clean-spray.png')

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
Image.fromarray(new).save(OUT/'fire_station_alpha-fir-proxy.png')
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
for col,(label,mb,atlas) in enumerate((('opaque baseline Low',d['baseline_plants'](1),old),('FIR/SHORT-NEEDLE proxy Low: alpha+root core',plants,new))):
    env['active_atlas']=atlas
    im=env['project'](d['combine'](d['building'],mb),d['camera'])
    sheet.paste(im,(10+480*col,55));dr.text((10+480*col,32),label+f' /{d["tri_count"](mb)}plant tris',fill='black')
dr.text((10,8),'ARTIFACT ONLY: exact source alpha; unlit proxy, NOT a spruce scan or Unity acceptance.',fill='black')
sheet.save(OUT/'fir-alpha-proxy-low.jpg',quality=95)

# Map diagnostic semantic colors to the EXISTING atlas material for a real
# source primitive/batch audit. This is in-memory/artifact only.
actual_plants=MB();tf=g['LAY']['thuja_far'];u=(tf['u'][0]+tf['u'][1])/2;v=(tf['v'][0]+tf['v'][1])/2
for face,uv,mat in zip(plants.F,plants.UV,plants.M):
    actual_plants.face([plants.V[i] for i in face],uv if mat==g['ALPHA'] else [(u,v)]*len(face),mat if mat==g['ALPHA'] else g['MAT'])
old_thuja=g['SPEC']['ground']['thuja'];old_spruce=g['SPEC']['ground']['spruce']
try:
    g['SPEC']['ground']['thuja']=[];g['SPEC']['ground']['spruce']=[]
    body=g['build'](1)
finally:
    g['SPEC']['ground']['thuja']=old_thuja;g['SPEC']['ground']['spruce']=old_spruce
full_low=d['combine'](body,actual_plants);baseline_low=g['build'](1)
assert set(full_low.M)==set(baseline_low.M)=={g['MAT'],g['ALPHA']}
assert np.array_equal(np.min(full_low.V,axis=0),np.min(baseline_low.V,axis=0))
assert np.array_equal(np.max(full_low.V,axis=0),np.max(baseline_low.V,axis=0))
model={'axis_origin':g['AX_O'].tolist(),'axis_u':g['AX_U'].tolist(),'axis_v':g['AX_V'].tolist(),'anchor':g['ANCHOR'].tolist(),
       'lods':[]}
for lod in range(3):
    mb=full_low if lod==1 else g['build'](lod)
    model['lods'].append({'V':[list(map(float,v)) for v in mb.V],'F':mb.F,'UV':mb.UV,'M':mb.M})
(OUT/'fir-proxy-source-model.json').write_text(json.dumps(model))

proof={'status':'ARTIFACT_ONLY_FIR_SHORT_NEEDLE_CONIFER_NOT_VERIFIED_PICEA',
       'source_sha256':pins,'crop':crop,'raw_alpha_components':count,'largest_component_pixels':int(sizes.max()),
       'source_identity':'Poly Haven fir_tree_01 CC0 short-needle conifer; not verified Picea',
       'source_page':'https://polyhaven.com/a/fir_tree_01','license_page':'https://polyhaven.com/license',
       'candidate_atlas_region_uv':rect.tolist(),'pixel_box_xyxy':[x0,y0,x1,y1],'inner_image_uv':inner,
       'old_pixels_outside_region_exactly_preserved':True,
       'old_atlas_sha256':hashlib.sha256(atlas_path.read_bytes()).hexdigest(),
       'changed_base_pixels':int(np.any(new!=old,axis=2).sum()),
       'global_alpha_coverage_old':float((old[:,:,3]>=128).mean()),'global_alpha_coverage_proxy':float((new[:,:,3]>=128).mean()),
       'full_low_tris':{'old':d['tri_count'](baseline_low),'proxy':d['tri_count'](full_low)},
       'full_low_materials':sorted(set(full_low.M)),'full_hero_bounds_exactly_unchanged':True,'baseline_alpha_uv_audit_all_lods':uv_audit,
       'plant_triangles':{'old_low':888,'candidate_low':d['tri_count'](plants)},
       'compound_bough':'single clean short-needle branched spray; component-filtered, bbox-cropped, stem centred on u=.5',
       'batching_source_contract':{'prototype':'landmark_fire_station_jrg2','lod':'same existing .lod1 node',
        'material':'same existing fire_station_alpha slot/submesh; no extra node or primitive material',
        'runtime':'InstanceImporter.ProtoMaterial returns r.Materials[name]; WorldInstances draws same prototype/LOD mesh submesh with existing materialStart, gameObject.layer and shadow policy',
        'limitation':'source contract predicts no added material batch; actual imported submeshes, bounds and route stats remain PENDING'},
       'risks':['Fir/short-needle conifer proxy, not species-verified Picea.',
                'Alpha source texel coverage is not screen coverage; thin needle loss/shimmer and overdraw require actual profile captures/temporal QA.',
                '16px inner padding protects first4plain mips locally; farther global atlas mips may mix neighboring cells. Global alpha-coverage preservation can change old fence/letter mips despite byte-identical old base pixels; requires runtime validation.',
                'Unlit photo RGB cannot establish final Low/High source palette or lighting match.']}
(OUT/'fir-alpha-proxy-proof.json').write_text(json.dumps(proof,indent=2))
print('ALPHA_PROXY_ARTIFACT_ONLY',d['tri_count'](plants),uv_audit)
