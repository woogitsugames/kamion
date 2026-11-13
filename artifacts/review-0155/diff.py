import sys,os,json
from PIL import Image, ImageChops
import numpy as np
res={}
for tier in ('Low','High'):
    a=f'after/{tier}-clear'; b=f'before/{tier}-clear'; rows=[]
    for f in sorted(os.listdir(a)):
        if not f.endswith('.png') or not os.path.exists(os.path.join(b,f)): continue
        A=np.asarray(Image.open(os.path.join(a,f)).convert('RGB'),dtype=np.int16)
        B=np.asarray(Image.open(os.path.join(b,f)).convert('RGB'),dtype=np.int16)
        d=np.abs(A-B).max(axis=2)
        rows.append((f, float(d.mean()), float((d>24).mean()*100)))
    rows.sort(key=lambda r:-r[2])
    res[tier]=rows
    print(tier, len(rows), 'identical:', sum(1 for r in rows if r[1]==0))
    for r in rows[:15]: print('  %-45s MAE %.3f  px>24: %.3f%%'%r)
json.dump(res,open('image-diff.json','w'),indent=1)
