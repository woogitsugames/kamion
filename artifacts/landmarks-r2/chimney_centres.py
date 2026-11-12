"""Locate the two painted shafts on clean red bands in the resized reference."""
import json
from pathlib import Path

import numpy as np
from PIL import Image

out = Path(__file__).resolve().parent
root = out.parents[1]
source = root / "Data/raw/refs/commons/cmFile_20200711_073128_Elektrociep_ownia_Bia_ystok.jpg.jpg"
with Image.open(source) as opened:
    image = np.asarray(opened.convert("RGB"), dtype=np.int16)
assert image.shape[:2] == (2160, 3840)
rows = []
for name, box in (("left", (2876, 505, 3048, 545)), ("right", (3560, 280, 3764, 330))):
    x0, y0, x1, y1 = box
    crop = image[y0:y1, x0:x1]
    mask = (crop[:, :, 0] - crop[:, :, 1] > 10) & (crop[:, :, 0] - crop[:, :, 2] > 12)
    centres, widths = [], []
    for line in mask:
        indices = np.flatnonzero(line)
        runs = np.split(indices, np.flatnonzero(np.diff(indices) > 1) + 1)
        run = max(runs, key=len)
        if len(run) >= 30:
            centres.append(x0 + (run[0] + run[-1]) / 2)
            widths.append(len(run))
    assert len(centres) > (y1 - y0) * .8, name
    rows.append(dict(side=name, sampled_box=box, rows_used=len(centres),
                     centre_x_median=float(np.median(centres)), width_median=float(np.median(widths))))
result = dict(source=str(source.relative_to(root)), source_size=[3840, 2160],
              method="Largest contiguous red-paint run in each row: R-G>10, R-B>12, at least 30 px; fixed clean band window",
              status="Measured screen centres on a resized photo; pose and material identity remain UNVERIFIED", rows=rows)
(out / "chimney-centres.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
