"""Compare fixed native ROIs and make 960 px before/after sheets."""
from pathlib import Path
import json
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parent
stage = sys.argv[1]
config = json.loads((root / 'grime-rois.json').read_text(encoding='utf-8-sig'))
font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 16)
rows = []
for condition in sorted((root / stage).iterdir()):
    if not condition.is_dir() or not (condition / 'complete.ok').exists():
        continue
    for camera, regions in config['cameras'].items():
        if not (condition / f'{camera}.png').exists():
            continue
        with Image.open(root / 'before' / condition.name / f'{camera}.png') as old_file, Image.open(condition / f'{camera}.png') as new_file:
            old, new = old_file.convert('RGB'), new_file.convert('RGB')
        if old.size != tuple(config['native_size']) or new.size != old.size:
            raise ValueError('Mismatched dimensions')
        for name, box in regions.items():
            values = []
            for picture in (old, new):
                rgb = np.asarray(picture.crop(box), dtype=np.float32)
                y = rgb @ np.array((.2126, .7152, .0722), dtype=np.float32) / 255 * 100
                values.append({'mean_display_y': float(y.mean()), 'sigma_display_points': float(y.std())})
            rows.append({'condition': condition.name, 'camera': camera, 'region': name,
                         'before': values[0], 'after': values[1],
                         'mean_delta_points': values[1]['mean_display_y']-values[0]['mean_display_y']})
        for label, box in (('whole', None), ('curtain', (1100, 135, 2340, 620))):
            pictures = [image.crop(box) if box else image for image in (old, new)]
            height = round(pictures[0].height * 480 / pictures[0].width)
            sheet = Image.new('RGB', (960, height+34), '#202020')
            draw = ImageDraw.Draw(sheet)
            for index, picture in enumerate(pictures):
                sheet.paste(picture.resize((480, height), Image.Resampling.LANCZOS), (index*480, 34))
                draw.text((index*480+8, 8), ('PRZED' if index == 0 else 'PO')+' | '+condition.name, font=font, fill='white')
            sheet.save(condition / f'review-{camera}-{label}.jpg', quality=94)
(root / f'{stage}-roi-delta.json').write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding='utf8')
print(f'Compared {len(rows)} native ROI rows; sheets width 960 px.')
