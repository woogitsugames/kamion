"""Legacy kerb-scuff ROI control, projected from immutable actual geometry."""
import json
import numpy as np
from PIL import Image,ImageDraw
from bus_world_proof import OUT,read

def main():
    _,nodes=read(OUT/'raw-before/chunk_6_6.glb')
    attrs=next(a for m,a in nodes['markings']if m=='decal_tyre')
    xyz=attrs['POSITION'].astype(float);idx=attrs['indices'].reshape(-1,3)
    # Raw GLTF coordinate(-E,U,N), raw V is1-strength. Match only original strength2.5 scuffs.
    center=np.array([-617.8605,-601.8095])
    near=np.linalg.norm(xyz[idx][:,:,[0,2]].mean(1)-center,axis=1)<20
    scuffs=np.all(attrs['TEXCOORD_1'][idx,1]<-1.49,axis=1)
    idx=idx[near&scuffs];assert len(idx)==152,len(idx)
    specs={c['id']:c for c in json.loads((OUT/'qa-gate-field-cameras.json').read_text())['cameras']}
    results=[]
    for cond in ['Low-clear','Low-overcast','High-clear','High-overcast']:
        packet=json.loads((OUT/'gate-r2-after'/cond/'runtime-pose.json').read_text())
        for cam in packet['cameras']:
            if cam['id']not in specs:continue
            name=cam['id'];spec=specs[name]
            expected=np.array([spec['pos'][0],cam['cameraPosition']['y'],spec['pos'][1]])
            actual=np.array([cam['cameraPosition'][k]for k in ['x','y','z']])
            assert np.max(abs(expected-actual))<.0002
            anchor=spec['pos'][2]-actual[1]
            pos=xyz.copy();pos[:,0]*=-1;pos[:,1]-=anchor
            clip=np.array(cam['projection']).reshape(4,4)@np.array(cam['view']).reshape(4,4)@np.column_stack([pos,np.ones(len(pos))]).T
            ndc=(clip[:3]/clip[3]).T
            before=Image.open(OUT/'gate-kerb-before'/cond/(name+'.png')).convert('RGB')
            after=Image.open(OUT/'gate-r2-after'/cond/(name+'.png')).convert('RGB')
            assert before.size==after.size
            points=np.column_stack([(ndc[:,0]+1)*after.width/2,(1-ndc[:,1])*after.height/2])
            mask=Image.new('1',after.size);draw=ImageDraw.Draw(mask)
            for tri in idx:
                if np.all(clip[3,tri]>0):draw.polygon([tuple(points[i])for i in tri],fill=1)
            mask=np.asarray(mask,bool);assert mask.any()
            a=np.asarray(before,float);b=np.asarray(after,float);delta=(b-a)[mask]
            results.append(dict(condition=cond,camera=name,projected_legacy_scuff_pixels=int(mask.sum()),
                                mean_rgb_delta=delta.mean(0).tolist(),mean_abs_rgb_lsb=float(abs(delta).mean()),
                                p95_abs_rgb_lsb=float(np.percentile(abs(delta),95)),fraction_rgb_over3_lsb=float((abs(delta)>3).mean())))
            overlay=after.copy();pixels=np.asarray(overlay).copy();pixels[mask]=.5*pixels[mask]+.5*np.array([255,60,30]);overlay=Image.fromarray(pixels)
            overlay.thumbnail((960,960));overlay.save(OUT/f'kerb-negative-mask-{cond}-{name}.jpg',quality=90)
    report=dict(legacy_source_triangles=152,note='Actual immutable strength2.5 kerb-scuff geometry mask, not new gate tracks. New runtime camera agrees authored world position; older kerb BEFORE predates runtime recorder, so no retroactive matrix-equality claim. RGB includes raster AA/dither and exposure, not physical reflectance or globalqualityPASS.',results=results)
    (OUT/'gate-r2-kerb-negative-metrics.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
