"""All-camera overviews and native-pixel target crops for independent visual review."""
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw

root = Path(__file__).parent
metrics = json.loads((root/'image-metrics.json').read_text())
for condition in ('Low-clear','Low-overcast','High-clear','High-overcast'):
    rows = sorted((r for r in metrics if r['condition']==condition),key=lambda r:r['mae'],reverse=True)
    dest = root/'overviews'/condition
    dest.mkdir(parents=True,exist_ok=True)
    for start in range(0,len(rows),12):
        sheet = Image.new('RGB',(960,432),'white')
        draw = ImageDraw.Draw(sheet)
        draw.text((5,3), f'{condition}: kazda komorka = PRZED | PO',fill='black')
        for offset,row in enumerate(rows[start:start+12]):
            x,y = offset%3*320, offset//3*104+16
            draw.text((x+3,y+1), row['camera'][:48],fill='black')
            pair = Image.open(root/'pairs'/condition/f"{row['camera']}.jpg").crop((0,30,960,252))
            pair.thumbnail((320,84),Image.Resampling.LANCZOS)
            sheet.paste(pair,(x,y+19))
        sheet.save(dest/f'overview-{start//12:02d}.jpg',quality=90)

probe = root/'projection-probe.json'
if probe.exists():
    data = json.loads(probe.read_text())
    for row in data['rows']:
        for light in ('clear','overcast'):
            condition = f"{row['tier']}-{light}"
            x,y,w,h = row['projectedRectTopLeft']
            # Native model bounds, padded for anti-aliasing; no object isolation or pixel painting.
            if row['behindCamera'] or not all(math.isfinite(v) for v in (x,y,w,h)):
                x,y,w,h = 820,300,700,500
            padding = max(15,.1*max(w,h))
            x0,y0 = max(0,int(x-padding)),max(0,int(y-padding))
            x1,y1 = min(2340,int(x+w+padding)),min(1080,int(y+h+padding))
            if x1<=x0 or y1<=y0:
                continue
            a = Image.open(root/'before'/condition/f"{row['camera']}.png").crop((x0,y0,x1,y1)).convert('RGB')
            b = Image.open(root/'after'/condition/f"{row['camera']}.png").crop((x0,y0,x1,y1)).convert('RGB')
            a.thumbnail((480,340),Image.Resampling.LANCZOS); b.thumbnail((480,340),Image.Resampling.LANCZOS)
            sheet = Image.new('RGB',(960,370),'white')
            draw = ImageDraw.Draw(sheet)
            draw.text((5,5),f"{condition} {row['camera']} | native LOD {row['selectedLod']} | PRZED / PO",fill='black')
            sheet.paste(a,(0,30));sheet.paste(b,(480,30))
            dest = root/'target-crops'/condition
            dest.mkdir(parents=True,exist_ok=True)
            sheet.save(dest/f"{row['camera']}.jpg",quality=93)
print('All-camera overviews and available native target crops written.')
