"""patch_lum.py img name=x0,y0,x1,y1 ...: mean sRGB and linear luminance of image boxes, and ratios to the first box."""
import sys
import numpy as np
from PIL import Image
im = np.asarray(Image.open(sys.argv[1]).convert("RGB"), float) / 255.0
lin = np.where(im <= 0.04045, im / 12.92, ((im + 0.055) / 1.055) ** 2.4)
ref = None
for a in sys.argv[2:]:
    name, box = a.split("=")
    x0, y0, x1, y1 = (int(v) for v in box.split(","))
    p = lin[y0:y1, x0:x1].reshape(-1, 3).mean(0)
    s = im[y0:y1, x0:x1].reshape(-1, 3).mean(0) * 255
    L = float(p @ [0.2126, 0.7152, 0.0722])
    ref = ref or L
    print(f"{name:10s} sRGB {s[0]:5.0f} {s[1]:5.0f} {s[2]:5.0f}  lin {p[0]:.3f} {p[1]:.3f} {p[2]:.3f}  Y {L:.3f}  /{sys.argv[2].split('=')[0]} {L / ref:.2f}  r/b {p[0] / max(p[2], 1e-6):.2f}")
