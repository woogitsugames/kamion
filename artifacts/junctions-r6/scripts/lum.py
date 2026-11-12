"""lum.py <image> [--crop1440] [--out annotated.jpg] name=x0,y0,x1,y1 ...: median sRGB luminance (0.2126 R + 0.7152 G + 0.0722 B on
8-bit values, as in REVIEW s10-0117) of rectangles; --crop1440 = centre-crop a 2340x1080 render to 1440x1080 first (photo
frame). Prints name, median, p10-p90 and ratios to the rectangle called `asphalt` when present."""
import sys
import numpy as np
from PIL import Image, ImageDraw
a = sys.argv[1:]
im = Image.open(a[0]).convert("RGB")
if "--crop1440" in a:
    w, h = im.size
    im = im.crop(((w - 1440) // 2, 0, (w - 1440) // 2 + 1440, h))
elif im.size != (1440, 1080) and "--raw" not in a:
    im = im.resize((1440, 1080), Image.LANCZOS)
out = a[a.index("--out") + 1] if "--out" in a else None
A = np.asarray(im).astype(float)
L = 0.2126 * A[..., 0] + 0.7152 * A[..., 1] + 0.0722 * A[..., 2]
res = {}
d = ImageDraw.Draw(im)
for s in a[1:]:
    if "=" not in s:
        continue
    name, r = s.split("=")
    x0, y0, x1, y1 = (int(v) for v in r.split(","))
    v = L[y0:y1, x0:x1]
    res[name] = (np.median(v), np.percentile(v, 10), np.percentile(v, 90))
    d.rectangle([x0, y0, x1, y1], outline=(255, 0, 0)); d.text((x0, max(0, y0 - 11)), name, fill=(255, 255, 0))
ref = res.get("asphalt", (None,))[0]
print(a[0].replace("\\", "/").split("/")[-2] + "/" + a[0].replace("\\", "/").split("/")[-1])
for k, (m, p10, p90) in res.items():
    print(f"  {k:12s} {m:6.1f}  p10 {p10:5.1f} p90 {p90:5.1f}" + (f"  x asphalt {m / ref:4.2f}" if ref else ""))
if out:
    im.save(out, quality=88)
