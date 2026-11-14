"""Row profile of a wall strip: mean luminance per row of the box x0,y0,x1,y1 -> wall level (p90), band level, lintel.
usage: rows.py img x0,y0,x1,y1"""
import sys
import numpy as np
from PIL import Image
im = np.asarray(Image.open(sys.argv[1]).convert("RGB"), float)
x0, y0, x1, y1 = map(int, sys.argv[2].split(","))
c = im[y0:y1, x0:x1]
L = (0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2])
r = L.mean(1)
print("rows", " ".join(f"{v:.0f}" for v in r))
wall = np.percentile(r, 85)
print(f"wall(p85 of rows) {wall:.0f}  min row {r.min():.0f}  mean rgb of wall rows {c[r > wall - 3].reshape(-1, 3).mean(0).round(0)}")
print("pixel percentiles of box p5/p25/p50/p75/p95:", np.percentile(L, [5, 25, 50, 75, 95]).round(0))
