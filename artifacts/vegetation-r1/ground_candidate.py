"""Preview only: mask hypothesis, not a Unity render or a measured visual improvement."""
import json
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/worldgen"))
from streetscape.foliage_policy import metric_patch_field

east, north = np.arange(-100., 101.), np.arange(100., -101., -1.)
old_dry = metric_patch_field(east, north, 6.0, 881)
large = metric_patch_field(east, north, 8.0, 881)
small = metric_patch_field(east, north, 2.5, 883)
# Blend correlated patch scales, then widen the useful middle range. These are
# art values, not local measurements of soil moisture or maintenance practice.
dry = np.clip((.8*large + .2*small - .5)*2.4 + .5, 0, 1)
old = [old_dry*.18, old_dry*.18, .55+old_dry*.45]
new = [.06+dry*.40, .08+dry*.84, .25+dry*.75]
labels = ["mapped maintained lawn", "roadside verge, outside mapped lawn", "unmanaged ground"]
sheet = Image.new("RGB", (960, 3*190), "#222222")
draw = ImageDraw.Draw(sheet)
measurements = {}
for row, label in enumerate(labels):
    measurements[label] = {}
    for col, (stage, values) in enumerate((("before", old[row]), ("candidate", new[row]))):
        values = ndimage.gaussian_filter(values, 1.5)
        measurements[label][stage] = dict(std=float(values.std()),
            p10_p50_p90=np.percentile(values, [10, 50, 90]).tolist())
        # Shared neutral scale: same value always gives the same grey.
        im = Image.fromarray(np.uint8(values*255)).convert("RGB").resize((440, 160))
        sheet.paste(im, (col*480, row*190+25))
        draw.text((col*480+4, row*190+4), stage+": "+label, fill="white")
sheet.save(Path(__file__).with_name("ground-mask-hypothesis.jpg"), quality=92)
Path(__file__).with_name("ground-mask-hypothesis.json").write_text(
    json.dumps({"status":"WORKING_VALUE synthetic 200m plane; not rendered validation", "masks":measurements}, indent=2)+"\n")
print(json.dumps(measurements, indent=2))
