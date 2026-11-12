"""Fixed-frame 960 px evidence of wheel changes on the same regenerated world."""
from pathlib import Path
import json
import sys
from PIL import Image, ImageDraw

root=Path(__file__).resolve().parent
stage=sys.argv[1]
if not stage.replace('-','').isalnum():
    raise ValueError('Invalid stage')
out=root/(stage+'-pairs')
out.mkdir(exist_ok=True)
rows=[]
for tier in ('Low','High'):
    for lighting in ('overcast','clear'):
        condition=f'{tier}-{lighting}'
        for camera in ('truck-wheel-detail','truck-mudguard-detail','truck-step-detail'):
            before=root/'detail-before-fleet'/condition/f'{camera}.png'
            after=root/stage/condition/f'{camera}.png'
            if not before.exists() or not after.exists():
                raise ValueError(f'Missing actual frame: {condition} {camera}')
            sheet=Image.new('RGB',(960,256),(24,24,24))
            draw=ImageDraw.Draw(sheet)
            for x,path,label in ((0,before,'PRZED'),(480,after,'KANDYDAT')):
                with Image.open(path) as image:
                    if image.size!=(2340,1080):
                        raise ValueError('Changed native resolution')
                    sheet.paste(image.convert('RGB').resize((480,222),Image.Resampling.LANCZOS),(x,34))
                draw.text((x+8,9),f'{label} | {condition}',fill='white')
            name=f'{condition}-{camera}.jpg'
            sheet.save(out/name,quality=94)
            rows.append({'condition':condition,'camera':camera,'before':str(before),'after':str(after),'pair':name})
(out/'index.json').write_text(json.dumps({'note':'Same fixed QA cameras, native resolution and regenerated world. Appearance requires visual review; no automatic PASS.','rows':rows},ensure_ascii=False,indent=2),encoding='utf8')
print(out)
