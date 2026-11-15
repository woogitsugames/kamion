"""Crop of the 0.1 m 2025 orthophoto (QA reference, ADR 0204). usage: ortho10.py cx cy half out.jpg [px] [dataset_dir]"""
import sys, glob, rasterio, numpy as np
from rasterio.merge import merge
from PIL import Image, ImageDraw
cx, cy, half, out = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
px = int(sys.argv[5]) if len(sys.argv) > 5 else 960
d = sys.argv[6] if len(sys.argv) > 6 else "Data/raw/gugik/gugik-orto-2025-rgb-0p10-knyszyn"
b = (cx - half, cy - half, cx + half, cy + half)
srcs = [rasterio.open(f) for f in sorted(glob.glob(d + "/*.tif"))]
srcs = [s for s in srcs if not (s.bounds.right < b[0] or s.bounds.left > b[2] or s.bounds.top < b[1] or s.bounds.bottom > b[3])]
a, _ = merge(srcs, bounds=b, res=2 * half / px, indexes=[1, 2, 3])
im = Image.fromarray(np.moveaxis(a, 0, 2)).resize((px, px)); dr = ImageDraw.Draw(im)
step = 10 if half <= 60 else (50 if half <= 300 else 200)
import math
x = math.ceil(b[0] / step) * step
while x < b[2]:
    X = (x - b[0]) / (2 * half) * px; dr.line([(X, 0), (X, 8)], fill=(255, 255, 0)); dr.text((X + 2, 8), str(int(x) % 10000), fill=(255, 255, 0)); x += step
y = math.ceil(b[1] / step) * step
while y < b[3]:
    Y = (b[3] - y) / (2 * half) * px; dr.line([(0, Y), (8, Y)], fill=(255, 255, 0)); dr.text((10, Y - 5), str(int(y) % 10000), fill=(255, 255, 0)); y += step
im.save(out, quality=90)
