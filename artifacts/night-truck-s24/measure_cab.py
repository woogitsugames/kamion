# uv run --no-project --with pillow --with numpy --with scipy python measure_cab.py <tagdir>
# Regions in 1920x1080 cab-driver (FOV 70) = review s24 K1 regions x2 (they were on 960x540 sheets).
# Shadow jaggedness (clear, cab-hub left dash 0..700 x 120..500 and cab-dash lower left 0..600 x 780..1080): binarise at
# the midpoint between the 20th and 80th luminance percentile, perimeter of the binary mask vs perimeter after a
# gaussian (sigma 3 px) smoothing of the mask -> ratio 1.0 = smooth edges, > 1 = staircase.
import sys, os, numpy as np
from PIL import Image
from scipy import ndimage

def load(p): return np.asarray(Image.open(p).convert('RGB')).astype(np.float32)
def luma(a): return a @ np.array([0.2126, 0.7152, 0.0722], np.float32)
def reg(a, x0, x1, y0, y1): return a[y0:y1, x0:x1]
def perim(m): return (m ^ ndimage.binary_erosion(m)).sum()

tag = sys.argv[1]
R = {'sky': (600, 1400, 0, 300), 'dash-under-cluster': (660, 1260, 920, 1080), 'pillarA': (260, 380, 400, 800),
     'cluster-left-dash': (690, 800, 840, 960), 'cluster-right-dash': (1130, 1240, 840, 960), 'rim-top': (760, 1160, 735, 790),
     'road': (700, 1300, 520, 700)}
for tl in ('High-night', 'Low-night', 'High-dusk'):
    p = os.path.join(tag, f'cab-{tl}', 'cab-driver.png')
    if not os.path.exists(p): continue
    a = load(p); y = luma(a)
    print(f'{tl:10s} cab-driver mean {y.mean():5.1f} | ' + ' | '.join(f'{k} {reg(y, *v).mean():5.1f}' for k, v in R.items()))
    p = os.path.join(tag, f'cab-{tl}', 'cab-dash.png')
    if os.path.exists(p):
        y = luma(load(p))
        print(f'{tl:10s} cab-dash   mean {y.mean():5.1f} | p99 {np.percentile(y, 99):5.1f} | max {y.max():5.1f}')
for tl in ('High-clear', 'Ultra-clear', 'Low-clear'):
    for cam, box in (('cab-hub', (0, 700, 120, 500)), ('cab-dash', (0, 600, 780, 1080)), ('cab-driver', (0, 400, 840, 1000))):
        p = os.path.join(tag, f'cab-{tl}', cam + '.png')
        if not os.path.exists(p): continue
        y = reg(luma(load(p)), *box)
        thr = 0.5 * (np.percentile(y, 20) + np.percentile(y, 80))
        m = y > thr
        sm = ndimage.gaussian_filter(m.astype(np.float32), 3) > 0.5
        print(f'{tl:11s} {cam:10s} jagged {perim(m) / max(perim(sm), 1):5.2f} (thr {thr:5.1f}, p20 {np.percentile(y, 20):5.1f}, p80 {np.percentile(y, 80):5.1f})')
