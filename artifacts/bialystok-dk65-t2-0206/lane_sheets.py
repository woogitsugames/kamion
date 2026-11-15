"""ADR 0206: contact sheets of native orthophoto crops (60 x 34 m, rotated so the edge runs left->right in driving
direction) at the midpoint of every trunk / trunk_link edge, labelled with OSM way + lanes; for counting lane lines."""
import json, math, numpy as np, rasterio
from rasterio.windows import from_bounds
from PIL import Image, ImageDraw
R = 'bialystok-kleeberga'; OUT = 'artifacts/bialystok-dk65-t2-0206/lanes'
g = json.load(open(f'Data/Regions/{R}/roads.graph.json', encoding='utf-8'))
o = rasterio.open(json.load(open(f'Data/Regions/{R}/ortho.json'))['file'])
k = 8.0; W, H = 60, 34
tiles = []
for e in sorted(g['edges'], key=lambda e: (e['attrs']['highway']['v'], e['osm_way'])):
    a = e['attrs']
    if a['highway']['v'] not in ('trunk', 'trunk_link') or e['length_m'] < 15: continue
    P = np.array(e['geometry']); s = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]; m = s[-1] / 2
    x = np.interp(m, s, P[:, 0]); y = np.interp(m, s, P[:, 1])
    i = max(1, np.searchsorted(s, m)); dx, dy = P[i] - P[i - 1]; ang = math.degrees(math.atan2(dy, dx))
    r = 50
    im = np.moveaxis(o.read(window=from_bounds(x - r, y - r, x + r, y + r, o.transform), out_shape=(3, int(2 * r * k), int(2 * r * k)), boundless=True), 0, -1)
    im = Image.fromarray(im).rotate(-ang, resample=Image.BICUBIC)  # edge direction -> +x (east) after rotation
    c = r * k; im = im.crop((int(c - W / 2 * k), int(c - H / 2 * k), int(c + W / 2 * k), int(c + H / 2 * k)))
    im = im.resize((480, 272), Image.LANCZOS); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 480, 14), fill=(0, 0, 0))
    d.text((3, 1), f"{e['osm_way']} {a['highway']['v']} L{a['lanes']['v']}({a['lanes']['src'][0]}) {e['length_m']:.0f}m @{x:.0f},{y:.0f}", fill=(255, 255, 0))
    d.line((0, 136, 480, 136), fill=(255, 0, 0)); tiles.append(im)
for n in range(0, len(tiles), 12):
    sheet = Image.new('RGB', (960, 6 * 272), (0, 0, 0))
    for j, t in enumerate(tiles[n:n + 12]): sheet.paste(t, ((j % 2) * 480, (j // 2) * 272))
    sheet.save(f'{OUT}/sheet_{n // 12:02d}.jpg', quality=88)
print(len(tiles), 'crops')
