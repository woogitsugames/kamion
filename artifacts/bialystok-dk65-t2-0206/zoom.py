"""ADR 0206: native 0.25 m orthophoto crop (with graph overlay labels) around a point; usage: zoom.py x y w h out.jpg"""
import json, sys, numpy as np, rasterio
from rasterio.windows import from_bounds
from PIL import Image, ImageDraw
R = 'bialystok-kleeberga'
x, y, w, h = map(float, sys.argv[1:5]); out = sys.argv[5]
g = json.load(open(f'Data/Regions/{R}/roads.graph.json', encoding='utf-8'))
o = rasterio.open(json.load(open(f'Data/Regions/{R}/ortho.json'))['file'])
k = 4.0; W, H = int(w * k), int(h * k)
im = Image.fromarray(np.moveaxis(o.read(window=from_bounds(x - w/2, y - h/2, x + w/2, y + h/2, o.transform), out_shape=(3, H, W), boundless=True), 0, -1)).convert('RGB')
d = ImageDraw.Draw(im)
for e in g['edges']:
    a = e['attrs']; hw = a['highway']['v']
    if hw not in ('trunk', 'trunk_link', 'secondary', 'tertiary', 'secondary_link'): continue
    P = [((p[0] - x + w/2) * k, (y + h/2 - p[1]) * k) for p in e['geometry']]
    if not any(0 <= p[0] <= W and 0 <= p[1] <= H for p in P): continue
    d.line(P, fill=(255, 60, 60), width=1)
    m = P[len(P) // 2]
    d.text((m[0] + 3, m[1] + 3), f"{e['osm_way']} L{a['lanes']['v']}", fill=(255, 255, 0))
s = float(sys.argv[6]) if len(sys.argv) > 6 else 1.0
im = im.resize((int(W * s), int(H * s)), Image.LANCZOS) if s != 1.0 else im
im.save(out, quality=88)
