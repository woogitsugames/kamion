"""Compare the same baseline-selected crown pixels; avoid colour-selection bias."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]/"tools/worldgen"))
from streetscape.vegetation_metrics import foliage_mask

boxes = json.loads((HERE/"crown-rois-0109.json").read_text(encoding="utf-8-sig"))
results = {}


def read(path):
    image = Image.open(path).convert("RGB")
    image.thumbnail((960, 960))
    return np.array(image)


def summarize(values):
    return dict(p10=float(np.percentile(values, 10)), p50=float(np.percentile(values, 50)),
                p90=float(np.percentile(values, 90)), lt16_percent=float((values < 16).mean()*100))


for tier in ("Low", "High"):
    for light in ("overcast", "clear"):
        group = tier+"-"+light
        results[group] = {}
        for camera, rectangles in boxes.items():
            paths = [HERE/stage/group/(camera+".png") for stage in ("before", "after")]
            if not all(path.exists() for path in paths):
                continue
            before, after = map(read, paths)
            if before.shape != after.shape:
                raise ValueError("Frame dimensions differ: "+group+" "+camera)
            h, w = before.shape[:2]
            old, new = [], []
            for x0, y0, x1, y1 in rectangles:
                a = before[round(y0*h):round(y1*h), round(x0*w):round(x1*w)]
                b = after[round(y0*h):round(y1*h), round(x0*w):round(x1*w)]
                fixed = foliage_mask(a)
                old.append((a.astype(np.float32)@np.array([.2126, .7152, .0722], np.float32))[fixed])
                new.append((b.astype(np.float32)@np.array([.2126, .7152, .0722], np.float32))[fixed])
            a, b = np.concatenate(old), np.concatenate(new)
            if len(a) < 20:
                results[group][camera] = {"status":"insufficient baseline crown pixels"}
                continue
            results[group][camera] = dict(before=summarize(a), after=summarize(b), pixels=len(a),
                delta_p50=float(np.median(b)-np.median(a)), rois=rectangles,
                baseline_sha256=hashlib.sha256(paths[0].read_bytes()).hexdigest(),
                candidate_sha256=hashlib.sha256(paths[1].read_bytes()).hexdigest(),
                method="sRGB8 Rec709 at width <=960; same baseline foliage mask on both frames; not semantic segmentation")
(HERE/"crowns-fixed-mask-comparison.json").write_text(json.dumps(results, indent=2)+"\n", encoding="utf-8")
for group, rows in results.items():
    print(group, {camera: (round(r["before"]["p50"], 2), round(r["after"]["p50"], 2))
                  for camera, r in rows.items() if "before" in r})
