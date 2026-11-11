"""Luminance variation of plain plaster rectangles on the renders, by spatial band (ADR 0094, review s9 P1-2 / P2-4).

    uv run --project tools/worldgen python artifacts/buildings-r14/bands_screen.py artifacts/buildings-r14/<round>/<Tier-light>

Rectangles in the 1280 px JPG frame (measured on the full-size PNG). Bands = differences of Gaussian blurs of the
luminance (sigma = band edge / 2 px of the full-size PNG): < 1.5 px, 1.5-3, 3-8, 8-24, > 24 px (the last = what is left
after the 24 px blur, minus its plane fit, so a lighting gradient across the wall does not count). sRGB levels (std).
p5-p95 = spread of the 3 px-blurred luminance. The reviewer's own filter is not in the repo: compare rounds, not
absolute values with the review."""
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

RECTS = [
    ("r10_fence_2", "white office wall, above windows", 40, 75, 380, 135),
    ("r10_fence_2", "white office wall, between windows", 142, 160, 220, 245),
    ("r10_block_3", "grey gable", 1085, 150, 1180, 300),
    ("r10_block_1", "grey gable", 1118, 70, 1146, 240),
    ("r10_house_2", "white house gable", 722, 250, 752, 288),
]


def main():
    d = Path(sys.argv[1])
    for cam, name, x0, y0, x1, y1 in RECTS:
        p = d / f"{cam}.png"
        if not p.exists():
            print(f"{cam:12s} {name:34s} missing")
            continue
        im = Image.open(p).convert("RGB")
        k = im.width / 1280.0
        a = np.asarray(im.crop((int(x0 * k), int(y0 * k), int(x1 * k), int(y1 * k))), float) @ [0.2126, 0.7152, 0.0722]
        prev, out = a, []
        for e in (1.5, 3, 8, 24):
            low = ndimage.gaussian_filter(a, e / 2, mode="nearest")
            out.append((prev - low)[6:-6, 6:-6].std())
            prev = low
        yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
        A = np.column_stack([xx.ravel(), yy.ravel(), np.ones(a.size)])
        res = prev.ravel() - A @ np.linalg.lstsq(A, prev.ravel(), rcond=None)[0]
        out.append(res.std())
        b3 = ndimage.gaussian_filter(a, 1.5, mode="nearest")[6:-6, 6:-6]
        print(f"{cam:12s} {name:34s} mean {a.mean():6.1f}  <1.5 {out[0]:.2f}  1.5-3 {out[1]:.2f}  3-8 {out[2]:.2f}  8-24 {out[3]:.2f}"
              f"  >24 {out[4]:.2f}  p5-p95 {np.percentile(b3, 95) - np.percentile(b3, 5):.1f}")


main()
