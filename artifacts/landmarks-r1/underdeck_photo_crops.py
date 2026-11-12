"""Read-only native photo details: do not confuse lighting spread with paint wear."""
from pathlib import Path
from PIL import Image
import json
import hashlib
import numpy as np

ROOT=Path(__file__).resolve().parent
path=ROOT/'reference7204-original.jpg'
im=Image.open(path).convert('RGB')
out=ROOT/'underdeck-photo-details'; out.mkdir(exist_ok=True)
regions={'front_piers':(118,323,182,420),'mid_pier':(222,325,266,409),'rear_pier':(318,328,360,408)}
meta={'source_file':path.name,'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_size':im.size,
      'preview_basis':[960,640],'license':'CC0','author':'Rakoon','regions':{}}
for name,box in regions.items():
    native=tuple(round(v*im.width/960) for v in box)
    crop=im.crop(native); crop.thumbnail((960,960)); crop.save(out/(name+'.png'))
    meta['regions'][name]={'native_box':native,'output_size':crop.size}
    boxes=({'grey_chamfer':(95,150,124,440),'ochre_face':(160,150,220,440)} if name=='front_piers'
           else {'ochre_face':(120,130,155,415)} if name=='mid_pier' else {})
    if boxes:
        pixels=np.asarray(crop)
        roi_stats={}
        for label,(x0,y0,x1,y1) in boxes.items():
            a=pixels[y0:y1,x0:x1]
            y=a@np.array([.2126,.7152,.0722])
            roi_stats[label]={'box_in_crop':[x0,y0,x1,y1],
                'RGB_p50':np.median(a,axis=(0,1)).tolist(),'Y_p50':float(np.median(y)),
                'Y_std':float(y.std()),'note':'sRGB photo pixels, not reflectance; different face orientations'}
        meta[name+'_ROIs']=roi_stats
(out/'source.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
print(meta['source_size'])
for key,value in meta.items():
    if key.endswith('_ROIs'): print(key,value)
