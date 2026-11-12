"""Actual dusk pool on/off A/B. Native PNGs, fixed ground ROIs, 41px-scale smoothing.
These are image contrast measurements, not lux measurements or device timings.
"""
import os
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[key] = '1'
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parent
ROIS = {
    'driver-andersa-to-putry': (.45, .62, .65, .93),
    'cab-dash': (.15, .03, .50, .22),
    'r10_hall_3': (.10, .80, .90, .95),
    'r10_block_3': (.20, .76, .65, .93),
    'r10_house_2': (.10, .75, .60, .95),
    'stretch-05-docks': (.15, .70, .85, .95),
}
results = {}
for tier in ('Low', 'High'):
    results[tier] = {}
    sheet = Image.new('RGB', (960, len(ROIS)*175), '#202020')
    draw = ImageDraw.Draw(sheet)
    for row, (camera, roi) in enumerate(ROIS.items()):
        images = []
        arrays = []
        smoothed = []
        for state in ('off', 'on'):
            with Image.open(OUT/'baseline'/f'{tier}-{state}'/(camera+'.png')) as source:
                im = source.convert('RGB')
            images.append(im)
            arrays.append(np.asarray(im, dtype=np.int16))
            smoothed.append(np.asarray(im.convert('L').filter(ImageFilter.GaussianBlur(20)), dtype=float))
        rect = tuple(round(v*(images[0].width if i%2 == 0 else images[0].height)) for i, v in enumerate(roi))
        x0, y0, x1, y1 = rect
        off, on = (a[y0:y1, x0:x1] for a in smoothed)
        eligible = (off >= 15) & (off < 180)
        if not eligible.any():
            raise ValueError('Empty valid ground ROI: '+camera)
        ratios = (on[eligible]+0.5)/(off[eligible]+0.5)
        difference = arrays[1]-arrays[0]
        results[tier][camera] = dict(roi_native=rect, roi_normalized=roi,
            eligible_fraction=float(eligible.mean()), median_ratio=float(np.median(ratios)),
            p95_ratio=float(np.percentile(ratios, 95)), max_ratio=float(ratios.max()),
            frame_positive_change_gt1_fraction=float((difference.max(axis=2)>1).mean()),
            frame_negative_change_ltminus1_fraction=float((difference.min(axis=2)<-1).mean()))
        diagnostic = Image.fromarray(np.uint8(np.clip(np.maximum(difference, 0)*6, 0, 255)))
        for col, (im, label) in enumerate(zip(images+[diagnostic], ('pools OFF', 'pools ON', 'positive difference x6'))):
            thumb = im.copy(); thumb.thumbnail((316, 145))
            sheet.paste(thumb, (col*320, row*175+25))
            draw.text((col*320+3, row*175+5), camera+' / '+label, fill='white')
    sheet.save(OUT/f'dusk-baseline-{tier}.jpg', quality=95)
(OUT/'dusk-baseline-metrics.json').write_text(json.dumps(dict(
    method='original PNG L channel, Gaussian radius20 native px, fixed manually selected ground ROIs, off luma15..179, ratio (on+.5)/(off+.5); diagnostic difference x6 only',
    scope='pools only; High point lights and lens emission remain on in both states; hall3 ROI is grass, house2 paving',
    results=results), indent=2), encoding='utf-8')
for tier, cameras in results.items():
    for camera, values in cameras.items():
        print(tier, camera, 'p95 ratio', round(values['p95_ratio'], 3), 'max', round(values['max_ratio'], 3),
              'changed frame%', round(values['frame_positive_change_gt1_fraction']*100, 2))
