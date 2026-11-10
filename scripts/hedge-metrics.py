"""N-4 berberis metric (review r7 §10 / r8 N-22, ADR 0060): hedge pixels from visual-qa `-Mask ':hedge_'` (<id>_mask.png,
magenta), eroded 2 px; Rec.709 luma p50 and sigma (% of sRGB), mean R-B (%), median HSV saturation (%), mask share.
Frames are measured at 1024 px width like the review.

usage: uv run --project tools/worldgen python scripts/hedge-metrics.py <render dir> [ids...] [--json out]
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

IDS = ["photo-biezenstwa-ground", "hedge_a_close", "hedge_c_along", "g3a_eye_s0362", "g3a_rondo_bie_approach"]


def load(p, w=1024):
    im = Image.open(p).convert("RGB")
    return np.asarray(im.resize((w, round(im.height * w / im.width)), Image.NEAREST if "mask" in p.name else Image.BILINEAR),
                      np.float32) / 255.0


def stats(d: Path, cid: str):
    f, m = d / f"{cid}.png", d / f"{cid}_mask.png"
    if not f.exists() or not m.exists():
        return None
    a, k = load(f), load(m)
    mask = (k[..., 0] > 0.9) & (k[..., 1] < 0.15) & (k[..., 2] > 0.9)
    mask = ndimage.binary_erosion(mask, iterations=2)
    if mask.sum() < 50:
        return {"px": int(mask.sum())}
    px = a[mask]
    y = (0.2126 * px[:, 0] + 0.7152 * px[:, 1] + 0.0722 * px[:, 2]) * 100
    mx, mn = px.max(1), px.min(1)
    sat = np.where(mx > 1e-6, (mx - mn) / np.maximum(mx, 1e-6), 0) * 100
    return {"px": int(mask.sum()), "share": round(float(mask.mean() * 100), 2), "p50": round(float(np.median(y)), 1),
            "sigma": round(float(y.std()), 2), "r_b": round(float((px[:, 0] - px[:, 2]).mean() * 100), 1),
            "sat": round(float(np.median(sat)), 1)}


if __name__ == "__main__":
    args = sys.argv[1:]
    out = None
    if "--json" in args:
        i = args.index("--json")
        out = args[i + 1]
        args = args[:i] + args[i + 2:]
    d = Path(args[0])
    ids = args[1:] or IDS
    res = {cid: stats(d, cid) for cid in ids}
    for k, v in res.items():
        print(f"{d.name:16s} {k:26s} {v}")
    if out:
        Path(out).write_text(json.dumps(res, indent=1))
