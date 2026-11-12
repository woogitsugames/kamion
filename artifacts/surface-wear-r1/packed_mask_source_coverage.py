"""Project actual old-road geometry and sample the actual GPU-readback open-R field."""
import json,hashlib
import numpy as np
from PIL import Image
from bus_world_proof import ROOT,OUT,read

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sample_repeat(data,world):
    uv=np.mod(world/16,1);p=uv*data.shape[0]-.5;i=np.floor(p).astype(int);f=p-i
    x,y=i[:,0]%len(data),i[:,1]%len(data);xx,yy=(x+1)%len(data),(y+1)%len(data)
    return data[y,x]*(1-f[:,0])*(1-f[:,1])+data[y,xx]*f[:,0]*(1-f[:,1])+data[yy,x]*(1-f[:,0])*f[:,1]+data[yy,xx]*f[:,0]*f[:,1]
def main():
    directory=OUT/'packed-mask-activation/Low-overcast'
    activation=json.loads((directory/'activation.json').read_text());assert len(activation['frames'])==4
    qa=OUT/'PackedRoadMask.shader'
    for r in activation['frames']:
        assert not r['worldDetail'] and r['actuallyAssigned'] and r['assignedRenderers']==44
        assert r['shaderSourceSha256']==sha(qa) and r['maskSize']==2048 and r['maskMips']==12
        assert r['maskUVMultiplier']==.25 and r['metallicScale']==0 and r['crackStrength']==.75
        assert r['tile']==dict(x=4.,y=4.,z=16.,w=1.)
    metadata=json.loads((directory/'gpu-openR.json').read_text());binary=OUT/'packed-mask16-private/GPU-openR-mip0.f32'
    assert sha(binary)==metadata['sha256'];red=np.fromfile(binary,dtype='<f4').reshape(2048,2048)
    specs={c['id']:c for c in json.loads((OUT/'qa-packed-mask-cameras.json').read_text())['cameras']}
    runtime=json.loads((directory/'runtime-pose.json').read_text())['cameras'];rows=[]
    for name,chunk,box in [('d_wear_lane_old','3_4',[470,280,610,400]),('d_wear_missing_uv_2','5_4',[300,300,850,415])]:
        cam=next(c for c in runtime if c['id']==name);_,nodes=read(ROOT/f'Data/raw/derived/bialystok-industrial-c/world/chunk_{chunk}.glb')
        primitives=list(nodes['road']);source_chunks=[chunk]
        if name=='d_wear_missing_uv_2':
            # The selected foreground crosses the eastern chunk boundary; include actual neighbour geometry.
            _,neighbour=read(ROOT/'Data/raw/derived/bialystok-industrial-c/world/chunk_6_4.glb');primitives.extend(neighbour['road']);source_chunks.append('6_4')
        image=Image.open(directory/(name+'.png'));scale=image.width/960;x0,y0,x1,y1=[round(v*scale)for v in box]
        depth=np.full((y1-y0,x1-x0),np.inf);world=np.full((*depth.shape,2),np.nan)
        anchor=specs[name]['pos'][2]-cam['cameraPosition']['y'];matrix=np.array(cam['projection']).reshape(4,4)@np.array(cam['view']).reshape(4,4)
        for material,attrs in primitives:
            if material!='road_asphalt':continue
            xyz=attrs['POSITION'].astype(float);xyz[:,0]*=-1;xyz[:,1]-=anchor
            clip=matrix@np.column_stack([xyz,np.ones(len(xyz))]).T;ndc=(clip[:3]/clip[3]).T
            points=np.column_stack([(ndc[:,0]+1)*image.width/2,(1-ndc[:,1])*image.height/2])
            for tri in attrs['indices'].reshape(-1,3):
                if np.any(clip[3,tri]<=0):continue
                p=points[tri];lo=np.maximum(np.floor(p.min(0)).astype(int),[x0,y0]);hi=np.minimum(np.ceil(p.max(0)).astype(int),[x1,y1])
                if np.any(lo>=hi):continue
                xs,ys=np.meshgrid(np.arange(lo[0],hi[0])+.5,np.arange(lo[1],hi[1])+.5);a,b,c=p
                den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
                if abs(den)<1e-10:continue
                wa=((b[1]-c[1])*(xs-c[0])+(c[0]-b[0])*(ys-c[1]))/den;wb=((c[1]-a[1])*(xs-c[0])+(a[0]-c[0])*(ys-c[1]))/den
                weights=np.stack([wa,wb,1-wa-wb],-1);z=weights@ndc[tri,2];sl=np.s_[lo[1]-y0:hi[1]-y0,lo[0]-x0:hi[0]-x0]
                valid=np.all(weights>=-1e-6,axis=-1)&(z<depth[sl]);w=weights/clip[3,tri];pos=(w@xyz[tri][:,[0,2]])/w.sum(-1)[...,None]
                depth[sl][valid]=z[valid];world[sl][valid]=pos[valid]
        valid=np.isfinite(world[:,:,0]);assert valid.any();samples=sample_repeat(red,world[valid])
        rows.append(dict(camera=name,source_chunks=source_chunks,roi960=box,road_pixels=int(valid.sum()),roi_pixels=int(valid.size),source_road_fraction=float(valid.mean()),
            GPU_R_mean=float(samples.mean()),GPU_R_positive_fraction=float((samples>0).mean()),GPU_R_over01_fraction=float((samples>.1).mean()),GPU_R_max=float(samples.max())))
    identical=[]
    for camera in runtime:
        a=directory/(camera['id']+'.png');b=OUT/'packed-mask-qa/Low-overcast'/(camera['id']+'.png')
        identical.append(dict(camera=camera['id'],same_pixels=np.array_equal(np.asarray(Image.open(a)),np.asarray(Image.open(b)))))
    report=dict(actual_activation=activation,GPU_R_readback=metadata,source_mask_coverage=rows,supplemental_same_variant_images=identical,
        note='Actual render callback proves Low detail keyword false and the assigned2kQA mask. Coverage projects actual road triangles into inspected ROIs and bilinearly samples the actual GPU mip0 R at world/16. It is not a per-fragment autoLOD/amount readback or a quality PASS; positive data and branch activation are established without a new tuning variant.')
    (OUT/'packed-mask16-activation-coverage-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(rows));print(identical)
if __name__=='__main__':main()
