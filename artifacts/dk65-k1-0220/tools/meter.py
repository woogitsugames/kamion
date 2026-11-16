"""ADR 0220: paint state of one edge line per metre of chainage (# solid, - broken, . no paint) on a strip.

    uv run --project tools/worldgen python artifacts/dk65-k1-0220/tools/meter.py STRIP.npz KM_A KM_B L|P
"""
import sys

import numpy as np

z = np.load(sys.argv[1])
G = z["g"].astype(float)
s0, res, half = float(z["s0"]), float(z["res"]), float(z["half"])
ka, kb, side = float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
r0, r1 = int((ka * 1000 - s0) / res), int((kb * 1000 - s0) / res)
B = G[r0:r1]
t = half - np.arange(G.shape[1]) * res
lo, hi = (2.3, 4.6) if side == "L" else (-4.6, -2.3)
prof = np.percentile(B, 85, axis=0)
m = (t >= lo) & (t <= hi)
j = int(np.argmax(np.where(m, prof, -1)))
inner = -1 if t[j] > 0 else 1
k0, k1 = sorted((j + inner * 3, j + inner * 8))
p = (B[:, j - 1:j + 2].max(1) - np.median(B[:, k0:k1 + 1], axis=1)) >= 22
s = "".join("#" if p[i:i + 10].mean() > 0.8 else ("-" if p[i:i + 10].mean() > 0.2 else ".") for i in range(0, len(p), 10))
print(f"{side} km {ka:.3f}..{kb:.3f} t={t[j]:.2f}")
for i in range(0, len(s), 50):
    print(f"  {ka + i / 1000:.3f} {s[i:i + 50]}")
