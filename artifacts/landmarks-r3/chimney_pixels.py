"""Fixed photographic pixel windows, no physical-albedo or survey claims."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

root=Path(__file__).resolve().parent
phase=sys.argv[1]
fit=json.loads((root/'photo-pose-fit.json').read_text())
source=root.parents[1]/fit['source']
photo=np.asarray(Image.open(source).convert('RGB'))
windows=[dict(name='multi',ranges=[(420,475),(505,545),(590,635),(675,725)],
              red=(505,545),white=(590,635)),
         dict(name='single',ranges=[(165,240),(280,330),(445,465),(500,555)],
              red=(280,330),white=(445,465))]

def extract(image,index,ranges):
    obs=fit['observed'][index]
    pixels=[]
    for a,b in ranges:
        for y in range(a,b):
            x=round(obs['intercept']+obs['slope']*y)
            pixels.append(np.median(image[y,x-3:x+4],axis=0))
    return np.array(pixels)

def red_mask(p):
    # Dirty cream paint is not red: the photograph's white often has R-G12.
    return (p[:,0]-p[:,1]>25)&(p[:,0]-p[:,2]>25)&(p[:,2]-p[:,1]>-8)

rows=[]
for condition in ['Low-overcast','Low-clear','High-overcast','High-clear']:
    path=root/phase/condition/'ec-ref073128.png'
    if not path.exists(): continue
    with Image.open(path) as opened:
        # Same full-height angular comparison used by photo_pair.py.
        render=np.asarray(opened.convert('RGB').crop((210,0,2130,1080)).resize((3840,2160)))
    for index,w in enumerate(windows):
        p=extract(photo,index,w['ranges']); q=extract(render,index,w['ranges'])
        pr,qr=red_mask(p),red_mask(q)
        item=dict(condition=condition,stack=w['name'],sampled_rows=len(p),
                  red_white_disagreement_fraction=float((pr!=qr).mean()),
                  photo_red_rows=int(pr.sum()),render_red_rows=int(qr.sum()))
        for label in ['red','white']:
            pp=extract(photo,index,[w[label]]); qq=extract(render,index,[w[label]])
            item[label+'_photo_median_rgb']=np.median(pp,axis=0).tolist()
            item[label+'_render_median_rgb']=np.median(qq,axis=0).tolist()
        rows.append(item)
result=dict(phase=phase,status='Measured sRGB red/non-red classification at fixed photo-centreline windows; pose WORKING_VALUE, not physical reflectance',
            red_threshold='R-G>25, R-B>25, B-G>-8 (exclude ochre/brown dirt); non-red is not proof of a white material',
            excluded='Head/galleries and occluded shaft base are outside the row windows',
            windows=windows,rows=rows)
(root/f'chimney-pixels-{phase}.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(rows[:2],indent=2))
