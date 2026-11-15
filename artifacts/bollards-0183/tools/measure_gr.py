"""ADR 0183 r4: G/R of the red chain vs the red post bands (review P1-1 regions, detail-2m) and the lower-chain
luminance contrast in the photo-matched frame (P1-3). Red pixels = R > 1.25 G and R > 60."""
import sys
import numpy as np
from PIL import Image
A = "artifacts/bollards-0183/renders"


def gr(png, box):
    a = np.asarray(Image.open(png).convert("RGB")).astype(float)[box[1]:box[3], box[0]:box[2]].reshape(-1, 3)
    m = (a[:, 0] > 1.25 * a[:, 1]) & (a[:, 0] > 60)
    if m.sum() < 5:
        return None, int(m.sum())
    c = a[m].mean(0)
    return (round(c[1] / c[0], 2), [int(x) for x in c]), int(m.sum())


for tag in sys.argv[1:]:
    for t in ("low", "high"):
        p = f"{A}/{tag}-{t}/bollards-detail-2m.png"
        print(tag, t, "chain", gr(p, (1640, 370, 1900, 470)), "post", gr(p, (1470, 400, 1570, 800)))
