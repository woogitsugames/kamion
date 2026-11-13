"""Mean / median sRGB of pixel boxes. usage: pxabs.py img x0,y0,x1,y1 [...]"""
import sys
import numpy as np
from PIL import Image
im = np.asarray(Image.open(sys.argv[1]).convert("RGB"), float)
for a in sys.argv[2:]:
    x0, y0, x1, y1 = map(int, a.split(","))
    r = im[y0:y1, x0:x1].reshape(-1, 3)
    print(a, "mean", r.mean(0).round(0), "median", np.median(r, 0).round(0))
