"""Project real generated 12m power poles into fixed route cameras; measure sky contrast.
No placement changes. Screen sampling can include wires: inspect annotated proof before using numbers.
"""
import json, math, sys, re
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
root=Path(__file__).resolve().parents[2]
phase=Path(sys.argv[1])
raw=root/'Data/raw/derived/bialystok-industrial-c/world'
poles=[i for p in raw.glob('instances*.json') for i in json.loads(p.read_text())['instances'] if i['p']=='power_pole' or i['p'].startswith('lamp_')]
cameras=json.loads((root/'Data/Regions/bialystok-industrial-c/generated/control_cameras.json').read_text())['cameras']
records=[]
out=phase/'pole-review';out.mkdir(exist_ok=True)
for c in cameras:
    name=c['id'].replace('_','-')
    if name not in ['g3a-rondo-bie-approach','photo-biezenstwa-ground','driver-andersa-to-putry','g3b-rondo-putry-approach','route-putry-approach']:
        continue
    path=phase/(name+'.png')
    if not path.exists():continue
    im=Image.open(path).convert('RGB');a=np.asarray(im,float);h,w=a.shape[:2]
    lum=a@np.array([.2126,.7152,.0722])
    pos=np.array(c['pos']);forward=np.array(c['look_at'])-pos;forward/=np.linalg.norm(forward)
    right=np.cross(forward,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,forward)
    f=h/(2*math.tan(math.radians(c['fov_deg']/2)))
    preview=im.resize((960,round(h*960/w)));draw=ImageDraw.Draw(preview);count=0
    for pole in poles:
        # Power pole accessor maxY12m; named lamp prototypes carry their metre height.
        height=12.0 if pole['p']=='power_pole' else float(re.search(r'_(\d+)m',pole['p']).group(1))
        point=np.array([pole['e'],pole['n'],pole['z']+height-.3]);v=point-pos;depth=float(v@forward)
        if not 300<depth<900:continue
        x=int(round(w/2+f*(v@right)/depth));y=int(round(h/2-f*(v@up)/depth))
        if not 10<x<w-10 or not 10<y<h*.6:continue
        patch=lum[y-8:y+9,x-8:x+9];ring=patch.copy();ring[5:12,5:12]=np.nan
        sky=float(np.nanmedian(ring))
        if sky<170:continue
        ink=float(lum[y-3:y+4,x-3:x+4].min());count+=1
        records.append({'camera':name,'prototype':pole['p'],'source':pole['src'],'e':pole['e'],'n':pole['n'],'depth_m':round(depth,1),'xy_original_px':[x,y],
                        'sky_srgb_luma':round(sky,2),'ink_srgb_luma':round(ink,2),'contrast_to_sky':round((sky-ink)/max(sky,1),4)})
        px,py=x*960/w,y*960/w;draw.ellipse((px-3,py-3,px+3,py+3),outline='red');draw.text((px+4,py+2),str(round(depth)),fill='red')
    if count:preview.save(out/(name+'.jpg'),quality=96)
(out/'far-poles.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
print(json.dumps(records,indent=2))
