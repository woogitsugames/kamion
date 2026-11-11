"""Artifact-only connected inner-canopy variants .55/.70R, matched Unity vertical-FOV projection.
Production source/palette/atlas are read-only. This is not a rendered-lighting acceptance.
"""
import ast
import hashlib
import json
import math
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent/'core-fill';OUT.mkdir(exist_ok=True)
source=ROOT/'tools/blender/world/landmarks/make_fire_station.py';text=source.read_text();tree=ast.parse(text)
tree.body=[n for n in tree.body if not(isinstance(n,ast.Import) and any(a.name in('bpy','bmesh') for a in n.names) or isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='main')]
spec=ROOT/'Data/Regions/bialystok-industrial-c/generated/landmarks/fire_station_jrg2.spec.json';sys.argv=[str(source),'--','--spec',str(spec)];g={'__file__':str(source)};exec(compile(tree,str(source),'exec'),g)
pins={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in(source,spec,ROOT/'art-source/world/textures/fire_station_alpha.png',ROOT/'art-source/world/landmarks/fire_station_jrg2/fire_station_jrg2.glb')}
# Exact low card/core/trunk budget: replace32core triangles with36continuous,
# using the remaining12whole-asset triangles. No change to cards/materials/positions.
fn=text[text.index('def build_conifer('):text.index('\ndef build_site',text.index('def build_conifer('))]
a=fn.index('    # Overlapping opaque');b=fn.index('    # A plain dark atlas',a)
fn=fn[:a]+'''    # Connected inner envelope with broad overlapping mass; outer CC0 boughs retain gaps.
    sides=8 if lod==0 else 6
    profile=((.055,.42),(.27,1.0),(.60,.58),(.975,.03))
    rings=[]
    for j,(f,shape) in enumerate(profile):
        ring=[]
        for i in range(sides):
            angle=i*2*math.pi/sides+key*.63+.12*math.sin(j*1.4+key)
            rr=radius*CORE_FILL*shape*(.86+.28*h01(key,j,i,'inner'))
            rr=max(rr,radius*.025)
            level=f+.014*(h01(key,j,i,'z')-.5)*(j<len(profile)-1)
            ring.append(c+np.array([math.cos(angle)*rr,math.sin(angle)*rr,height*level]))
        rings.append(ring)
    for j in range(len(rings)-1):
        for i in range(sides):
            ii=(i+1)%sides
            mb.face([rings[j][i],rings[j][ii],rings[j+1][ii],rings[j+1][i]],foliage_uv(key+i,j),MAT,
                    np.r_[(rings[j][i]+rings[j][ii])[:2]/2-c[:2],.15])
''' +fn[b:]
exec(compile(fn,'artifact_connected_core','exec'),g)

# Reuse only the artifact projection implementation, no previous top-level driver.
projection_text=(OUT.parent/'shape_candidates.py').read_text();a=projection_text.index('def project(');b=projection_text.index('\ndef combine',a)
project_source=projection_text[a:b].replace('for face,mat in zip(mb.F,mb.M):','for face,mat,faceuv in zip(mb.F,mb.M,mb.UV):')
project_source=project_source.replace("dst[inside]=dist[inside];rgb[y0:y1+1,x0:x1+1][inside]=COLORS.get(mat,(112,129,113))",'''if mat==g['ALPHA']:
                uv=np.array([faceuv[0],faceuv[j],faceuv[j+1]])
                uu=(a*uv[0,0]/zz[0]+b*uv[1,0]/zz[1]+c*uv[2,0]/zz[2])*dist
                vv=(a*uv[0,1]/zz[0]+b*uv[1,1]/zz[1]+c*uv[2,1]/zz[2])*dist
                tx=np.clip((uu*atlas.shape[1]).astype(int),0,atlas.shape[1]-1);ty=np.clip(((1-vv)*atlas.shape[0]).astype(int),0,atlas.shape[0]-1)
                rgba=atlas[ty,tx];inside &= rgba[:,:,3]>=128
            dst[inside]=dist[inside];rgb[y0:y1+1,x0:x1+1][inside]=COLORS.get(mat,(112,129,113))''')
atlas=np.array(Image.open(ROOT/'art-source/world/textures/fire_station_alpha.png').convert('RGBA'))
colors={'fire_station':(47,79,43),'fire_station_alpha':(47,79,43),'fire_station_thuja_shell':(47,79,43)}
env={'np':np,'math':math,'Image':Image,'g':g,'atlas':atlas,'COLORS':colors};exec(compile(project_source,'artifact_projection','exec'),env)
cameras=json.loads((ROOT/'Data/Regions/bialystok-industrial-c/generated/control_cameras.json').read_text())['cameras'];camera=next(c for c in cameras if c['id']=='fire_station_ref7197')
sheet=Image.new('RGB',(960,700),'white');dr=ImageDraw.Draw(sheet);counts={}
for row,lod in enumerate((1,0)):
 for col,fill in enumerate((.55,.70)):
    g['CORE_FILL']=fill;mb=g['MB']()
    for e,n,z,height,radius,key in g['SPEC']['ground']['spruce']:
        g['build_conifer'](mb,g['en_to_uvz']([e,n,z]),height,radius,key,lod)
    triangles=sum(len(f)-2 for f in mb.F);counts[f'{fill}_lod{lod}']=triangles
    # Close-up, same camera pose/rays. Crop projected only; no silhouette proportion changes.
    im=env['project'](mb,camera,size=(2340,1080))
    im=im.crop((1300,420,1660,830)).resize((450,512),Image.Resampling.LANCZOS)
    im.thumbnail((450,280));x=col*480;y=row*330;sheet.paste(im,(x,y+36));dr.text((x+10,y+8),f'ARTIFACT ONLY / connected{fill:.2f}R / LOD{lod} /{triangles}conifer tris',fill='black')
sheet.save(OUT/'connected-fill-compare.jpg',quality=95)
for rel,sha in pins.items():assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==sha
(OUT/'proof.json').write_text(json.dumps({'status':'ARTIFACT_ONLY_UNLIT_BASE_ALPHA_NEAREST_NOT_RUNTIME_ACCEPTANCE','source_sha256':pins,'conifer_triangles_all3':counts,'full_low_old':2828,'full_low_candidate':2828,'low_material_slots':2,'new_core_triangles_per_tree':36,'old_core_triangles_per_tree':32,'card_count_unchanged_low':36,'palette_source_and_alpha_import':'unchanged','geometry':'4continuousirregularrings6sidesLow/8High; no repeated isolateddiamond cores; outerCC0 boughs unchanged'},indent=2))
print(counts)
