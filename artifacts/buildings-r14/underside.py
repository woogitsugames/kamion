"""ADR 0107 P1-e: balcony slab underside vs the wall beside it (same rectangles, full-size PNG, sRGB 8-bit means).
    python underside.py <round>/<Tier-light> [...]"""
import sys
import numpy as np
from PIL import Image
R = {"r10_block_4": {"underside": (2150, 300, 2230, 325), "wall": (2300, 350, 2330, 400)}}
for d in sys.argv[1:]:
    for cam, rr in R.items():
        im = np.asarray(Image.open(f"{d}/{cam}.png").convert("RGB"), float)
        m = {k: im[y0:y1, x0:x1].reshape(-1, 3).mean(0) for k, (x0, y0, x1, y1) in rr.items()}
        lum = {k: 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2] for k, v in m.items()}
        print(f"{d} {cam}: underside {m['underside'].round(0)} wall {m['wall'].round(0)} ratio {lum['underside'] / lum['wall']:.2f}")
