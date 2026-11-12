"""Small two-PNG ROI check, single thread; no full-matrix batch or map conversion."""
import argparse, hashlib, json, time
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageStat
parser = argparse.ArgumentParser()
parser.add_argument('--stage', default='result-0112-legend2x')
parser.add_argument('--label', default='512 candidate')
parser.add_argument('--tag', default='legend2x')
options = parser.parse_args()
if '/' in options.tag or '\\' in options.tag or '..' in options.tag:
    raise ValueError('tag must be a filename stem')
start = time.perf_counter()
root = Path(__file__).resolve().parent
roi = (440, 840, 680, 1040)
images = []
for stage in ('baseline', options.stage):
    with Image.open(root/stage/'Low-overcast/cab-dash.png') as im:
        images.append(im.convert('RGB').crop(roi))
diff = ImageChops.difference(*images)
changed = sum(1 for p in diff.getdata() if p != (0, 0, 0))
sheet = Image.new('RGB', (960, 440), '#dddddd')
draw = ImageDraw.Draw(sheet)
font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 17)
for col, im in enumerate(images):
    draw.text((col*480+8, 6), ('256 baseline' if col == 0 else options.label)+' — nearest 2x', fill='black', font=font)
    sheet.paste(im.resize((480, 400), Image.Resampling.NEAREST), (col*480, 32))
sheet.save(root/(options.tag+'-Low-overcast-left-ROI-960.png'))
record = {'scope': 'Only one 240x200 native ROI from two Low-overcast captures; not full-frame photometry',
          'roi': roi, 'changed_pixels': changed, 'pixels': images[0].width*images[0].height,
          'max_channel_delta': max(v[1] for v in diff.getextrema()), 'mean_channel_delta': ImageStat.Stat(diff).mean,
          'crop_sha256': [hashlib.sha256(im.tobytes()).hexdigest() for im in images],
          'elapsed_seconds': time.perf_counter()-start}
(root/(options.tag+'-roi-check.json')).write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps(record, indent=2))

