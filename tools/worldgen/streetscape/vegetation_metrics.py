"""ADR0088: crown-only sRGB p10/p50 and crushed-black coverage in fixed ROIs.

Use identical normalized rectangles before/after. The mask selects green foliage
and retains crushed canopy pixels, instead of dropping black leaves as 'not green'.
Rectangles are deliberately restricted to crowns: this is not a semantic model.
    uv run --project tools/worldgen tools/worldgen/streetscape/vegetation_metrics.py <directory> --out <json>
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROIS = {
    "dk8-dk19-exit": [[0., 0., .43, .40], [.70, 0., 1., .43]],
    "driver-andersa-to-putry": [[.49, .25, .92, .45]],
    "route-putry-approach": [[.75, .14, 1., .43]],
}


def foliage_mask(rgb):
    a = np.asarray(rgb, dtype=np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    y = a @ np.array([.2126, .7152, .0722], dtype=np.float32)
    green = (g >= r * .97) & (g >= b * .98) & (2*g-r-b > 1.5)
    return (green | (y < 16)) & (y < 160)


def measure(path, boxes):
    with Image.open(path) as image:
        image = image.convert("RGB")
        image.thumbnail((960, 960))
        a = np.asarray(image)
    h, w = a.shape[:2]
    samples, selected, pixels = [], [], 0
    for rect in boxes:
        x0, y0, x1, y1 = rect
        crop = a[round(y0*h):round(y1*h), round(x0*w):round(x1*w)]
        mask = foliage_mask(crop)
        y = crop.astype(np.float32) @ np.array([.2126, .7152, .0722], np.float32)
        selected.append(y[mask]); samples.append(y.ravel()); pixels += mask.size
    values, all_values = np.concatenate(selected), np.concatenate(samples)
    if len(values) < 20:
        return {"crown_pixels": len(values), "status": "insufficient crown pixels"}
    return {"crown_pixels": len(values), "roi_pixels": pixels,
            "mask_share_percent": round(len(values) / pixels * 100, 3),
            "crown_p10": round(float(np.percentile(values, 10)), 3),
            "crown_p50": round(float(np.percentile(values, 50)), 3),
            "crown_lt16_percent": round(float((values < 16).mean()*100), 3),
            "roi_lt16_percent": round(float((all_values < 16).mean()*100), 3),
            "source_sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
            "rois": boxes, "metric": "Rec709 on sRGB8, crown ROIs, width<=960"}


def directory(path, boxes=ROIS):
    result = {}
    for name, rectangles in boxes.items():
        p = Path(path) / (name if Path(name).suffix else name + ".png")
        if p.exists():
            result[name] = measure(p, rectangles)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--boxes", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    boxes = json.loads(args.boxes.read_text(encoding="utf-8")) if args.boxes else ROIS
    result = directory(args.directory, boxes)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=1))
