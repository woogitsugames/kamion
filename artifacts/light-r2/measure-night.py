"""Night exposure ablation: original PNG photometry and complete review sheets.
Fixed ROIs are diagnostics, not segmentation or a physical lux measurement.
"""
import os
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[key] = '1'
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent
GROUND = {
    'driver-andersa-to-putry': (.45, .62, .65, .93),
    'cab-dash': (.15, .03, .50, .22),
    'r10_hall_3': (.10, .80, .90, .95),
    'r10_block_3': (.20, .76, .65, .93),
    'r10_house_2': (.10, .75, .60, .95),
    'stretch-05-docks': (.15, .70, .85, .95),
}
LABELS = ('dusk', 'bias-2', 'bias-3', 'bias-4', 'bias-5')
results = {}

def stats(rgb):
    a = np.asarray(rgb, dtype=np.float32)
    y = a @ np.array([.2126, .7152, .0722], dtype=np.float32)
    return dict(rgb_mean=a.mean(axis=(0, 1)).round(4).tolist(),
                luma_mean=float(y.mean()), luma_p05_p50_p95=np.percentile(y, [5, 50, 95]).tolist(),
                luma_below_3pct_fraction=float((y < 7.65).mean()),
                any_channel_ge250_fraction=float((a.max(axis=2) >= 250).mean()))

for tier in ('Low', 'High'):
    results[tier] = {}
    for camera, ground in GROUND.items():
        sheet = Image.new('RGB', (960, 735), '#202020')
        draw = ImageDraw.Draw(sheet)
        results[tier][camera] = {}
        for index, label in enumerate(LABELS):
            folder = OUT/'fresh-dusk'/tier if label == 'dusk' else OUT/'night-ablation'/f'{tier}-{label}'
            probes = json.loads((folder/'lamp-probes.json').read_text())['cameras']
            probe = next(p for p in probes if p['camera'] == camera)
            if probe['lampsOn'] != 1 or probe['pools'] != (4 if tier == 'Low' else 8):
                raise ValueError(f'Unexpected lamp state: {tier}/{camera}/{label}')
            if label != 'dusk' and probe['sunElevation'] != -8:
                raise ValueError('Night was not applied')
            with Image.open(folder/(camera+'.png')) as source:
                im = source.convert('RGB')
            rect = tuple(round(v*(im.width if i%2 == 0 else im.height)) for i, v in enumerate(ground))
            record = dict(frame=stats(im), ground_roi_native=rect, ground=stats(im.crop(rect)),
                          model=probe)
            if camera == 'r10_block_3':
                record['sky_roi_native'] = [350, 40, 530, 130]
                record['sky'] = stats(im.crop((350, 40, 530, 130)))
            if camera == 'cab-dash':
                # Broad steering wheel/instrument area; visual inspection must confirm actual gauge readability.
                instrument = tuple(round(v*(im.width if i%2 == 0 else im.height)) for i, v in enumerate((.48, .48, .62, .64)))
                record['instrument_roi_native'] = instrument
                record['instrument_diagnostic'] = stats(im.crop(instrument))
            results[tier][camera][label] = record
            thumb = im.copy(); thumb.thumbnail((476, 220))
            x, y = index%2*480, index//2*245
            sheet.paste(thumb, (x+2, y+23))
            draw.text((x+5, y+5), tier+' / '+label+' / '+camera, fill='white')
        sheet.save(OUT/f'night-{tier}-{camera}.jpg', quality=95)
(OUT/'night-ablation-metrics.json').write_text(json.dumps(dict(
    method='native PNG Rec709 sRGB luminance; frame and fixed manually authored ROI diagnostics; no gate thresholds inferred',
    scope='Dusk vs Night exposure candidates; identical scene/tier/camera, no physical sky fit or device/GPU claim',
    results=results), indent=2), encoding='utf-8')
for tier, cameras in results.items():
    for label, values in cameras['r10_block_3'].items():
        print(tier, label, 'sky luma', round(values['sky']['luma_mean'], 2),
              'ground p50/p95', [round(v, 2) for v in values['ground']['luma_p05_p50_p95'][1:]])
