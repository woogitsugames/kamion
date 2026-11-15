"""ADR 0207: zoom of a straightened strip (strip_<chunk>.jpg, 8 px/m) at route station s, 30 m long, x3 = 24 px/m,
lateral ruler every 1 m (0 = OSM axis, + = left of travel, top). Usage: strip_zoom.py <region> <s> <out.jpg>"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[3]
reg, s, out = sys.argv[1], float(sys.argv[2]), sys.argv[3]
c0 = int(s // 120 * 120)
im = Image.open(ROOT / "artifacts/dk65-tiles-0207" / reg / "ortho" / f"strip_{c0:04d}.jpg")
x0 = int((s - c0) * 8); x0 = min(x0, im.size[0] - 240)
c = im.crop((x0, 20 + 8 * 6, x0 + 240, 20 + 8 * 24)).resize((720, 432), Image.LANCZOS)
d = ImageDraw.Draw(c)
for m in range(-9, 10):
    y = (8 * (15 - m) - 48) * 3
    d.line([(0, y), (25 if m % 5 else 50, y)], fill=(255, 0, 0), width=2); d.text((55, y - 6), str(m), fill=(255, 0, 0))
d.text((100, 2), f"{reg} s={s:.0f} m, 30 m long, 24 px/m", fill=(255, 255, 0))
c.save(out, quality=92)
