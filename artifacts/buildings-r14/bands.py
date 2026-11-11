"""Band spectrum of a tiling albedo map: std of the luminance (relative to the mean, %) per wavelength band in metres.
    python bands.py <BaseColor.png> <tile_m>"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
a = np.asarray(Image.open(sys.argv[1]).convert("RGB"), float) / 255.0
L = float(sys.argv[2])
lin = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4) @ [0.2126, 0.7152, 0.0722]
px = L / lin.shape[1]
m = lin.mean()
edges = [0.0, 0.01, 0.03, 0.08, 0.2, 0.5, 1e9]      # wavelength ~ 2.5 sigma
prev = lin
out = []
for lo, hi in zip(edges, edges[1:]):
    low = ndimage.gaussian_filter(lin, hi / px / 2.5, mode="wrap") if hi < 1e8 else np.full_like(lin, m)
    out.append(f"{lo:g}-{hi:g} m: {100 * (prev - low).std() / m:.2f} %")
    prev = low
print(f"mean {m:.3f} total {100 * lin.std() / m:.2f} % | " + " | ".join(out))
