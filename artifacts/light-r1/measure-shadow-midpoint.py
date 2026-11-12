"""Second, float-only shadow-edge detector; retain the initial derivative result.

The derivative minimum in the soft PCF transition is not a stable edge (wall grain
and 8-bit blur plateaus compete). Detect the local half-contrast crossing instead,
with independent bright/dark samples referenced to the raycast horizontal line.
No discarded columns; Gaussian sensitivity 1.5/2.5 native pixels.
"""
import csv
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent
results = {}
for variant in ('legacy', 'policy'):
    folder = OUT/'shadow-metric-v2'/variant
    proof = json.loads((folder/'shadow-wall-10m.json').read_text())
    ends = sorted((proof['pixelStart'], proof['pixelEnd']), key=lambda p: p['x'])
    x0, x1 = int(np.ceil(ends[0]['x'])), int(np.floor(ends[1]['x']))
    x = np.arange(x0, x1+1)
    base = np.interp(x, [p['x'] for p in ends], [p['y'] for p in ends])
    with Image.open(folder/'r10_hall_3.png') as im:
        rgb = im.convert('RGB').crop((x0-12, 530, x1+13, 630))
    luminance = np.asarray(rgb, dtype=float) @ np.array([0.2126, 0.7152, 0.0722])
    row = dict(proof=proof, sampled_x=[x0, x1], smoothing={})
    for sigma in (1.5, 2.5):
        radius = int(np.ceil(3*sigma))
        positions = np.arange(-radius, radius+1)
        kernel = np.exp(-positions**2/(2*sigma**2)); kernel /= kernel.sum()
        a = np.apply_along_axis(lambda v: np.convolve(np.pad(v, radius, mode='reflect'), kernel, mode='valid'), 0, luminance)
        a = np.apply_along_axis(lambda v: np.convolve(np.pad(v, radius, mode='reflect'), kernel, mode='valid'), 1, a)
        a = sum(a[:, i:i+len(x)] for i in range(10, 15))/5
        edges, contrasts = [], []
        for column, yref in enumerate(base):
            y = int(round(yref))-530
            bright, dark = a[y-3:y+5, column].mean(), a[y+35:y+49, column].mean()
            contrasts.append(bright-dark)
            if bright-dark < 25:
                raise ValueError(f'Insufficient edge contrast: {variant}/{column}')
            midpoint = (bright+dark)/2
            profile = a[:, column]
            crossings = np.where((profile[:-1] >= midpoint) & (profile[1:] < midpoint))[0]
            crossings = [i for i in crossings if y+4 <= i <= y+32]
            if not crossings:
                raise ValueError(f'No half-contrast crossing: {variant}/{column}')
            index = min(crossings, key=lambda i: abs(i-(y+14)))
            edge = index+(profile[index]-midpoint)/(profile[index]-profile[index+1])
            edges.append(edge+530)
        edges = np.asarray(edges)
        fit = np.polyval(np.polyfit(x, edges, 1), x)
        residual = edges-fit
        row['smoothing'][str(sigma)] = dict(columns=len(x), excluded_columns=0,
            max_absolute_deviation_px=float(np.max(np.abs(residual))),
            rms_deviation_px=float(np.sqrt(np.mean(residual**2))),
            min_bright_dark_contrast=float(min(contrasts)),
            threshold_1px_met=bool(np.max(np.abs(residual)) <= 1))
        with (folder/f'edge-midpoint-r{sigma}.csv').open('w', newline='') as stream:
            writer = csv.writer(stream); writer.writerow(['x', 'edge_y', 'fit_y', 'residual_px'])
            writer.writerows(zip(x, edges, fit, residual))
        overlay = rgb.copy(); draw = ImageDraw.Draw(overlay)
        draw.line([(float(xx-x0+12), float(yy-530)) for xx, yy in zip(x, edges)], fill='red', width=1)
        draw.line([(float(xx-x0+12), float(yy-530)) for xx, yy in zip(x, fit)], fill='cyan', width=1)
        overlay.thumbnail((960, 960)); overlay.save(folder/f'edge-midpoint-r{sigma}.png')
    results[variant] = row
(OUT/'shadow-10m-midpoint.json').write_text(json.dumps(dict(
    method='float Rec709 sRGB luma; Gaussian sigma1.5/2.5, 5-column average, per-column local half-contrast crossing; OLS line; no excluded columns',
    limitation='static hall3 luminance boundary, not GPU shadow geometry; material variation and detector sensitivity remain',
    results=results), indent=2), encoding='utf-8')
print(json.dumps({k: v['smoothing'] for k, v in results.items()}, indent=2))
