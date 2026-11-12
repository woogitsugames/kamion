"""Small sequential image comparisons; displayed luminance, not physical photometry."""
import os
for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[name] = '1'
from pathlib import Path
import json
from PIL import Image, ImageDraw
import numpy as np

root = Path(__file__).resolve().parent
out = root / 'final-pairs'
out.mkdir(exist_ok=True)
rows = []
for source, target, cameras in (
    ('before', 'final', ['truck-34','truck-34r','truck-front','truck-side','truck-rear34','cab-driver','chase']),
    ('detail-before-fleet', 'detail-final-fleet', ['truck-step-detail','truck-mudguard-detail','truck-wheel-detail']),
):
    for tier in ('Low', 'High'):
        for light in ('overcast', 'clear'):
            condition = f'{tier}-{light}'
            for camera in cameras:
                with Image.open(root/source/condition/f'{camera}.png') as a, Image.open(root/target/condition/f'{camera}.png') as b:
                    if a.size != (2340,1080) or b.size != a.size:
                        raise ValueError('Unexpected dimensions')
                    sheet = Image.new('RGB',(960,256),(32,32,32))
                    draw = ImageDraw.Draw(sheet)
                    for x, pic, label in ((0,a,'PRZED'),(480,b,'PO')):
                        sheet.paste(pic.convert('RGB').resize((480,222),Image.Resampling.LANCZOS),(x,34))
                        draw.text((x+8,8),f'{label} | {condition}',fill='white')
                    sheet.save(out/f'{condition}-{camera}.jpg',quality=93)
                    if camera == 'truck-step-detail':
                        # Fixed tread patch; includes holes/shadows. No mask based on resulting brightness.
                        roi = (800,810,1080,855)
                        values = []
                        for pic in (a,b):
                            rgb = np.asarray(pic.convert('RGB').crop(roi),dtype=np.float32)
                            y = rgb @ np.array([.2126,.7152,.0722],dtype=np.float32)/255*100
                            values.append({'mean_display_y':float(y.mean()),'sigma_display_points':float(y.std())})
                        rows.append({'condition':condition,'roi':roi,'before':values[0],'after':values[1]})
(root/'final-step-roi.json').write_text(json.dumps({'note':'Display Rec709 Y in percentage points, fixed native ROI including shadows; no physical dirt coverage or phone performance claim.','rows':rows},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'pairs':len(list(out.glob('*.jpg'))),'step_roi':rows},ensure_ascii=False))
