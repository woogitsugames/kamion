"""Ortho crop with the road graph drawn on it (QA aid, ADR 0204).  usage: ortho_graph.py REGION cx cy half out.jpg [px]"""
import sys, json, rasterio, numpy as np
from rasterio.windows import from_bounds
from PIL import Image, ImageDraw
reg, cx, cy, half, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
px = int(sys.argv[6]) if len(sys.argv) > 6 else 960
draw_graph = (sys.argv[7] if len(sys.argv) > 7 else "1") == "1"
g = json.load(open(f"Data/Regions/{reg}/roads.graph.json", encoding="utf-8"))
with rasterio.open(f"Data/raw/derived/{reg}/ortho_0p25m.tif") as ds:
    w = from_bounds(cx - half, cy - half, cx + half, cy + half, ds.transform)
    a = ds.read([1, 2, 3], window=w, out_shape=(3, px, px), boundless=True)
im = Image.fromarray(np.moveaxis(a, 0, 2)); d = ImageDraw.Draw(im)
def P(x, y): return ((x - (cx - half)) / (2 * half) * px, (cy + half - y) / (2 * half) * px)
col = {"primary": (255, 60, 60), "secondary": (255, 160, 0), "tertiary": (255, 230, 0), "residential": (0, 255, 255), "service": (190, 190, 255), "unclassified": (0, 255, 120)}
if draw_graph:
    for e in g["edges"]:
        h = e["attrs"]["highway"]["v"]
        d.line([P(*p) for p in e["geometry"]], fill=col.get(h, (255, 255, 255)), width=1)
im.save(out, quality=88)
