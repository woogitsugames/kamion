"""Native PNG diagnostics: fixed ROI comparisons, no lux or calibrated-photo claim."""
import os
for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[k] = '1'
import json
from pathlib import Path
import numpy as np
from PIL import Image
root = Path(__file__).resolve().parent
rois = {'driver-andersa-to-putry': (1053,670,1521,1004),
        'cab-dash': (1123,518,1451,691), 'r10_block_3': (468,821,1521,1004)}
result = []
for tier in ('Low', 'High'):
    for camera, roi in rois.items():
        with Image.open(root/'night-sky'/f'{tier}-ungraded'/(camera+'.png')) as src:
            before = np.array(src.convert('RGB').crop(roi), dtype=np.int16)
        for variant in ('dim-warm', 'dim-neutral', 'dark-neutral'):
            folder = root/'night-sky'/f'{tier}-{variant}'
            with Image.open(folder/(camera+'.png')) as src:
                after = np.array(src.convert('RGB').crop(roi), dtype=np.int16)
                sky = np.asarray(src.convert('RGB').crop((350,40,530,130)), dtype=np.float32)
            delta = np.abs(after-before)
            result.append(dict(tier=tier, camera=camera, variant=variant, roi=roi,
                mean_abs_rgb=float(delta.mean()), max_abs_rgb=int(delta.max()),
                fraction_pixels_changed=float(np.any(delta != 0, axis=2).mean()),
                sky_roi_luma_mean=float((sky @ np.array([.2126,.7152,.0722])).mean())
                if camera == 'r10_block_3' else None))
out = dict(method='Native RGB PNG, exact absolute channel difference in manually fixed foreground ROI. Sky ROI only block3; no physical photometry.', results=result)
(root/'sky-grade-metrics.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
for r in result:
    if r['variant'] == 'dim-neutral':
        print(r)
