"""Screen measurements of ADR 0091 (same rectangles every round; coordinates in the 1280 px wide JPG).

    uv run --project tools/worldgen python artifacts/buildings-r11/measure.py artifacts/buildings-r11/<round>/<Tier-light>

mean = mean sRGB 8-bit of the rectangle in the 1280 px JPG (what the s9 review measured);
hf = standard deviation of the luminance after removing everything coarser than ~3 px of the full-size PNG
     (the high-frequency 'pepper' of the render grain), in sRGB levels.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

RECTS = [  # camera, name, x0, y0, x1, y1
    ("r10_block_3", "sky", 600, 40, 760, 100),
    ("r10_block_3", "grey plaster gable", 1085, 150, 1180, 300),
    ("r10_block_3", "grey plaster front", 480, 108, 570, 140),
    ("r10_block_3", "plinth", 1110, 328, 1220, 355),
    ("r10_block_4", "sky", 700, 60, 800, 160),
    ("r10_block_4", "brick", 250, 80, 450, 280),
    ("r10_block_4", "peach plaster", 1120, 110, 1180, 200),
    ("r10_block_2", "sky", 560, 30, 680, 90),
    ("r10_block_2", "yellow plaster", 250, 30, 330, 70),
    ("r10_house_2", "sky", 500, 30, 800, 90),
]


def main():
    d = Path(sys.argv[1])
    for cam, name, x0, y0, x1, y1 in RECTS:
        j = d / "1280" / f"{cam}.jpg"
        p = d / f"{cam}.png"
        if not j.exists():
            print(f"{cam:12s} {name:20s} missing")
            continue
        a = np.asarray(Image.open(j).convert("RGB"), float)[y0:y1, x0:x1]
        m = a.reshape(-1, 3).mean(0)
        im = Image.open(p).convert("L")
        k = im.width / 1280.0
        c = im.crop((int(x0 * k), int(y0 * k), int(x1 * k), int(y1 * k)))
        hf = np.asarray(c, float) - np.asarray(c.filter(ImageFilter.GaussianBlur(3)), float)
        print(f"{cam:12s} {name:20s} mean {m[0]:5.1f} {m[1]:5.1f} {m[2]:5.1f}  avg {m.mean():5.1f}  R/B {m[0] / max(m[2], 1):.2f}  hf {hf[4:-4, 4:-4].std():.2f}")


main()
