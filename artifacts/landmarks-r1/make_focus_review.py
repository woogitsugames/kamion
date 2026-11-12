from pathlib import Path
from PIL import Image, ImageDraw
import sys

ROOT=Path(__file__).resolve().parent
phase=sys.argv[1]
out=ROOT/'review'/phase
out.mkdir(parents=True,exist_ok=True)
ids=('fire-station-ref7197','fire-station-route','fire-station-abeam','fire-station-above')
for condition in ('Low-overcast','Low-clear','High-overcast','High-clear'):
    sheet=Image.new('RGB',(960,984),(24,24,24))
    for row,name in enumerate(ids):
        for col,stage in enumerate(('before',phase)):
            image=Image.open(ROOT/stage/condition/(name+'.png')).convert('RGB')
            image.thumbnail((480,222))
            x,y=col*480,row*246
            sheet.paste(image,(x,y+24))
            ImageDraw.Draw(sheet).text((x+6,y+6),f'{stage} {condition} {name}',fill='white')
    sheet.save(out/(condition+'.jpg'),quality=95)
    # Match the region around the gable rather than pretending the full sensor
    # aspect ratios of the 3:2 photo and wide QA camera are identical.
    ref=Image.open(ROOT/'reference7197.jpg').convert('RGB')
    ref=ref.crop((1120,1000,2960,2140)); ref.thumbnail((480,320))
    render=Image.open(ROOT/phase/condition/'fire-station-ref7197.png').convert('RGB')
    scale=render.width/960
    render=render.crop(tuple(round(v*scale) for v in (355,130,685,335)))
    render.thumbnail((480,320))
    pair=Image.new('RGB',(960,344),(24,24,24))
    pair.paste(ref,(0,24)); pair.paste(render,(480,24))
    draw=ImageDraw.Draw(pair)
    draw.text((6,6),'Commons 7197 Rakoon CC0 - gable crop',fill='white')
    draw.text((486,6),f'{phase} {condition} - gable crop',fill='white')
    pair.save(out/(condition+'-photo.jpg'),quality=95)
print(out)
