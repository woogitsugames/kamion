"""Road paint vs asphalt contrast from visual-QA frames (review r6 W-H6, ADR 0049 addendum).

For every <id>.png that has a <id>_mask.png (visual-qa.ps1 -Mask ':marking_white', paint slots flat magenta):
  paint   = mask pixels, eroded by 2 px (no edge blend with the asphalt), lower 60 % of the frame (near road);
  asphalt = a ring 4..14 px around the paint (dilated mask minus the paint, minus anything saturated > 0.25 or
            magenta in the mask render) - i.e. the asphalt the eye compares the line with.
Display luma Y' = Rec.709 weights on the sRGB-encoded 0..255 values (the review's "luminancja wyswietlania").
Reports per frame and pooled: paint median / p95 / max-channel p99 (sRGB), asphalt median, ratio = paint/asphalt
median Y' (display) and the linear-light ratio.
Usage: uv run --project tools/worldgen python scripts/paint-contrast.py <dir> [<dir> ...] [--json out.json]
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


def srgb_to_lin(v):
    v = v / 255.0
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)


def measure(img_path: Path, mask_path: Path):
    im = np.asarray(Image.open(img_path).convert("RGB")).astype(np.float64)
    mk = np.asarray(Image.open(mask_path).convert("RGB")).astype(np.int32)
    if mk.shape != im.shape:
        return None
    h = im.shape[0]
    magenta = (mk[..., 0] > 200) & (mk[..., 1] < 60) & (mk[..., 2] > 200)
    rows = np.zeros(magenta.shape, bool)
    rows[int(h * 0.4):, :] = True
    paint = ndimage.binary_erosion(magenta, iterations=2) & rows
    ring = ndimage.binary_dilation(magenta, iterations=14) & ~ndimage.binary_dilation(magenta, iterations=4) & rows
    mx = im.max(-1)
    mn = im.min(-1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
    ring &= sat < 0.25
    if paint.sum() < 200 or ring.sum() < 200:
        return None
    y = im[..., 0] * 0.2126 + im[..., 1] * 0.7152 + im[..., 2] * 0.0722
    yl = srgb_to_lin(im) @ np.array([0.2126, 0.7152, 0.0722])
    pm, am = float(np.median(y[paint])), float(np.median(y[ring]))
    return {
        "paint_px": int(paint.sum()), "asphalt_px": int(ring.sum()),
        "paint_median": round(pm, 1), "paint_p95": round(float(np.percentile(y[paint], 95)), 1),
        "paint_maxch_p99": round(float(np.percentile(mx[paint], 99)), 1),
        "asphalt_median": round(am, 1),
        "ratio_display": round(pm / am, 3),
        "ratio_linear": round(float(np.median(yl[paint]) / np.median(yl[ring])), 3),
    }


def main():
    args = sys.argv[1:]
    out = None
    if "--json" in args:
        i = args.index("--json")
        out = Path(args[i + 1])
        del args[i:i + 2]
    res = {}
    for d in map(Path, args):
        per = {}
        seen = set()
        for m in sorted(d.glob("*_mask.png")):
            img = m.with_name(m.name.replace("_mask.png", ".png"))
            key = img.stem.replace("-", "_")          # control camera and gate3 camera of the same id
            if img.exists() and key not in seen:
                seen.add(key)
                r = measure(img, m)
                if r:
                    per[img.stem] = r
        if per:
            ratios = [v["ratio_display"] for v in per.values()]
            per["_summary"] = {
                "frames": len(ratios),
                "ratio_display_median": round(float(np.median(ratios)), 3),
                "ratio_display_min": round(min(ratios), 3),
                "paint_median_max": max(v["paint_median"] for k, v in per.items() if not k.startswith("_")),
                "paint_maxch_p99_max": max(v["paint_maxch_p99"] for k, v in per.items() if not k.startswith("_")),
                "asphalt_median_median": round(float(np.median([v["asphalt_median"] for k, v in per.items()
                                                                  if not k.startswith("_")])), 1),
            }
        res[str(d)] = per
        print(f"== {d}")
        for k, v in per.items():
            print(f"  {k:32s} {v}")
    if out:
        out.write_text(json.dumps(res, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
