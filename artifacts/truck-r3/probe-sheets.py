"""Make labelled 960 px previews of actual diagnostic output; no color edits."""
from pathlib import Path
import sys
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parent
stage = sys.argv[1]
if not (root/stage/'complete.ok').is_file():
    raise ValueError('Probe not complete')
out = root/'probe-previews'
out.mkdir(exist_ok=True)
for condition in ('Low-overcast','High-overcast'):
    for camera in ('truck-wheel-detail','truck-mudguard-detail'):
        with Image.open(root/stage/condition/f'{camera}.png') as original:
            pic = original.convert('RGB')
            pic.thumbnail((960,900),Image.Resampling.LANCZOS)
        sheet = Image.new('RGB',(960,pic.height+36),(24,24,24))
        ImageDraw.Draw(sheet).text((8,10),f'DEBUG {stage} | {condition} | {camera} | nie koncowy render',fill='white')
        sheet.paste(pic,((960-pic.width)//2,36))
        sheet.save(out/f'{stage}-{condition}-{camera}.jpg',quality=94)
print(out)
