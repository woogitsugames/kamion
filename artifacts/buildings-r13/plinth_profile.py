"""Plinth splash contrast: mean luma per row of a plinth column (1280 px JPG), top band vs bottom band.
    python plinth_profile.py <dir> [camera x0 x1 y0 y1]"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
d = Path(sys.argv[1])
cam, x0, x1, y0, y1 = (sys.argv[2], *map(int, sys.argv[3:7])) if len(sys.argv) > 6 else ("r10_block_3", 1110, 1220, 322, 362)
a = np.asarray(Image.open(d / "1280" / f"{cam}.jpg").convert("RGB"), float)[y0:y1, x0:x1]
l = a @ [0.2126, 0.7152, 0.0722]
rows = l.mean(1)
print(cam, "rows", " ".join(f"{v:.0f}" for v in rows))
n = max(2, len(rows) // 5)
print(f"top {rows[:n].mean():.1f} bottom {rows[-n:].mean():.1f} diff {rows[:n].mean() - rows[-n:].mean():.1f}")
