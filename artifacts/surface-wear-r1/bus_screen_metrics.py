"""Native screen-space oil contrast, using its actual projected source fan (not an invented ROI)."""
from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageDraw
from bus_world_proof import ROOT,OUT,read

def main():
    rows=json.loads((OUT/'bus-only-after/High-overcast/runtime-pose.json').read_text())['cameras']
    camera=next(x for x in rows if x['id']=='d_field_bus464_close')
    spec=next(x for x in json.loads((OUT/'qa-final-field-cameras.json').read_text())['cameras']if x['id']==camera['id'])
    anchor_z=spec['pos'][2]-camera['cameraPosition']['y']
    _,nodes=read(OUT/'bus-only-raw/chunk_4_5.glb')
    attrs=next(a for material,a in nodes['markings']if material=='decal_oil')
    xyz=attrs['POSITION'][-10:].astype(float);xyz[:,0]*=-1;xyz[:,1]-=anchor_z
    clip=np.array(camera['projection']).reshape(4,4)@np.array(camera['view']).reshape(4,4)@np.column_stack([xyz,np.ones(10)]).T
    ndc=(clip[:3]/clip[3]).T;points=np.column_stack([(ndc[:,0]+1)*camera['width']*.5,(1-ndc[:,1])*camera['height']*.5])
    mask=Image.new('1',(camera['width'],camera['height']));draw=ImageDraw.Draw(mask)
    for k in range(9):draw.polygon([tuple(points[0]),tuple(points[k+1]),tuple(points[1+(k+1)%9])],fill=1)
    mask=np.asarray(mask,bool);bbox=[int(points[:,0].min()),int(points[:,1].min()),int(points[:,0].max())+1,int(points[:,1].max())+1]
    ring=Image.new('1',(camera['width'],camera['height']));ImageDraw.Draw(ring).rectangle([bbox[0]-45,bbox[1]-45,bbox[2]+45,bbox[3]+45],fill=1);background=np.asarray(ring,bool)&~mask
    results=[]
    for cond in ['Low-clear','Low-overcast','High-clear','High-overcast']:
        a=np.asarray(Image.open(OUT/'final-field-before'/cond/(camera['id']+'.png')).convert('RGB'),float)
        b=np.asarray(Image.open(OUT/'bus-only-after'/cond/(camera['id']+'.png')).convert('RGB'),float)
        delta=b-a
        results.append(dict(condition=cond,before_rgb=a[mask].mean(0).tolist(),after_rgb=b[mask].mean(0).tolist(),mean_rgb_delta=delta[mask].mean(0).tolist(),
                            background_mean_abs_lsb=float(abs(delta[background]).mean()),darkened_pixels_over3lsb=int((delta[mask].mean(1)<-3).sum())))
    packet=dict(note='Actual source fan projected through captured runtime view/projection; screen RGB is weather/exposure-dependent, NOT physicaloil/albedo measurement or ownerPASS. Background ring includes AA/dither; originalimages untouched.',camera=camera['id'],native_bbox=bbox,fan_pixels=int(mask.sum()),anchor_z_inferred=anchor_z,results=results)
    (OUT/'bus-screen-metrics.json').write_text(json.dumps(packet,indent=2)+'\n');print(json.dumps(packet))
if __name__=='__main__':main()
