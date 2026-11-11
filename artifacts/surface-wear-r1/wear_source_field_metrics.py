"""Actual road-field rasterization inside visually checked asphalt ROIs."""
import json
import numpy as np
from PIL import Image
from bus_world_proof import ROOT,OUT,read
from wear_probe_metrics import luminance

CASES=[('d_wear_lane_old','3_4',[470,280,610,400]),('d_wear_newroad_negative','0_0',[800,150,870,230])]
def main():
    specs={c['id']:c for c in json.loads((OUT/'qa-wear-probe-cameras.json').read_text())['cameras']}
    native=json.loads((OUT/'native-gate-r2.json').read_text())['materials']
    rows=[]
    for camera_id,chunk,box in CASES:
        _,nodes=read(ROOT/f'Data/raw/derived/bialystok-industrial-c/world/chunk_{chunk}.glb')
        cam=next(c for c in json.loads((OUT/'wear-probe-after/High-overcast/runtime-pose.json').read_text())['cameras']if c['id']==camera_id)
        anchor=specs[camera_id]['pos'][2]-cam['cameraPosition']['y']
        full=Image.open(OUT/'wear-probe-before/High-overcast'/(camera_id+'.png'))
        x0,y0,x1,y1=[round(v*full.width/960)for v in box]
        depth=np.full((y1-y0,x1-x0),np.inf);uv=np.full((*depth.shape,2),np.nan);material=np.full(depth.shape,'',dtype=object)
        matrix=np.array(cam['projection']).reshape(4,4)@np.array(cam['view']).reshape(4,4)
        for name,attrs in nodes['road']:
            if name not in ['road_asphalt','road_asphalt_new']:continue
            xyz=attrs['POSITION'].astype(float);xyz[:,0]*=-1;xyz[:,1]-=anchor
            clip=matrix@np.column_stack([xyz,np.ones(len(xyz))]).T
            ndc=(clip[:3]/clip[3]).T;points=np.column_stack([(ndc[:,0]+1)*full.width/2,(1-ndc[:,1])*full.height/2])
            if 'TEXCOORD_1'in attrs:
                field=attrs['TEXCOORD_1'].copy();field[:,1]=1-field[:,1]
                field=field.astype(np.float16).astype(float) # Actual uploaded channel is Half.
            else:field=np.tile([-1.,5.],(len(xyz),1))
            for tri in attrs['indices'].reshape(-1,3):
                if np.any(clip[3,tri]<=0):continue
                p=points[tri];lo=np.maximum(np.floor(p.min(0)).astype(int),[x0,y0]);hi=np.minimum(np.ceil(p.max(0)).astype(int),[x1,y1])
                if np.any(lo>=hi):continue
                xs,ys=np.meshgrid(np.arange(lo[0],hi[0])+.5,np.arange(lo[1],hi[1])+.5)
                a,b,c=p;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
                if abs(den)<1e-10:continue
                wa=((b[1]-c[1])*(xs-c[0])+(c[0]-b[0])*(ys-c[1]))/den
                wb=((c[1]-a[1])*(xs-c[0])+(a[0]-c[0])*(ys-c[1]))/den
                weights=np.stack([wa,wb,1-wa-wb],axis=-1);z=weights@ndc[tri,2]
                sl=np.s_[lo[1]-y0:hi[1]-y0,lo[0]-x0:hi[0]-x0]
                mask=np.all(weights>=-1e-6,axis=-1)&(z<depth[sl])
                perspective=weights/clip[3,tri];sample=(perspective@field[tri])/perspective.sum(-1)[...,None]
                depth[sl][mask]=z[mask];uv[sl][mask]=sample[mask];material[sl][mask]=name
        valid=np.isfinite(uv[:,:,0]);assert valid.any(),camera_id
        for mat in sorted(set(material[valid])):
            mask=valid&(material==mat);w=uv[mask];known=w[:,0]>=-.5;lc=np.mod(w[:,0],1)
            wp=np.clip(1-abs(abs(lc-.5)-.24)/.11,0,1)*known
            edge=(w[:,1]<.65)&known
            bind=next(m for m in native if m['path'].endswith('/M_'+mat+'.mat'))
            assert '_ROADWEAR'in bind['keywords'].split(',')
            entry=dict(camera=camera_id,chunk=chunk,roi960=box,source_material=mat,pixels=int(mask.sum()),roi_pixels=int(valid.size),source_coverage_fraction=float(mask.mean()),
                       known_fraction=float(known.mean()),wheel_mask_positive_fraction=float((wp>.01).mean()),wheel_mask_mean=float(wp.mean()),wheel_mask_max=float(wp.max()),
                       edge_under_065m_fraction=float(edge.mean()),edge_distance_min=float(w[:,1].min()),native_binding=bind,conditions=[])
            for cond in ['Low-clear','Low-overcast','High-clear','High-overcast']:
                before=np.asarray(Image.open(OUT/'wear-probe-before'/cond/(camera_id+'.png')).convert('RGB'),float)[y0:y1,x0:x1]
                after=np.asarray(Image.open(OUT/'wear-probe-after'/cond/(camera_id+'.png')).convert('RGB'),float)[y0:y1,x0:x1]
                delta=luminance(after)-luminance(before);wheel=np.zeros_like(valid);wheel[mask]=wp>.01
                entry['conditions'].append(dict(condition=cond,source_asphalt_mean_delta_lsb=float(delta[mask].mean()),
                    actual_wheel_mask_mean_delta_lsb=float(delta[wheel].mean())if wheel.any()else None,
                    actual_wheel_mask_pixels=int(wheel.sum())))
            rows.append(entry)
    report=dict(note='Actual GLB road triangles projected with runtime matrices, Half UV1 and perspective interpolation inside inspected clear-asphalt ROIs. Source masks are not a general occlusion renderer; selected ROIs contain no visible foreground objects. Zero gutter coverage here cannot validate the separate edge block. Display deltas are not physical albedo or a visual PASS.',rows=rows)
    (OUT/'wear-source-field-metrics.json').write_text(json.dumps(report,indent=2)+'\n')
    for row in rows:print(row['camera'],row['source_material'],'known',row['known_fraction'],'wp positive',row['wheel_mask_positive_fraction'],'edge',row['edge_under_065m_fraction'],[(r['condition'],r['actual_wheel_mask_mean_delta_lsb'])for r in row['conditions']])
if __name__=='__main__':main()
