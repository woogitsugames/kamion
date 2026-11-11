"""Artifact-only CPU source-mesh projection, no Blender/Unity and no production writes.

uv run --project tools/worldgen python artifacts/firestation-r10/shape_candidates.py
"""
import ast
import copy
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / 'shape-candidates'
OUT.mkdir(exist_ok=True)
SOURCE = ROOT/'tools/blender/world/landmarks/make_fire_station.py'
SPEC = ROOT/'Data/Regions/bialystok-industrial-c/generated/landmarks/fire_station_jrg2.spec.json'
# Execute definitions only. Explicitly prohibit the writer main() and Blender imports.
tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
tree.body = [n for n in tree.body if not (
    isinstance(n, ast.Import) and any(a.name in ('bpy', 'bmesh') for a in n.names)
    or isinstance(n, ast.Expr) and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Name) and n.value.func.id == 'main')]
sys.argv = [str(SOURCE), '--', '--spec', str(SPEC)]
g = {'__file__': str(SOURCE), '__name__': 'artifact_definition_reader'}
exec(compile(tree, str(SOURCE), 'exec'), g)
MB, P3, h = g['MB'], g['P3'], g['h01']
snapshot = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (
    SOURCE, SPEC, ROOT/'art-source/world/landmarks/fire_station_jrg2/dims.json',
    ROOT/'art-source/world/landmarks/fire_station_jrg2/fire_station_jrg2.glb')}

PROFILES = [
    [(0,.5),(.08,.9),(.35,1),(.75,.85),(.94,.5),(1,.04)],
    [(0,.8),(.10,1),(.35,.78),(.60,.55),(.82,.29),(1,.02)],
    [(0,.38),(.12,.74),(.40,1),(.63,.90),(.85,.50),(1,.03)],
]

def tetra(mb, points, mat):
    """Closed flattened bough volume (4 triangles), no detached leaf cards."""
    for face in ((0,2,1),(0,1,3),(0,3,2),(1,2,3)):
        mb.face([points[i] for i in face], [(0,0),(1,0),(.5,1)], mat)

def spruce(mb, c, height, radius, key, lod):
    # Fuller drooping spindle boughs. Eight triangles per closed bough;
    # High savings are budget headroom, not a quality target.
    whorls = [.08,.19,.30,.41,.52,.63,.74,.85] if lod == 0 else [.14,.38,.62,.86]
    branches = 5 if lod == 0 else 3
    for j,f in enumerate(whorls):
        length=radius*(1-f)**.72*(1.18 if lod == 0 else 1.20)
        for i in range(branches):
            angle=key*.63+j*1.69+i*2*math.pi/branches+.28*(h(key,j,i,'angle')-.5)
            direction=np.array([math.cos(angle),math.sin(angle)])
            side=np.array([-direction[1],direction[0]])
            ll=length*(.82+.36*h(key,j,i,'len'))
            level=f+.035*(h(key,j,i,'height')-.5)
            centre=c+np.r_[direction*ll*.47,height*level]
            width=radius*(.48 if lod == 0 else .74)*(1-f)**.72
            hh=height*(.075 if lod == 0 else .20)*(1-.4*f)
            # Roots connect to the trunk; tips droop independently instead of a continuous conical skirt.
            pts=[c+np.array([0,0,height*(level+.055)]),
                 c+np.r_[direction*ll,height*(level-.045)],
                 centre+np.r_[side*width,0],centre-np.r_[side*width,0],
                 centre+[0,0,hh],centre-[0,0,hh]]
            for face in ((0,2,4),(2,1,4),(1,3,4),(3,0,4),(2,0,5),(1,2,5),(3,1,5),(0,3,5)):
                mb.face([pts[v] for v in face],[(0,0),(1,0),(.5,1)],'spruce')
    tetra(mb,[c+[-.045,-.045,0],c+[.045,-.045,0],c+[0,.045,0],c+[0,0,height]],'trunk')

