"""ADR 0341 windscreen layer: before / after measurement of the cab control cameras (visual-qa PNGs, 2340 x 1080).

uv run --no-project --with numpy --with pillow python tools/rendering/windscreen_measure.py <before_dir> <after_dir> <out_dir>
Each dir holds <Tier>-<lighting>/<camera>.png. Regions (fractions of the frame, cab-driver / cab-dash framing):
  road  - the road seen through the lower windscreen (readability: high-pass contrast must survive),
  sky   - sky through the upper windscreen,
  pane  - the whole windscreen above the dash (added light statistics).
Output: measure.txt (luma in sRGB %, linear added light), diff_<id>.jpg (|after - before| x8), pair_<id>.jpg (crops 1:1).
"""
import os
import sys

import numpy as np
from PIL import Image

REGIONS = {
    "cab-driver": {"road": (0.28, 0.43, 0.90, 0.72), "sky": (0.30, 0.05, 0.70, 0.40), "pane": (0.26, 0.0, 1.0, 0.74),
                   "crop": (1100, 560, 1600, 820)},
    "cab-dash": {"road": (0.20, 0.25, 0.75, 0.45), "sky": (0.25, 0.0, 0.60, 0.10), "pane": (0.10, 0.0, 1.0, 0.48),
                 "crop": (900, 250, 1400, 510)},
}


def load(p):
    a = np.asarray(Image.open(p).convert("RGB")).astype(np.float32) / 255.0
    return a


def lin(a):
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)


def luma(a):
    return a @ np.array([0.2126, 0.7152, 0.0722], np.float32)


def box(a, r):
    k = 2 * r + 1
    c = np.cumsum(np.cumsum(np.pad(a, r + 1, mode="edge"), 0), 1)
    return (c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k])[: a.shape[0], : a.shape[1]] / (k * k)


def reg(img, f):
    h, w = img.shape[:2]
    x0, y0, x1, y1 = f
    return img[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)]


def main():
    bdir, adir, out = sys.argv[1:4]
    os.makedirs(out, exist_ok=True)
    lines = ["ADR 0341 windscreen layer - before vs after (luma sRGB %, added = linear after - before, x100)"]
    for case in sorted(os.listdir(adir)):
        for cam, R in REGIONS.items():
            pa, pb = os.path.join(adir, case, cam + ".png"), os.path.join(bdir, case, cam + ".png")
            if not (os.path.exists(pa) and os.path.exists(pb)):
                continue
            a, b = load(pa), load(pb)
            ya, yb = luma(a), luma(b)
            la, lb = luma(lin(a)), luma(lin(b))
            res = []
            for name in ("road", "sky"):
                ra, rb = reg(ya, R[name]), reg(yb, R[name])
                hpa, hpb = ra - box(ra, 3), rb - box(rb, 3)
                res.append(f"{name} mean {rb.mean() * 100:.1f}->{ra.mean() * 100:.1f} hp-sigma {hpb.std() * 100:.2f}->{hpa.std() * 100:.2f}"
                           f" (x{hpa.std() / max(hpb.std(), 1e-6):.2f})")
            d = reg(la, R["pane"]) - reg(lb, R["pane"])
            res.append(f"pane added p50 {np.percentile(d, 50) * 100:.2f} p95 {np.percentile(d, 95) * 100:.2f} "
                       f"p99 {np.percentile(d, 99) * 100:.2f} max {d.max() * 100:.2f}")
            lines.append(f"{case:16s} {cam:10s} " + " | ".join(res))
            tag = f"{case}_{cam}"
            diff = np.clip(np.abs(a - b) * 8.0, 0, 1)
            Image.fromarray((diff * 255).astype(np.uint8)).resize((960, 443)).save(os.path.join(out, f"diff_{tag}.jpg"), quality=88)
            x0, y0, x1, y1 = R["crop"]
            pair = np.concatenate([b[y0:y1, x0:x1], np.ones((y1 - y0, 6, 3), np.float32), a[y0:y1, x0:x1]], axis=1)
            Image.fromarray((pair * 255).astype(np.uint8)).save(os.path.join(out, f"pair_{tag}.jpg"), quality=90)
    txt = "\n".join(lines)
    open(os.path.join(out, "measure.txt"), "w", encoding="utf-8").write(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()
