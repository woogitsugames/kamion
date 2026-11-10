"""Parapet run-off A/B on the control renders (visual-qa.ps1 -Runoff on|off, same cameras).

diff = luminance(off) - luminance(on) (> 0 where the streak layer darkens the wall). Per frame:
  px_ge3        pixels darkened by >= 3 levels (8-bit), i.e. visible streak area
  p99_dark      99th percentile of the darkening over those pixels (levels)
  vert_ratio    |d/dx| energy / |d/dy| energy of the diff (> 1: vertical structures = streaks, not blotches)
  top_share     share of streak pixels in the upper half of each streak column run (streaks hang from the coping)
Usage: uv run --project tools/worldgen python scripts/runoff_ab.py <dir_on> <dir_off> [cam ...]
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def lum(p):
    a = np.asarray(Image.open(p).convert("RGB")).astype(np.float32)
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def measure(on, off):
    d = lum(off) - lum(on)
    m = d >= 3
    gx = np.abs(np.diff(d, axis=1))[:-1, :]
    gy = np.abs(np.diff(d, axis=0))[:, :-1]
    vr = float(gx.sum() / max(gy.sum(), 1e-6))
    top, tot = 0, 0
    for x in np.nonzero(m.any(0))[0]:
        ys = np.nonzero(m[:, x])[0]
        w = d[ys, x]
        mid = 0.5 * (ys.min() + ys.max())
        top += float(w[ys <= mid].sum())
        tot += float(w.sum())
    return {"px_ge3": int(m.sum()), "p99_dark": round(float(np.percentile(d[m], 99)), 1) if m.any() else 0.0,
            "vert_ratio": round(vr, 2), "top_share": round(top / max(tot, 1e-6), 2)}


def main():
    d_on, d_off = Path(sys.argv[1]), Path(sys.argv[2])
    cams = sys.argv[3:] or sorted(p.stem for p in d_off.glob("*.png"))
    for cam in cams:
        a, b = d_on / f"{cam}.png", d_off / f"{cam}.png"
        if a.exists() and b.exists():
            print(cam, json.dumps(measure(a, b)))


if __name__ == "__main__":
    main()
