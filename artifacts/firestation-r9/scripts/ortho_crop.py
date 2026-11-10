"""Crop the GUGiK 0.25 m orthophoto around JRG2 and draw the BDOT/OSM footprints + route. Reference only."""
import json, sys
from pathlib import Path
import numpy as np
import rasterio
from rasterio.windows import from_bounds
from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parents[3]
ox, oy = 777995.0, 596223.0
cx, cy = ox - 235.0, oy - 147.0
half = float(sys.argv[1]) if len(sys.argv) > 1 else 90.0
out = Path(sys.argv[2]) if len(sys.argv) > 2 else REPO / "artifacts/firestation-r9/refs/ortho_site.png"
tif = REPO / "Data/raw/derived/bialystok-industrial-c/ortho_0p25m.tif"
with rasterio.open(tif) as ds:
    w = from_bounds(cx - half, cy - half, cx + half, cy + half, ds.transform)
    a = ds.read([1, 2, 3], window=w)
im = Image.fromarray(np.moveaxis(a, 0, 2))
scale = 4 if half <= 60 else 2
im = im.resize((im.width * scale // 1, im.height * scale // 1), Image.LANCZOS)
ppm = im.width / (2 * half)
im.save(out.with_name(out.stem + "_clean.png"))
d = ImageDraw.Draw(im)


def px(e, n):
    return ((e + ox - (cx - half)) * ppm, ((cy + half) - (n + oy)) * ppm)


bdot = [[-262.92, -142.67], [-248.56, -154.39], [-248.18, -153.91], [-240.74, -159.51], [-239.85, -158.33], [-237.42, -160.1], [-233.51, -165.5], [-224.75, -172.17], [-209.53, -153.03], [-220.88, -143.87], [-219.95, -142.68], [-231.72, -133.16], [-229.42, -130.09], [-235.82, -125.08], [-243.99, -118.69], [-262.92, -142.67]]
osm = [[-222.74, -173.85], [-233.36, -165.13], [-238.92, -159.17], [-240.01, -160.4], [-262.44, -142.62], [-243.73, -118.95], [-229.11, -130.46], [-232.18, -134.34], [-217.59, -145.82], [-217.37, -145.53], [-206.88, -153.79], [-222.74, -173.85]]
d.line([px(*p) for p in bdot], fill=(255, 220, 0), width=2)
d.line([px(*p) for p in osm], fill=(0, 255, 255), width=1)
r = json.load(open(REPO / "Data/Regions/bialystok-industrial-c/route_start.json"))
d.line([px(*p) for p in r["points_en"]], fill=(255, 0, 0), width=2)
# 10 m grid ticks
for k in range(int(-half), int(half) + 1, 10):
    x, y = px(-235 + k, -147 - half)
    d.line([(x, im.height - 8), (x, im.height)], fill=(255, 255, 255))
    x, y = px(-235 - half, -147 + k)
    d.line([(0, y), (8, y)], fill=(255, 255, 255))
im.save(out)
print(out, im.size, "ppm", ppm)
