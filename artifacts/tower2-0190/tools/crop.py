"""Ortho crop with footprints. usage: crop.py E0 N0 E1 N1 out.jpg [px_per_m]"""
import json, sys
import numpy as np
from PIL import Image, ImageDraw
Image.MAX_IMAGE_PIXELS = None
ox, oy = 777995.0, 596223.0
x0, y0, x1, y1 = map(float, sys.argv[1:5]); sc = float(sys.argv[6]) if len(sys.argv) > 6 else 4.0
b = (776971.0, 595199.0, 779019.0, 597247.0)
im = Image.open("Data/raw/derived/bialystok-industrial-c/ortho_0p25m.tif")
c = im.crop((int((x0 + ox - b[0]) * 4), int((b[3] - (y1 + oy)) * 4), int((x1 + ox - b[0]) * 4), int((b[3] - (y0 + oy)) * 4))).convert("RGB")
c = c.resize((int((x1 - x0) * sc), int((y1 - y0) * sc)), Image.LANCZOS)
d = ImageDraw.Draw(c)
P = lambda x, y: ((x - x0) * sc, (y1 - y) * sc)
for f in json.load(open("Data/Regions/bialystok-industrial-c/buildings.geojson", encoding="utf-8"))["features"]:
    for poly in f["geometry"]["coordinates"]:
        r = np.asarray(poly[0]) - [ox, oy]; m = r.mean(0)
        if x0 < m[0] < x1 and y0 < m[1] < y1:
            d.line([P(*q) for q in r], fill=(255, 255, 0), width=1)
            p = f["properties"]
            d.text(P(*m), f"{f['id'][-28:-21] if f['id'].startswith('bdot') else f['id'][-9:]} {p.get('height_m')}", fill=(255, 60, 255))
g = 10 if x1 - x0 < 200 else 50
for v in np.arange(np.ceil(x0 / g) * g, x1, g):
    d.line([P(v, y0), P(v, y1)], fill=(255, 255, 255, 60), width=1); d.text(P(v + 0.5, y1 - 1), str(int(v)), fill=(255, 255, 255))
for v in np.arange(np.ceil(y0 / g) * g, y1, g):
    d.line([P(x0, v), P(x1, v)], fill=(255, 255, 255), width=1); d.text(P(x0 + 0.5, v), str(int(v)), fill=(255, 255, 255))
c.save(sys.argv[5], quality=88)
