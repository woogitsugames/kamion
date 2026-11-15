"""Luma (Rec.709 on sRGB codes, %) per frame: whole p50/p95 and the ground band (rows 55-95 %) p10/p50/p90 + p90/p10.
python lum.py <tag> -> <tag>/lum.tsv"""
import sys, glob, os
import numpy as np
from PIL import Image
tag = sys.argv[1]
rows = ["frame\tp50\tp95\tground_p10\tground_p50\tground_p90\tground_p90/p10"]
for f in sorted(glob.glob(f"{tag}/*/*.png")):
    a = np.asarray(Image.open(f).convert("RGB"), dtype=np.float32) / 255.0
    y = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    h = y.shape[0]
    g = y[int(h * .55):int(h * .95)]
    p = np.percentile(y, [50, 95]) * 100
    q = np.percentile(g, [10, 50, 90]) * 100
    rows.append(f"{os.path.relpath(f, tag)}\t{p[0]:.1f}\t{p[1]:.1f}\t{q[0]:.1f}\t{q[1]:.1f}\t{q[2]:.1f}\t{q[2]/max(q[0],.1):.2f}")
open(f"{tag}/lum.tsv", "w").write("\n".join(rows) + "\n")
print("\n".join(rows))