def thuja(mb,c,height,radius,key,lod,habit=None):
    habit = key%3 if habit is None else habit
    profile=PROFILES[habit]
    if lod:
        profile=[profile[0],profile[2],profile[3],profile[-1]]
        if habit == 1: profile=[profile[0],profile[1],profile[-1]]
    sides=8 if lod == 0 else 4
    rings=[]
    for j,(f,rr) in enumerate(profile):
        ring=[]
        for i in range(sides):
            a=i*2*math.pi/sides+.24*math.sin(j)+key
            rad=radius*rr*(.86+.28*h(key,j,i))
            ring.append(c+np.array([math.cos(a)*rad,math.sin(a)*rad,height*f]))
        rings.append(ring)
    for j in range(len(rings)-1):
        for i in range(sides):
            ii=(i+1)%sides
            mb.face([rings[j][i],rings[j][ii],rings[j+1][ii],rings[j+1][i]],[(0,0)]*4,'thuja')

def baseline_plants(lod):
    src=SOURCE.read_text(encoding='utf-8')
    block=src[src.index('    # thujas:'):src.index('    # flag poles with the national flag')]
    local=dict(g);local.update(mb=MB(),lod=lod,G=g['SPEC']['ground'])
    exec(compile('if True:\n'+block, 'baseline_plant_block', 'exec'),local)
    mb=local['mb']
    mb.M=['thuja' if m=='fire_station' else m for m in mb.M]
    return mb

def candidate_plants(lod, shift=4):
    mb=MB()
    for e,n,z,hh,r,key in g['SPEC']['ground']['thuja']:
        thuja(mb,g['en_to_uvz']([e,n,z]),hh,r,key,lod)
    for e,n,z,hh,r,key in g['SPEC']['ground']['spruce']:
        c=g['en_to_uvz']([e,n,z])
        # Only the two foreground spruces in front of the arches shift right;
        # the separate wing conifer stays at its reference position.
        if key < 2: c[0]+=shift
        spruce(mb,c,hh,r,key,lod)
    return mb

COLORS={'fire_station':(146,157,171),'fire_station_alpha':(114,125,145),'hedge_thuja':(41,76,43),
        'hedge_shell_thuja':(49,87,44),'thuja':(48,83,47),'spruce':(36,73,47),'trunk':(79,71,54)}
def project(mb,camera,size=(460,212),look_override=None):
    eye=np.array(camera['pos']);forward=np.array(camera['look_at'])-eye
    forward/=np.linalg.norm(forward);right=np.cross(forward,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,forward)
    vv=np.array(mb.V);en=vv[:,:1]*g['AX_U']+vv[:,1:2]*g['AX_V']+g['AX_O']
    world=np.c_[en,vv[:,2]+g['FLOOR']];v=world-eye
    z=v@forward;f=size[1]/(2*math.tan(math.radians(camera['fov_deg'])/2))
    xy=np.c_[size[0]/2+f*(v@right)/z,size[1]/2-f*(v@up)/z]
    rgb=np.full((size[1],size[0],3),(224,229,234),dtype=np.uint8)
    depth=np.full((size[1],size[0]),np.inf)
    for face,mat in zip(mb.F,mb.M):
        if min(z[list(face)])<=0: continue
        for j in range(1,len(face)-1):
            ids=[face[0],face[j],face[j+1]];p=xy[ids];zz=z[ids]
            x0=max(0,int(np.floor(min(p[:,0]))));x1=min(size[0]-1,int(np.ceil(max(p[:,0]))))
            y0=max(0,int(np.floor(min(p[:,1]))));y1=min(size[1]-1,int(np.ceil(max(p[:,1]))))
            if x1<x0 or y1<y0: continue
            den=(p[1,1]-p[2,1])*(p[0,0]-p[2,0])+(p[2,0]-p[1,0])*(p[0,1]-p[2,1])
            if abs(den)<1e-10:continue
            xx,yy=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
            a=((p[1,1]-p[2,1])*(xx-p[2,0])+(p[2,0]-p[1,0])*(yy-p[2,1]))/den
            b=((p[2,1]-p[0,1])*(xx-p[2,0])+(p[0,0]-p[2,0])*(yy-p[2,1]))/den
            c=1-a-b;dist=1/(a/zz[0]+b/zz[1]+c/zz[2])
            dst=depth[y0:y1+1,x0:x1+1];inside=(a>=0)&(b>=0)&(c>=0)&(dist<dst)
            dst[inside]=dist[inside];rgb[y0:y1+1,x0:x1+1][inside]=COLORS.get(mat,(112,129,113))
    return Image.fromarray(rgb)


