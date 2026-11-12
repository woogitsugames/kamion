"""Native PNG edge on a raycast/projection-verified 10 m wall segment.
No resampling for measurement. Report every column; no trimming or outlier removal.
Repeat with two derivative smoothing radii to expose the edge detector's sensitivity.
"""
import csv
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT/'shadow-metric-v2'
results = {}
for variant in ('legacy', 'policy'):
    folder = SOURCE/variant
    proof = json.loads((folder/'shadow-wall-10m.json').read_text())
    x0, x1 = sorted((proof['pixelStart']['x'], proof['pixelEnd']['x']))
    x0, x1 = int(np.ceil(x0)), int(np.floor(x1))
    if not (910 <= x0 < x1 <= 1930):
        raise ValueError(f'10 m span crosses door/downpipe diagnostic limits: {x0}, {x1}')
    with Image.open(folder/'r10_hall_3.png') as source:
        crop = source.convert('RGB').crop((x0-4, 540, x1+5, 616))
    row = dict(proof=proof, sampled_x=[x0, x1], smoothing={})
    for radius in (1.5, 2.5):
        a = np.asarray(crop.convert('L').filter(ImageFilter.GaussianBlur(radius)), dtype=float)
        # 5-column average suppresses fine wall grain, preserving the legacy ~50px wave.
        a = sum(a[:, i:i+(x1-x0+1)] for i in range(2, 7))/5
        gradient = (a[2:]-a[:-2])/2
        # Lower boundary of the bright band: reviewed window y555..600.
        low, high = 555-541, 600-541
        indices = np.argmin(gradient[low:high+1], axis=0)+low
        x = np.arange(x0, x1+1)
        columns = np.arange(len(x))
        g0, g1, g2 = gradient[indices-1, columns], gradient[indices, columns], gradient[indices+1, columns]
        denominator = g0-2*g1+g2
        offset = np.divide(0.5*(g0-g2), denominator, out=np.zeros_like(g1), where=np.abs(denominator)>1e-9)
        edge = 541+indices+np.clip(offset, -0.5, 0.5)
        fit = np.polyval(np.polyfit(x, edge, 1), x)
        residual = edge-fit
        record = dict(columns=len(x), max_absolute_deviation_px=float(np.max(np.abs(residual))),
                      rms_deviation_px=float(np.sqrt(np.mean(residual**2))),
                      strongest_gradient_range=[float(g1.min()), float(g1.max())],
                      edge_y_range=[float(edge.min()), float(edge.max())],
                      threshold_1px_met=bool(np.max(np.abs(residual)) <= 1),
                      excluded_columns=0)
        row['smoothing'][str(radius)] = record
        with (folder/f'edge-r{radius}.csv').open('w', newline='') as stream:
            writer = csv.writer(stream); writer.writerow(['x', 'edge_y', 'fit_y', 'residual_px'])
            writer.writerows(zip(x, edge, fit, residual))
        overlay = crop.copy(); draw = ImageDraw.Draw(overlay)
        draw.line([(float(xx-x0+4), float(yy-540)) for xx, yy in zip(x, edge)], fill='red', width=1)
        draw.line([(float(xx-x0+4), float(yy-540)) for xx, yy in zip(x, fit)], fill='cyan', width=1)
        overlay.thumbnail((960, 960))
        overlay.save(folder/f'edge-r{radius}.png')
    results[variant] = row
(ROOT/'shadow-10m-measurement.json').write_text(json.dumps(dict(
    method='native luminance derivative, Gaussian radius 1.5/2.5 px, 5-column average, subpixel quadratic minimum, ordinary least squares line, all columns retained',
    scope='static hall3 shadow edge only; no movement, other cameras or GPU/device claim', results=results), indent=2))
print(json.dumps({k: v['smoothing'] for k, v in results.items()}, indent=2))
