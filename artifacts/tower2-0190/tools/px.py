"""Mean sRGB of image regions given as fractions. usage: px.py img x0,y0,x1,y1 [...]"""
import sys
import numpy as np
from PIL import Image
im = np.asarray(Image.open(sys.argv[1]).convert("RGB"), float); H, W = im.shape[:2]
for a in sys.argv[2:]:
    x0, y0, x1, y1 = map(float, a.split(","))
    r = im[int(y0 * H):int(y1 * H), int(x0 * W):int(x1 * W)].reshape(-1, 3)
    print(a, "mean", r.mean(0).round(0), "median", np.median(r, 0).round(0), W, H)
