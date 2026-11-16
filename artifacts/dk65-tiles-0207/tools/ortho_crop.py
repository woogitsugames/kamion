"""ADR 0207: north-up crop of the GUGiK ortho 0.25 m around an EPSG:2180 point (QA only). 1 m grid ticks on the border.
uv run --project tools/worldgen python artifacts/dk65-tiles-0207/tools/ortho_crop.py <region> <x> <y> <size_m> <scale> <out.jpg>"""
import json, sys
from pathlib import Path
import rasterio
from rasterio.windows import from_bounds
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[3]
reg, x, y, size, sc, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5]), sys.argv[6]
o = json.loads((ROOT / "Data/Regions" / reg / "ortho.json").read_text(encoding="utf-8"))
ds = rasterio.open(ROOT / o["file"])
h = size / 2
a = ds.read(window=from_bounds(x - h, y - h, x + h, y + h, ds.transform), boundless=True)[:3].transpose(1, 2, 0)
im = Image.fromarray(a).resize((a.shape[1] * sc, a.shape[0] * sc), Image.NEAREST)
d = ImageDraw.Draw(im); ppm = 4 * sc
for m in range(int(size) + 1):
    L = 12 if m % 5 == 0 else 5
    d.line([(m * ppm, 0), (m * ppm, L)], fill=(255, 0, 0)); d.line([(0, m * ppm), (L, m * ppm)], fill=(255, 0, 0))
d.text((14, 14), f"{reg} ({x:.0f},{y:.0f}) {size:.0f} m N-up, ticks 1 m; GUGiK orto 2024", fill=(255, 255, 0))
im.save(out, quality=90)
