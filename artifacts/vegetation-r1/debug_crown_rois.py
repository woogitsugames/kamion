from pathlib import Path
import sys
import numpy as np
from PIL import Image,ImageDraw
sys.path.insert(0,'tools/worldgen')
from streetscape.vegetation_metrics import foliage_mask,ROIS
root=Path('artifacts/vegetation-r1')
for tier in ('Low','High'):
 im=Image.open(root/'before'/f'{tier}-overcast'/'route-putry-approach.png').convert('RGB'); im.thumbnail((960,960))
 a=np.array(im); h,w=a.shape[:2]; r=ROIS['route-putry-approach'][0]; x0,y0,x1,y1=[round(v*s) for v,s in zip(r,(w,h,w,h))]
 sel=foliage_mask(a[y0:y1,x0:x1]); crop=a[y0:y1,x0:x1].copy(); crop[sel]=(crop[sel].astype(float)*.35+np.array([255,0,255])*.65).astype('uint8'); a[y0:y1,x0:x1]=crop
 out=Image.fromarray(a); ImageDraw.Draw(out).rectangle((x0,y0,x1,y1),outline='yellow',width=2); out.save(root/'baseline-focus'/f'putry-crown-mask-{tier}.jpg',quality=94)
