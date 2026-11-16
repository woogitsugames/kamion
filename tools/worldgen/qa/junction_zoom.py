"""ADR 0203: zoomed [ortho | generated] pairs at given EPSG:2180 points: zoom.py out.jpg W H x,y[,label] ..."""
import json, sys, numpy as np, rasterio
from rasterio.windows import from_bounds
from PIL import Image, ImageDraw
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[1])); sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
import junction_topview as jt
from roads import pipeline
R = __import__('os').environ.get('REGION', 'bialystok-maczka'); out = sys.argv[1]; W = float(sys.argv[2]); H = float(sys.argv[3]); K = 960 / W
reg = pipeline.load_region(R); ox, oy = reg['origin']['x'], reg['origin']['y']
o = rasterio.open(json.load(open(f'Data/Regions/{R}/ortho.json'))['file']); world = jt.load_world(R)
cw, ch = 960, int(H * K); cells = []
for a in sys.argv[4:]:
    v = a.split(','); x, y = float(v[0]), float(v[1])
    ob = o.read(window=from_bounds(x - W / 2, y - H / 2, x + W / 2, y + H / 2, o.transform), out_shape=(3, ch, cw), boundless=True, resampling=rasterio.enums.Resampling.cubic)
    big, _ = jt.topview(world, x - ox, y - oy, W, cw)
    c = Image.new('RGB', (cw * 2 + 4, ch + 14)); c.paste(Image.fromarray(np.moveaxis(ob, 0, -1)).convert('RGB'), (0, 14)); c.paste(big.crop((0, (cw - ch) // 2, cw, (cw + ch) // 2)), (cw + 4, 14))
    ImageDraw.Draw(c).text((4, 1), f"{a}  {W:.0f} x {H:.0f} m", fill=(255, 255, 0)); cells.append(c)
s = Image.new('RGB', (cw * 2 + 4, sum(c.height for c in cells))); yy = 0
for c in cells: s.paste(c, (0, yy)); yy += c.height
s.save(out, quality=88)
