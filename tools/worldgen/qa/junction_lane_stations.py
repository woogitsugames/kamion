"""ADR 0203: lane-count check of DK8/DK65 mainline + slip roads. One cell per trunk / trunk_link edge >= 35 m:
[orthophoto | generated top view], 80 x 50 m around the edge midpoint, labelled with OSM way, lanes (tag source)."""
import json, sys, numpy as np, rasterio
from rasterio.windows import from_bounds
from PIL import Image, ImageDraw
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[1])); sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
import junction_topview as jt
from roads import pipeline
R = __import__('os').environ.get('REGION', 'bialystok-maczka'); out = sys.argv[1]
g = json.load(open(f'Data/Regions/{R}/roads.graph.json', encoding='utf-8'))
reg = pipeline.load_region(R); ox, oy = reg['origin']['x'], reg['origin']['y']
o = rasterio.open(json.load(open(f'Data/Regions/{R}/ortho.json'))['file'])
world = jt.load_world(R)
E = [e for e in g['edges'] if e['attrs']['highway']['v'] in ('trunk', 'trunk_link') and e['length_m'] >= 35]
def mid(e):
    P = np.array(e['geometry']); s = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
    return np.array([np.interp(s[-1] / 2, s, P[:, 0]), np.interp(s[-1] / 2, s, P[:, 1])])
E.sort(key=lambda e: (-round(mid(e)[0] / 60), -mid(e)[1]))
W, H, K = 80.0, 50.0, 4          # metres, px per metre
cw, ch = int(W * K), int(H * K)
cols = 2; rows_per = 8; rows = []
for i, e in enumerate(E):
    m = mid(e); a = e['attrs']
    ob = o.read(window=from_bounds(m[0] - W / 2, m[1] - H / 2, m[0] + W / 2, m[1] + H / 2, o.transform), out_shape=(3, ch, cw), boundless=True)
    left = Image.fromarray(np.moveaxis(ob, 0, -1)).convert('RGB')
    big, _ = jt.topview(world, m[0] - ox, m[1] - oy, W, cw)
    right = big.crop((0, (cw - ch) // 2, cw, (cw + ch) // 2))
    cell = Image.new('RGB', (cw * 2 + 4, ch + 16), (0, 0, 0)); cell.paste(left, (0, 16)); cell.paste(right, (cw + 4, 16))
    d = ImageDraw.Draw(cell)
    for im in (0, cw + 4):
        d.ellipse((im + cw / 2 - 3, 16 + ch / 2 - 3, im + cw / 2 + 3, 16 + ch / 2 + 3), outline=(255, 0, 0))
    d.text((4, 2), f"#{i} {a['highway']['v']} way {e['osm_way']} lanes={a['lanes']['v']} ({a['lanes']['src']}) x={m[0]:.0f} y={m[1]:.0f} L={e['length_m']:.0f}", fill=(255, 255, 0))
    rows.append(cell)
for p in range(0, len(rows), cols * rows_per):
    part = rows[p:p + cols * rows_per]
    sheet = Image.new('RGB', (cols * (cw * 2 + 12), rows_per * (ch + 20)), (40, 40, 40))
    for k, c in enumerate(part):
        sheet.paste(c, ((k % cols) * (cw * 2 + 12), (k // cols) * (ch + 20)))
    sheet.save(f'{out}/lanes_{p // (cols * rows_per):02d}.jpg', quality=85)
print(len(E), 'edges')
