# Shadow edge on the dash in cab-hub (clear): the sun shadow boundary crossing rows y 150..460 between x 150..330
# (the A-pillar shadow edge, review s24 K2). Per row: edge x = argmax |d/dx| of the 1 px-blurred luminance; staircase =
# mean |second difference| of the edge x (px; steps of a shadow-map texel give large jumps, a smooth edge ~0);
# width = 10-90 % transition width along the row (px).
import sys, os, numpy as np
from PIL import Image
from scipy import ndimage
tag = sys.argv[1]
for tl in ('High-clear', 'Ultra-clear', 'Low-clear'):
    p = os.path.join(tag, f'cab-{tl}', 'cab-hub.png')
    if not os.path.exists(p): continue
    a = np.asarray(Image.open(p).convert('RGB')).astype(np.float32) @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    g = ndimage.gaussian_filter(a, 1.0)
    xs, ws = [], []
    for y in range(150, 460):
        row = g[y, 150:330]
        d = np.abs(np.diff(row)); x = int(np.argmax(d)); xs.append(x)
        lo, hi = np.percentile(row, 5), np.percentile(row, 95)
        t10, t90 = lo + 0.1 * (hi - lo), lo + 0.9 * (hi - lo)
        seg = row[max(0, x - 40):x + 40]
        ws.append(((seg > t10) & (seg < t90)).sum())
    xs = np.array(xs, float)
    print(f'{tl:11s} staircase {np.abs(np.diff(xs, 2)).mean():5.2f} px | edge width p50 {np.median(ws):4.1f} px')
