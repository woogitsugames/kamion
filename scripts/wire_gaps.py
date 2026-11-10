"""REVIEW r6 W-P0 acceptance: power-line continuity in the control renders.

Three renders of the same cameras (scripts/visual-qa.ps1 -Wires on|off|solid):
  expected path E = off - solid luminance > max(12, 0.2 * off)      (where a wire is in the frame)
  drawn wire    D = off - on luminance >= DRAWN_MIN levels (8-bit)  (what the player sees)
Per connected run of E (8-connected after a 1 px dilation), ordered along its major axis: a step (column or row) of
the run where E exists is covered when D has a pixel there; a gap = > 2 consecutive uncovered steps.
Reports gaps per 100 px of wire, coverage and contrast (levels darker than the frame without wires). A second count
(gaps_alpha) uses D = drawn darkening >= 10 % of the solid wire's darkening, i.e. the line is drawn with >= 10 % of
full opacity: it separates rendering breaks from a continuous wire that is merely < 3 levels over a dark background;
gaps_bright_bg counts gaps only where the background is sky / light (>= 100 levels).
Usage: uv run --project tools/worldgen --with scipy python scripts/wire_gaps.py <dir_on> <dir_off> <dir_solid> [cam ...]
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

DRAWN_MIN = 3


def lum(p):
    a = np.asarray(Image.open(p).convert("RGB")).astype(np.float32)
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def measure(on, off, solid):
    lo, lf, ls = lum(on), lum(off), lum(solid)
    E = (lf - ls) > np.maximum(12.0, 0.2 * lf)
    r = _gaps(E, (lf - lo) >= DRAWN_MIN, lf - lo)
    r["gaps_alpha"] = _gaps(E, (lf - lo) >= 0.1 * (lf - ls), lf - lo)["gaps_gt2px"]
    # against sky / light background only (off >= 100 levels): where a dark conductor must read as a line
    r["gaps_bright_bg"] = _gaps(E & (lf >= 100), (lf - lo) >= DRAWN_MIN, lf - lo)["gaps_gt2px"]
    return r


def _gaps(E, D, dark):
    lab, n = ndi.label(ndi.binary_dilation(E, iterations=1), structure=np.ones((3, 3)))
    total_len, gaps, contrast = 0, 0, []
    for k in range(1, n + 1):
        ys, xs = np.nonzero((lab == k) & E)
        if len(xs) < 12:
            continue
        horiz = (xs.max() - xs.min()) >= (ys.max() - ys.min())
        a = xs if horiz else ys
        m = int(a.max() - a.min() + 1)
        cov = np.zeros(m, bool)
        present = np.zeros(m, bool)
        present[a - a.min()] = True
        cov[a[D[ys, xs]] - a.min()] = True
        run = 0
        for c, p in zip(cov, present):
            if p and not c:
                run += 1
                continue
            if run > 2:
                gaps += 1
            run = 0
        if run > 2:
            gaps += 1
        total_len += int(present.sum())
        contrast += list(dark[ys, xs])
    c = np.asarray(contrast) if contrast else np.zeros(1)
    return {"wire_px": total_len, "gaps_gt2px": gaps, "gaps_per_100px": round(100.0 * gaps / max(total_len, 1), 3),
            "coverage_pct": round(100.0 * float((c >= DRAWN_MIN).mean()), 1),
            "contrast_p50": round(float(np.median(c)), 1), "contrast_p10": round(float(np.percentile(c, 10)), 1)}


def main():
    d_on, d_off, d_solid = (Path(x) for x in sys.argv[1:4])
    cams = sys.argv[4:] or sorted(p.stem for p in d_on.glob("*.png"))
    for cam in cams:
        f = [d / f"{cam}.png" for d in (d_on, d_off, d_solid)]
        if all(x.exists() for x in f):
            print(cam, json.dumps(measure(*f)))


if __name__ == "__main__":
    main()
