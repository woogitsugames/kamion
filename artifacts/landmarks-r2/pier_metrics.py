"""Fixed screen ROI for the same broad pier face before/after, no reflectance claim."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

root = Path(__file__).resolve().parent
phase = sys.argv[1] if len(sys.argv) > 1 else "before"
out = root / "review" / f"pier-{phase}"
out.mkdir(parents=True, exist_ok=True)
rois = {"ochre_broad": [1544, 540, 1560, 590], "bare_chamfer": [1517, 540, 1527, 590],
        "ochre_side": [1496, 540, 1505, 590], "mixed_face_band": [1496, 520, 1560, 590],
        "ochre_lower": [1545, 674, 1560, 689]}
rows = []
for condition in ("Low-overcast", "Low-clear", "High-overcast", "High-clear"):
    with Image.open(root / phase / condition / "dk8-under-span.png") as source:
        image = source.convert("RGB")
    image.crop((1490, 470, 1590, 740)).save(out / f"{condition}-column.png")
    for name, box in rois.items():
        values = np.asarray(image.crop(box), dtype=float)
        y = values @ np.array([.2126, .7152, .0722])
        rows.append(dict(condition=condition, roi=name, box=box,
                         RGB_p50=np.median(values, axis=(0, 1)).tolist(),
                         Y_p50=float(np.median(y)), Y_std=float(y.std())))
(root / f"pier-metrics-{phase}.json").write_text(json.dumps(dict(
    camera="dk8-under-span", coordinate_status="Fixed pixel boxes; inspect crops to validate face selection",
    note="sRGB pixels under QA lighting, not measured material reflectance", rows=rows), indent=2), encoding="utf-8")
print(json.dumps(rows, indent=2))