def combine(*meshes):
    mb=MB()
    for m in meshes:
        off=len(mb.V);mb.V.extend(m.V);mb.F.extend(tuple(i+off for i in f) for f in m.F);mb.M.extend(m.M);mb.UV.extend(m.UV)
    return mb

def tri_count(mb): return sum(len(f)-2 for f in mb.F)

cams=json.loads((ROOT/'Data/Regions/bialystok-industrial-c/generated/control_cameras.json').read_text())['cameras']
camera=next(c for c in cams if c['id']=='fire_station_ref7197')
building=MB();g['build_hall'](building,1);g['build_middle'](building,1)
# Project actual front arch positions as colored regions (not material calibration).
ga=g['LAY']['arch'];hall=g['D']['hall'];COLORS['arch_marker']=(72,92,116)
for arch_index,center in enumerate(hall['arch_windows_u']):
    marker='arch_marker_'+str(arch_index);COLORS[marker]=(72+arch_index*8,92,116)
    w=ga['w'];spring=ga['spring'];rise=ga['rise'];sill=hall['arch_window_sill_z']
    pts=[P3((center-w/2,-.20),sill),P3((center+w/2,-.20),sill)]
    for x in np.linspace(w/2,-w/2,33):
        pts.append(P3((center+x,-.20),sill+spring+rise*math.sqrt(max(0,1-(2*x/w)**2))))
    building.face(pts,[(0,0)]*len(pts),marker)
    head_marker='arch_head_'+str(arch_index);COLORS[head_marker]=(200+arch_index*20,80,180)
    head=[P3((center-w/2,-.205),sill+spring),P3((center+w/2,-.205),sill+spring)]
    for x in np.linspace(w/2,-w/2,33):
        head.append(P3((center+x,-.205),sill+spring+rise*math.sqrt(max(0,1-(2*x/w)**2))))
    building.face(head,[(0,0)]*len(head),head_marker)
sheet=Image.new('RGB',(960,720),'white');d=ImageDraw.Draw(sheet)
d.text((10,8),'SOURCE ONLY / Unity VERTICAL FOV, 460x212; unlit, no runtime material/alpha mip proof',fill='black')
counts={};arch_visibility={}
base_projection=np.array(project(building,camera))
for row,lod in enumerate((1,0)):
    for col,(label,plant) in enumerate((('baseline',baseline_plants(lod)),('candidate +4u m',candidate_plants(lod)))):
        frame=project(combine(building,plant),camera)
        sheet.paste(frame,(10+480*col,48+330*row))
        frame_np=np.array(frame)
        arch_visibility[f'{label}_lod{lod}']={}
        for arch_index in range(2):
            color=COLORS['arch_marker_'+str(arch_index)];head_color=COLORS['arch_head_'+str(arch_index)]
            base_whole=np.all(base_projection==color,axis=2)|np.all(base_projection==head_color,axis=2)
            visible_whole=np.all(frame_np==color,axis=2)|np.all(frame_np==head_color,axis=2)
            base_head=np.all(base_projection==head_color,axis=2)
            visible_head=np.all(frame_np==head_color,axis=2)
            arch_visibility[f'{label}_lod{lod}'][str(arch_index)]={
                'whole_arched_opening':{'unoccluded_pixels':int(base_whole.sum()),'visible_pixels':int(visible_whole.sum()),'visible_fraction':float(visible_whole.sum()/base_whole.sum())},
                'upper_arch_head_above_spring':{'unoccluded_pixels':int(base_head.sum()),'visible_pixels':int(visible_head.sum()),'visible_fraction':float(visible_head.sum()/base_head.sum())}}
            frame_np[np.all(frame_np==head_color,axis=2)]=color
        sheet.paste(Image.fromarray(frame_np),(10+480*col,48+330*row))
        d.text((10+480*col,30+330*row),f'{label} LOD{lod}; plant triangles={tri_count(plant)}',fill='black')
        counts[f'{label}_lod{lod}']=tri_count(plant)
