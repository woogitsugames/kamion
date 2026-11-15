"""ADR 0203: orthophoto crop + roads.graph.json overlay (lanes / oneway labels) per junction check, data-level."""
import json, sys, numpy as np, rasterio
from rasterio.windows import from_bounds
from PIL import Image, ImageDraw
R = sys.argv[1]; out = sys.argv[2]; PX = 1200
g = json.load(open(f'Data/Regions/{R}/roads.graph.json', encoding='utf-8'))
J = json.load(open(f'Data/Regions/{R}/junction_checks.authored.json', encoding='utf-8'))['junctions']
o = rasterio.open(json.load(open(f'Data/Regions/{R}/ortho.json'))['file'])
COL = {'trunk': (255, 60, 60), 'trunk_link': (255, 160, 0), 'secondary': (255, 255, 0), 'tertiary': (120, 255, 120)}
for c in J:
    x, y = c['center_2180']; h = c['size_m'] / 2; k = PX / c['size_m']
    im = Image.fromarray(np.moveaxis(o.read(window=from_bounds(x-h, y-h, x+h, y+h, o.transform), out_shape=(3, PX, PX), boundless=True), 0, -1)).convert('RGB')
    two = Image.new('RGB', (PX * 2 + 8, PX)); two.paste(im, (0, 0))
    d = ImageDraw.Draw(im)
    for e in g['edges']:
        P = [((p[0] - x + h) * k, (y + h - p[1]) * k) for p in e['geometry']]
        if not any(0 <= p[0] <= PX and 0 <= p[1] <= PX for p in P): continue
        a = e['attrs']; hw = a['highway']['v']
        d.line(P, fill=COL.get(hw, (120, 200, 255)), width=2)
        m = P[len(P) // 2]
        if hw in COL:
            d.text(m, f"{a['lanes']['v']}{'>' if a['oneway']['v'] == 'yes' else ''}{'*' if a['lanes']['src']=='default' else ''}", fill=(255, 255, 255))
    two.paste(im, (PX + 8, 0)); two.resize((1928, 960), Image.LANCZOS).save(f"{out}/{c['id']}.jpg", quality=85)
