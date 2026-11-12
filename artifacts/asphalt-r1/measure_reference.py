"""Local photo measurements. Boxes are authored on a 960px-wide preview, not physical albedo."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent
photo = Image.open('Data/raw/mapillary/bialystok-industrial-c/150280503737744.jpg').convert('RGB')
photo.thumbnail((960, 960))
a = np.asarray(photo, dtype=float)
luma = a @ np.array([0.2126, 0.7152, 0.0722])
boxes = {'left_wheel': [320,350,335,370], 'between_wheels': [375,350,390,370],
         'right_wheel': [430,350,445,370]}
stats = {}
draw = ImageDraw.Draw(photo)
for key, (x0,y0,x1,y1) in boxes.items():
    v = luma[y0:y1,x0:x1]
    stats[key] = dict(box_preview_px=boxes[key], median_srgb_luma=float(np.median(v)),
                      mean_srgb_luma=float(v.mean()), std_srgb_luma=float(v.std()), pixels=v.size)
    draw.rectangle(boxes[key], outline='red', width=1)
middle = stats['between_wheels']['median_srgb_luma']
for k in ('left_wheel', 'right_wheel'):
    stats[k]['ratio_to_between_wheels'] = stats[k]['median_srgb_luma'] / middle
    stats[k]['delta_to_between_wheels'] = stats[k]['median_srgb_luma'] - middle
result = dict(source='Mapillary 150280503737744', author='picturehoover', license='CC BY-SA 4.0',
              captured_at='2020-06-27', note='Display luma in one photograph. Exposure, wear placement and view are not a physical albedo measurement. WORKING_VALUE target for matched-render tuning; other photos may differ.',
              preview_size=photo.size, measurements=stats)
(OUT/'reference-wheel-contrast.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
photo.save(OUT/'references'/'wheel-contrast-boxes.jpg')
print(json.dumps(result, indent=2))
