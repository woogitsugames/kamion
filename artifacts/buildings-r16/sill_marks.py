"""Per-mark contrast of the sill whiskers (ADR 0114 P1-f) from the Runoff on / off pair of one camera.
    python sill_marks.py <round dir> [camera ...]      (reads <round>/extra/<cam>.png and <round>/sill_off/<cam>.png)
A mark = a connected region darkened by >= 3 sRGB levels (luma). Whisker core = mean over the rows of the lower 2/3 of
the mark (below the band under the drip edge) of the strongest darkening in that row."""
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

w = np.array([0.2126, 0.7152, 0.0722])
import os
ON = os.environ.get("SILL_ON", "extra")      # sub-directory of the Runoff-on renders
rd = sys.argv[1]
for cam in sys.argv[2:] or ("r15_sill_5m", "r15_sill_20m"):
    on = np.asarray(Image.open(f"{rd}/{ON}/{cam}.png").convert("RGB")).astype(float) @ w
    off = np.asarray(Image.open(f"{rd}/sill_off/{cam}.png").convert("RGB")).astype(float) @ w
    d = off - on
    lab, n = ndimage.label(d >= 3.0)
    res = []
    for k, sl in enumerate(ndimage.find_objects(lab), 1):
        hh, ww = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        m = lab[sl] == k
        if m.sum() < 12 or hh < 5:
            continue
        reg = d[sl]
        rows = [reg[r][m[r]].max() for r in range(hh // 3, hh) if m[r].any()]
        res.append((np.mean(rows), reg[m].mean(), off[sl][m].mean(), ww, hh))
    a = np.array(res)
    print(f"{cam}: marks {len(a)} | whisker core median {np.median(a[:, 0]):.1f} (p10 {np.percentile(a[:, 0], 10):.1f}, "
          f"p90 {np.percentile(a[:, 0], 90):.1f}) sRGB levels | mean over the mark median {np.median(a[:, 1]):.1f} | "
          f"wall level {np.median(a[:, 2]):.0f} | mark {np.median(a[:, 3]):.0f} x {np.median(a[:, 4]):.0f} px")
