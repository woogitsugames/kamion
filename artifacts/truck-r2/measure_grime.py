"""Matched display-space dirt controls; ROI differences are not physical dirt coverage."""
from pathlib import Path
import argparse
import csv
import json
from contextlib import ExitStack
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--prefix', default='dirt-before')
parser.add_argument('--rois', type=Path, default=ROOT / 'grime-rois.json')
args = parser.parse_args()
config = json.loads(args.rois.read_text(encoding='utf-8-sig'))
expected_size = tuple(config['native_size'])
conditions = ('Low-overcast', 'Low-clear', 'High-overcast', 'High-clear')
cases = ('washed', 'fleet', 'dirty')
rows = []
for case in cases:
    if not (ROOT / f'{args.prefix}-{case}' / 'complete.ok').exists():
        raise RuntimeError(f'Incomplete control: {case}')

def stats(picture, box):
    if picture.size != expected_size:
        raise ValueError('Unexpected frame dimensions')
    values = np.asarray(picture.crop(box).convert('RGB'), dtype=np.float32)
    y = values @ np.array((.2126, .7152, .0722), dtype=np.float32) / 255 * 100
    return {'mean_display_y': float(y.mean()), 'median_display_y': float(np.median(y)),
            'sigma_display_points': float(y.std()),
            'p90_minus_p10_points': float(np.percentile(y, 90)-np.percentile(y, 10)),
            'mean_r': float(values[..., 0].mean()), 'mean_g': float(values[..., 1].mean()),
            'mean_b': float(values[..., 2].mean())}

for condition in conditions:
    for camera, regions in config['cameras'].items():
        with ExitStack() as stack:
            pictures = {case: stack.enter_context(Image.open(ROOT / f'{args.prefix}-{case}' / condition / f'{camera}.png')) for case in cases}
            for name, box in regions.items():
                if len(box) != 4 or not (0 <= box[0] < box[2] <= expected_size[0] and 0 <= box[1] < box[3] <= expected_size[1]):
                    raise ValueError(f'Invalid ROI: {camera} {name}')
                row = {'condition': condition, 'camera': camera, 'region': name}
                data = {case: stats(pictures[case], tuple(box)) for case in cases}
                for case in cases:
                    row.update({f'{case}_{key}': value for key, value in data[case].items()})
                clean = data['washed']['mean_display_y']
                row['fleet_minus_washed_display_points'] = data['fleet']['mean_display_y'] - clean
                row['dirty_minus_washed_display_points'] = data['dirty']['mean_display_y'] - clean
                rows.append(row)

with (ROOT / f'{args.prefix}-roi-metrics.csv').open('w', newline='', encoding='utf-8-sig') as file:
    writer = csv.DictWriter(file, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
(ROOT / f'{args.prefix}-roi-metrics.json').write_text(json.dumps({
    'note': 'Luma Rec.709 of displayed sRGB bytes, percent scale; matched controls only. Not radiance or material coverage. ROI selection must be visually verified on the current baseline.',
    'roi_config': config, 'rows': rows,
}, indent=2, ensure_ascii=False), encoding='utf8')
font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 15)
for camera, regions in config['cameras'].items():
    path = ROOT / f'{args.prefix}-fleet' / 'High-overcast' / f'{camera}.png'
    with Image.open(path) as original:
        preview = original.convert('RGB')
    preview.thumbnail((960, 960), Image.Resampling.LANCZOS)
    scale = preview.width / expected_size[0]
    sheet = Image.new('RGB', (960, preview.height + 85), '#202020')
    sheet.paste(preview, (0, 0))
    draw = ImageDraw.Draw(sheet)
    for index, (name, box) in enumerate(regions.items()):
        bounds = tuple(round(v * scale) for v in box)
        draw.rectangle(bounds, outline='magenta', width=2)
        draw.text(bounds[:2], str(index + 1), font=font, fill='magenta')
        draw.text(((index % 3) * 320 + 8, preview.height + (index // 3) * 24 + 8), f'{index + 1}: {name}', font=font, fill='white')
    sheet.save(ROOT / f'{args.prefix}-roi-{camera}.jpg', quality=94)
print(f'Measured {len(rows)} matched condition/camera/region rows; no physical coverage claim.')
