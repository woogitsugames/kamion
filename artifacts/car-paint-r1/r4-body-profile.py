"""CPU body/UV identity at fresh pixels using actual native triangle buffers."""
from pathlib import Path
import importlib.util
import json
import runpy
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'artifacts/car-paint-r1'
native=runpy.run_path(str(ART/'r4-native-uv-audit.py'))
spec=importlib.util.spec_from_file_location('model',ART/'r4-model.py');model=importlib.util.module_from_spec(spec);spec.loader.exec_module(model)
manifest=json.loads((ROOT/'Data/Regions/bialystok-industrial-c/generated/world_manifest.json').read_text())
cars=[i for c in manifest['chunks'] for i in json.loads((ROOT/c['instances']['file']).read_text())['instances'] if i['p'].startswith(('car_','van_'))]
levels,phase=model.film_hash(np.array([[c['e'],c['n']] for c in cars]),[-1024,-1024])
def matrix(d):return np.array([[d[f'e{i}{j}'] for j in range(4)] for i in range(4)])
def packet(camera):return json.loads((ART/'r4-before/High-overcast/poses'/f'{camera}-begin.json').read_text())

def caster(camera):
    p=packet(camera);vp=matrix(p['projection'])@matrix(p['view']);inv=np.linalg.inv(vp)
    region=matrix(p['regionRoots'][0]['localToWorld']);origin=np.array(list(p['cameraParents'][0]['worldPosition'].values()))
    prepared=[]
    for j,c in enumerate(cars):
        a=c['yaw'];co=np.cos(a);si=np.sin(a)
        transform=region@np.array([[co,0,-si,c['e']],[0,1,0,c['z']],[si,0,co,c['n']],[0,0,0,1.]])
        inverse=np.linalg.inv(transform);ro=(inverse@np.r_[origin,1])[:3]
        prepared.append((j,inverse,ro))
    def cast(x,y):
        q=inv@np.array([2*(x+.5)/2340-1,1-2*(y+.5)/1080,1,1]);point=q[:3]/q[3]
        rd=point-origin;rd/=np.linalg.norm(rd)
        best=None
        for j,inverse,ro in prepared:
            c=cars[j];geometry=native['native_geometry'].get((c['p'],0))
            if geometry is None:continue
            direction=(inverse@np.r_[rd,0])[:3]
            # Conservative fixed class-sized coarse box; exact triangle test follows.
            ext=np.array([1.3,2.2,3.0]);centre=np.array([0,1.0,0])
            t0=(centre-ext-ro)/np.where(np.abs(direction)>1e-10,direction,1e-10)
            t1=(centre+ext-ro)/np.where(np.abs(direction)>1e-10,direction,1e-10)
            entry=np.max(np.minimum(t0,t1));exit=np.min(np.maximum(t0,t1))
            if exit<max(entry,0) or (best is not None and entry>best['distance']):continue
            for g in geometry:
                v=g['position'];e1=v[:,1]-v[:,0];e2=v[:,2]-v[:,0]
                h=np.cross(direction,e2);det=np.einsum('ij,ij->i',e1,h)
                safe=np.where(np.abs(det)>1e-9,det,np.inf);f=1/safe;s=ro-v[:,0]
                u=f*np.einsum('ij,ij->i',s,h);qq=np.cross(s,e1);vv=f*np.einsum('j,ij->i',direction,qq)
                distance=f*np.einsum('ij,ij->i',e2,qq)
                valid=(np.abs(det)>1e-9)&(u>=0)&(vv>=0)&(u+vv<=1)&(distance>0)
                if not np.any(valid):continue
                k=int(np.argmin(np.where(valid,distance,np.inf)));t=float(distance[k])
                if best is not None and t>=best['distance']:continue
                bary=np.array([1-u[k]-vv[k],u[k],vv[k]])
                uv=bary@g['uv'][k];pos=ro+t*direction
                payload=None if g['payload'] is None else bary@g['payload'][k]
                normal=bary@g['normal'][k];normal/=max(np.linalg.norm(normal),1e-8)
                body=c['p'].split('_')[1] if c['p'].startswith('car_') else 'van'
                sill={'hatch':.19,'sedan':.19,'estate':.19,'suv':.25,'van':.27}[body]
                def ss(a,b,x):q=np.clip((x-a)/(b-a),0,1);return q*q*(3-2*q)
                upper=float(ss(.45,.85,abs(normal[1]))*ss(.6,.8,uv[1]))
                opacity=None if payload is None or not g['material'].startswith('M_car_paint_') else float(model.opacity(payload[0],model.longitudinal_weight(payload[1]),int(levels[j]))*(1-upper))
                best=dict(prototype=c['p'],source=c['src'],instance=j,level=int(levels[j]),phase=float(phase[j]),
                    distance=t,material=g['material'],native_uv0=uv.tolist(),height_m=float(pos[1]),height_above_sill_m=float(pos[1]-sill))
                best.update(native_payload=None if payload is None else payload.tolist(),cpu_expected_opacity=opacity,keep_upper=upper)
        return best
    return cast

probes={}
image_cache={}
for camera,points in {
    'r10_wheel_02':[(x,y) for x in (1080,1180,1280) for y in (300,400,500,600,700,780,810)],
    'r10_rear_04':[(700,y) for y in (500,650,800,950,1050)]+[(1750,y) for y in (650,850,1000)],
    'r4_dirt_candidate_3':[(1150,650),(1300,700)],
}.items():
    cast=caster(camera);probes[camera]=[dict(pixel=[x,y],hit=cast(x,y)) for x,y in points]
    for row in probes[camera]:
        x,y=row['pixel']
        row['luma']={}
        for condition in ('Low-clear','Low-overcast','High-clear','High-overcast'):
            row['luma'][condition]={}
            for tag in ('r4-before','r4-focus-r1'):
                key=(camera,condition,tag)
                if key not in image_cache:image_cache[key]=np.asarray(Image.open(ART/tag/condition/f'{camera}.png').convert('RGB'),np.float32)
                im=image_cache[key]
                box=im[y-2:y+3,x-2:x+3]
                row['luma'][condition][tag]=float((box@np.array([.2126,.7152,.0722])).mean())
out=dict(method='CPU ray/native-LOD0 triangle intersection from actual BEFORE projection/mount/region matrices and canonical instance placement; no building/tree occlusion test',probes=probes,
         note='Identity and metric-height evidence at selected car pixels; not a GPU ID buffer. Nonpaint hits are excluded from body profiles.')
(ART/'r4-body-identity.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out))
