"""Contrast of the sill marks (P1-f / review 0107 P1-r7-g), measured, not judged: the same camera rendered with the
run-off layer on and off (scripts/visual-qa.ps1 -Runoff on|off); the difference isolates the marks.
    python sill_contrast.py <on.png> <off.png> [x0 y0 x1 y1] [--out diff.png]
Reports, inside the crop (default: whole frame):
    marked px        pixels darkened by >= 3 sRGB levels (luma, 8 bit)
    p50 / p90 / max  darkening of the marked pixels, sRGB levels
    whiskers         connected marked regions taller than wide (>= 3:1) and >= 6 px tall, with their mean darkening
A mark 'reads' when its whiskers darken the wall by >= 6-8 levels (task threshold from 20 m)."""
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

args = [a for a in sys.argv[1:] if not a.startswith("--")]
on = np.asarray(Image.open(args[0]).convert("RGB")).astype(float)
off = np.asarray(Image.open(args[1]).convert("RGB")).astype(float)
if len(args) >= 6:
    x0, y0, x1, y1 = map(int, args[2:6])
    on, off = on[y0:y1, x0:x1], off[y0:y1, x0:x1]
w = np.array([0.2126, 0.7152, 0.0722])
d = (off @ w) - (on @ w)                       # darkening by the marks, sRGB levels
m = d >= 3.0
print(f"frame {on.shape[1]}x{on.shape[0]}: marked px {int(m.sum())} ({100 * m.mean():.2f} %)")
if m.any():
    v = d[m]
    print(f"darkening of marked px: p50 {np.percentile(v, 50):.1f}  p90 {np.percentile(v, 90):.1f}  max {v.max():.1f} sRGB levels")
lab, n = ndimage.label(d >= 4.0)
wh = []
for k, sl in enumerate(ndimage.find_objects(lab), 1):
    hh, ww = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
    if hh >= 6 and hh >= 3 * ww:
        reg = d[sl][lab[sl] == k]
        wh.append((float(reg.mean()), float(np.percentile(reg, 90)), ww, hh))
if wh:
    a = np.array(wh)
    print(f"whiskers: {len(wh)}; mean darkening median {np.median(a[:, 0]):.1f} (p10 {np.percentile(a[:, 0], 10):.1f}, "
          f"p90 {np.percentile(a[:, 0], 90):.1f}); core (p90 in whisker) median {np.median(a[:, 1]):.1f}; "
          f"width median {np.median(a[:, 2]):.0f} px, height median {np.median(a[:, 3]):.0f} px")
else:
    print("whiskers: 0")
if "--out" in sys.argv:
    out = sys.argv[sys.argv.index("--out") + 1]
    Image.fromarray(np.clip(d * 6 + 20, 0, 255).astype(np.uint8)).save(out)
