"""Native ray-selected visible rear paint, excluding trim/plate/other vehicles."""
from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'artifacts/car-paint-r1'
namespace={'__file__':str(ART/'r4-body-profile.py')}
exec(compile((ART/'r4-body-profile.py').read_text().split('probes={}')[0],str(ART/'r4-body-profile.py'),'exec'),namespace)
cast=namespace['caster']('r4_rear_target_3',ART/'r4-rear-controls-v2/High-overcast/off/poses/r4_rear_target_3-begin.json')
model=namespace['model']
points=[]
for y in range(360,801,20):
    for x in range(960,1701,20):
        hit=cast(x,y)
        if hit is None or hit['instance']!=895 or not hit['material'].startswith('M_car_paint_'):continue
        if hit['native_uv0'][0]>-1.9:continue # Rear surface, not the side.
        points.append(dict(pixel=[x,y],hit=hit))
assert points,'No visible rear paint'
low=[p for p in points if p['hit']['height_m']<.65]
assert low,'No lower rear paint'
out=dict(method='Actual native LOD0 CPU ray/material selection in the supplemental frame; 5x5 native-pixel means, no image alignment',
    target='car_hatch_black actualGPUlevel3/nativeIndex8908',paint_samples=len(points),lower_samples=len(low),
    visible_rear_paint_height_m=[min(p['hit']['height_m'] for p in points),max(p['hit']['height_m'] for p in points)],
    lower_paint_height_m=[min(p['hit']['height_m'] for p in low),max(p['hit']['height_m'] for p in low)],
    note='Paint-only, excludes trim/plate. Geometry may have no rear paint at sill height .19; does not claim dirt on plastic.',conditions=[],points=points)
for condition in ('Low-clear','Low-overcast','High-clear','High-overcast'):
    values=[]
    for mode in ('off','level0','level1','level2','level3'):
        image=np.asarray(Image.open(ART/'r4-rear-controls-v2'/condition/mode/'r4_rear_target_3.png').convert('RGB'),float)
        samples=[]
        for p in low:
            x,y=p['pixel'];box=image[y-2:y+3,x-2:x+3];samples.append((box@np.array([.2126,.7152,.0722])).mean())
        values.append(dict(mode=mode,lower_paint_luma_mean=float(np.mean(samples)),lower_paint_luma_range=[float(np.min(samples)),float(np.max(samples))]))
    out['conditions'].append(dict(condition=condition,values=values))
    canvas=Image.new('RGB',(960,430),'#222');draw=ImageDraw.Draw(canvas)
    for j,mode in enumerate(('off','level3')):
        im=Image.open(ART/'r4-rear-controls-v2'/condition/mode/'r4_rear_target_3.png').convert('RGB')
        im=im.crop((960,340,1680,940)).resize((480,400),Image.Resampling.LANCZOS)
        canvas.paste(im,(j*480,25));draw.text((j*480+4,5),f'{condition} same-frame {mode}',fill='white')
    (ART/'r4-rear-review-v2').mkdir(exist_ok=True)
    canvas.save(ART/'r4-rear-review-v2'/f'{condition}-native-rear.jpg',quality=94)
for p in low:
    h,u=p['hit']['native_payload'];upper=p['hit']['keep_upper']
    p['expected_opacities']=[float(model.opacity(h,model.longitudinal_weight(u),level)*(1-upper)) for level in range(4)]
(ART/'r4-rear-paint-metrics.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='points'}))
