"""ADR 0220: dash / gap lengths of an edge line on a strip (strip.py) between two km, one side.

    uv run --project tools/worldgen python artifacts/dk65-k1-0220/tools/dashes.py STRIP.npz KM_A KM_B L|P
Line column = the brightest column of the 85th-percentile profile in t 2.3..4.6 m (L) / -4.6..-2.3 m (P); paint = >= 22
grey levels above the asphalt 0.35-0.8 m towards the axis; runs shorter than 0.3 m merged (noise).
"""
import sys

import numpy as np


def main():
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
    col = B[:, j - 1:j + 2].max(1)
    bg = np.median(B[:, k0:k1 + 1], axis=1)
    p = (col - bg) >= 22
    edges = np.flatnonzero(np.diff(p.astype(int))) + 1
    seg = np.split(p, edges)
    runs = [(bool(s[0]), len(s) * res) for s in seg if len(s)]
    dash = [L for v, L in runs[1:-1] if v and L >= 0.3]
    gap = [L for v, L in runs[1:-1] if not v and L >= 0.3]
    print(f"t={t[j]:.2f} dashes n={len(dash)} median {np.median(dash):.2f} gaps n={len(gap)} median {np.median(gap):.2f}")


if __name__ == "__main__":
    main()
