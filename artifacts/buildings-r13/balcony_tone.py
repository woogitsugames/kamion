"""P1-5 (review s9): balustrade tone against the wall beside it, r10_block_4 (full-size PNG pixels).
    python balcony_tone.py <round>/<Tier-light> [...]"""
import sys
import numpy as np
from PIL import Image
R = {"wall (peach)": (2292, 300, 2325, 335), "front green": (2165, 210, 2250, 255), "front brown": (2180, 470, 2295, 505),
     "front grey sheet": (1942, 268, 1988, 288), "side green": (2068, 262, 2085, 300), "slab underside": (2110, 330, 2200, 345)}
for d in sys.argv[1:]:
    im = np.asarray(Image.open(f"{d}/r10_block_4.png").convert("RGB"), float)
    w = im[R["wall (peach)"][1]:R["wall (peach)"][3], R["wall (peach)"][0]:R["wall (peach)"][2]].mean()
    out = []
    for k, (x0, y0, x1, y1) in R.items():
        m = im[y0:y1, x0:x1].reshape(-1, 3).mean(0)
        out.append(f"{k} {m[0]:.0f}/{m[1]:.0f}/{m[2]:.0f} ({m.mean() / w:.2f})")
    print(d, "|", " | ".join(out))