sheet.save(OUT/'layout.jpg',quality=93)
roi=Image.fromarray(base_projection).resize((920,600),Image.Resampling.NEAREST)
rdr=ImageDraw.Draw(roi)
rdr.text((12,12),'Projected opening masks: blue = lower region; pink = upper arch head above spring.',fill='black')
rdr.text((12,28),'Whole metric = blue + pink, including mullion areas; NOT a measured glass-pane/albedo ROI.',fill='black')
roi.save(OUT/'arch-rois.jpg',quality=95)

# Same dimensions distinguish habit independently of size/spacing.
gallery=Image.new('RGB',(960,420),'white');dg=ImageDraw.Draw(gallery)
for col in range(3):
    mb=MB();thuja(mb,np.array([col*0.,0,0]),4,1,12+col,0,habit=col)
    eye=g['AX_O']+g['AX_U']*0+g['AX_V']*-12
    cam={'pos':[*eye,g['FLOOR']+2.0],'look_at':[*g['AX_O'],g['FLOOR']+2.0],'fov_deg':28}
    gallery.paste(project(mb,cam,(310,360)),(5+320*col,45));dg.text((12+320*col,15),('column','cone','egg')[col]+' / unlit source mesh',fill='black')
gallery.save(OUT/'thuja-forms.jpg',quality=93)

# Use the production hash function for spacing so this proof does not silently change seeds.
htree=ast.parse((ROOT/'tools/worldgen/streetscape/hero_building.py').read_text())
hf=next(n for n in htree.body if isinstance(n,ast.FunctionDef) and n.name=='_hash01')
hn={'hashlib':hashlib};exec(compile(ast.Module(body=[hf],type_ignores=[]),'hash','exec'),hn)
th=g['D']['thuja'];N=th['count'];length=float(np.linalg.norm(np.array(th['row_uv'][1])-th['row_uv'][0]));step=length/N
spacing={}
for jitter in (.5,.25):
    ts=[(k+.5)/N+(hn['_hash01'](g['ASSET'],'t',k)-.5)*jitter/N for k in range(N)]
    gaps=np.diff(ts)*length
    spacing[str(jitter)]={'min_m':float(min(gaps)),'max_m':float(max(gaps)),'nominal_m':step,'max_relative_deviation':float(np.max(abs(gaps/step-1)))}
for p,digest in snapshot.items(): assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==digest
raw_manifest=json.loads((OUT.parent/'baseline-raw-sha256.json').read_text())
for name,digest in raw_manifest.items():
    assert hashlib.sha256((ROOT/'Data/raw/derived/bialystok-industrial-c/world'/name).read_bytes()).hexdigest()==digest
(OUT/'proof.json').write_text(json.dumps({'status':'ARTIFACT_ONLY_UNLIT_SOURCE_MODEL_NOT_RUNTIME_ACCEPTANCE','source_sha256':snapshot,'plant_triangles':counts,'arch_visibility_definition':{'whole':'projected full arched opening silhouette from sill to curved top, including mullion/trim areas; NOT actual glass-pane pixels','head':'subset above sill+spring (4.2m floor-relative), the circular upper cap up to5.5m; excludes lower rectangular area','method':'CPU opaque source-mesh depth test against fixed fire_station_ref7197 camera verticalFOV at460x212; source shell treated opaque, NOT runtime alpha coverage; baseline ground/thuja positions retained','roi_proof':'arch-rois.jpg blue+pink=whole, pink=head'},'arch_visibility':arch_visibility,'spacing':spacing,'spruce_shift_m':4,'spruce_shift_ids':[0,1],'wing_conifer_id2':'unchanged; moving +u would place it into left arch','ground_height':'baseline heights retained for projection only; production must resample terrain through planner'},indent=2))
print(json.dumps({'plant_triangles':counts,'arch_visibility_definition':{'whole':'projected full arched opening silhouette from sill to curved top, including mullion/trim areas; NOT actual glass-pane pixels','head':'subset above sill+spring (4.2m floor-relative), the circular upper cap up to5.5m; excludes lower rectangular area','method':'CPU opaque source-mesh depth test against fixed fire_station_ref7197 camera verticalFOV at460x212; source shell treated opaque, NOT runtime alpha coverage; baseline ground/thuja positions retained','roi_proof':'arch-rois.jpg blue+pink=whole, pink=head'},'arch_visibility':arch_visibility,'spacing':spacing},indent=2))
