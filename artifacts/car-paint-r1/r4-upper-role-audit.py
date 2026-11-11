"""Level0 bilinear CPU effect using actual native UV/normal/Tile, before import."""
from pathlib import Path
import json
import runpy
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
ART=ROOT/'artifacts/car-paint-r1'
data=runpy.run_path(str(ART/'r4-native-uv-audit.py'))
matroot=ROOT/'art-source/world/materials'
old=np.asarray(Image.open(matroot/'car_grime/High/T_car_grime_BaseColor.png'),np.float32)/255
new=np.asarray(Image.open(matroot/'car_grime_clean/High/T_car_grime_clean_BaseColor.png'),np.float32)/255
oldmask=np.asarray(Image.open(matroot/'car_grime/High/T_car_grime_MaskMap.png'),np.float32)/255
newmask=np.asarray(Image.open(matroot/'car_grime_clean/High/T_car_grime_clean_MaskMap.png'),np.float32)/255
def linear(a):return np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4)
old=linear(old);new=linear(new)
def sample(image,uv):
    h,w=image.shape[:2]
    x=(uv[:,0]%1)*w-.5;y=(1-uv[:,1]%1)*h-.5
    ix=np.floor(x).astype(int);iy=np.floor(y).astype(int)
    fx=(x-ix)[:,None];fy=(y-iy)[:,None]
    return ((image[iy%h,ix%w]*(1-fx)+image[iy%h,(ix+1)%w]*fx)*(1-fy)+
            (image[(iy+1)%h,ix%w]*(1-fx)+image[(iy+1)%h,(ix+1)%w]*fx)*fy)
def smooth(a,b,x):
    q=np.clip((x-a)/(b-a),0,1);return q*q*(3-2*q)
rows=[]
for s in data['native_samples']:
    p=s['position'];n=s['normal'];uv=s['uv']/np.asarray(s['tile'][:2])
    for role,choose in (
        ('bonnet_horizontal',(n[:,1]>.85)&(p[:,1]>.75)&(p[:,1]<1.3)&(p[:,2]>.2)),
        ('roof_horizontal',(n[:,1]>.85)&(p[:,1]>=1.3)),
        ('upper_transition',(np.abs(n[:,1])>.45)&(np.abs(n[:,1])<=.85)&(p[:,1]>.6))):
        if not np.any(choose):continue
        q=uv[choose];height=s['uv'][choose,1]
        keep=smooth(.45,.85,np.abs(n[choose,1]))*smooth(.6,.8,height)
        rgb=[];mask=[];residual=[];smooth_residual=[]
        for phase in np.arange(8)/8:
            use=q.copy();use[:,0]+=phase
            a=sample(old,use);b=sample(new,use)
            ma=sample(oldmask,use)[:,3];nm=sample(newmask,use);mb=nm[:,3]
            rgb.append(np.mean((b-a)/np.maximum(a,1e-6),axis=1))
            mask.append(mb-ma)
            coverage=nm[:,0]
            forward=(1-.30*coverage)[:,None]*np.column_stack([np.ones(len(coverage)),1-.08*coverage,1-.22*coverage])
            restored=b*(1-keep[:,None]+keep[:,None]*forward)
            restored_a=np.clip(mb-.35*coverage*keep,0,1)
            legacy=np.clip((.68-ma)/.35,0,1)*(1-smooth(1.3,1.5,height))
            removed=legacy*(1-keep)
            old_multiplier=(1-.30*removed)[:,None]*np.column_stack([np.ones(len(removed)),1-.08*removed,1-.22*removed])
            r3=a/np.maximum(old_multiplier,.2)
            r3a=np.clip(ma+.35*removed,0,1)
            residual.append(np.mean((restored-r3)/np.maximum(r3,1e-6),axis=1))
            smooth_residual.append(restored_a-r3a)
        change=np.asarray(rgb);rough=np.asarray(mask)
        rows.append(dict(prototype=s['prototype'],lod=s['lod'],role=role,triangles=int(choose.sum()),
            old_r3_keep_upper_min=float(keep.min()),old_r3_keep_upper_max=float(keep.max()),
            base_relative_gain_mean=float(change.mean()),base_relative_gain_max=float(change.max()),
            smoothness_delta_mean=float(rough.mean()),smoothness_delta_max=float(rough.max()),
            restored_relative_residual_mean=float(np.asarray(residual).mean()),
            restored_relative_residual_max_abs=float(np.abs(residual).max()),
            restored_smoothness_residual_max_abs=float(np.abs(smooth_residual).max())))
out=dict(method='Actual serialized native paint triangle centroids, normalized Snorm8 normals, bound Tile4x4, eight phase offsets; uncompressed High PNG level0 bilinear CPU model',
    causal_problem_confirmed=any(r['base_relative_gain_max']>.001 for r in rows),
    note='No lighting/GPU/ASTC or displayed RGB claim. R3 keepUpper preserves old map film; clean map currently removes it from horizontal upper surfaces. Do not import until role handling is resolved.',rows=rows)
(ART/'r4-upper-role-restoration.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(dict(confirmed=out['causal_problem_confirmed'],maximum_base_gain=max(r['base_relative_gain_max'] for r in rows),
                     maximum_smoothness_delta=max(r['smoothness_delta_max'] for r in rows),samples=len(rows))))
