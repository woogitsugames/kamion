"""ADR 0220: edge lines on a straightened orthophoto strip (strip.py): position, spacing, solid / dashed per 10 m.

    uv run --project tools/worldgen python artifacts/dk65-k1-0220/tools/lines.py STRIP.npz OUT.json

Per 10 m block (rows = 0.1 m of chainage): the column profile (85th percentile over the block) gives the line peaks
in the windows L = t in [+2.3, +4.6] m, P = t in [-4.6, -2.3] m and the centre line in [-1.2, +1.2] m (t > 0 = left of
the direction of growing km). Per row, a line pixel is "paint" when it is >= DELTA grey levels above the asphalt
next to it (median of t +-0.35...0.8 m from the peak, the side towards the axis); duty = share of paint rows.
Class per block: solid (duty >= 0.80), dashed (0.20...0.80 with >= 3 paint runs), none (< 0.20 and the asphalt is lit),
shade (asphalt darker than SHADE: tree shadow, not readable). WORKING_VALUE thresholds, checked on the sheets.
"""
import json
import sys

import numpy as np

DELTA = 22.0
SHADE = 70.0
BLOCK = 100          # rows = 10 m


def peak(prof, t, lo, hi):
    m = (t >= lo) & (t <= hi)
    if not m.any():
        return None
    i = np.argmax(np.where(m, prof, -1))
    # prominence over the 1 m around it
    win = (np.abs(t - t[i]) > 0.3) & (np.abs(t - t[i]) < 1.0)
    prom = prof[i] - np.median(prof[win])
    return float(t[i]), float(prom)


def main():
    z = np.load(sys.argv[1])
    G = z["g"].astype(float)
    s0, res, half = float(z["s0"]), float(z["res"]), float(z["half"])
    t = half - np.arange(G.shape[1]) * res
    out = []
    for b0 in range(0, G.shape[0] - BLOCK + 1, BLOCK):
        B = G[b0:b0 + BLOCK]
        prof = np.percentile(B, 85, axis=0)
        rec = {"km": round((s0 + b0 * res) / 1000.0, 3)}
        for name, lo, hi in (("L", 2.3, 4.6), ("P", -4.6, -2.3), ("C", -1.2, 1.2)):
            pk = peak(prof, t, lo, hi)
            if pk is None or pk[1] < 12:
                rec[name] = {"cls": "none?", "t": None}
                continue
            tc, prom = pk
            j = int(round((half - tc) / res))
            col = B[:, max(j - 1, 0):j + 2].max(axis=1)
            inner = -1 if tc > 0 else 1         # towards the axis
            k0, k1 = sorted((j + inner * int(0.35 / res), j + inner * int(0.8 / res)))
            bg = np.median(B[:, max(k0, 0):k1 + 1], axis=1)
            paint = (col - bg) >= DELTA
            duty = float(paint.mean())
            runs = int(np.sum(np.diff(paint.astype(int)) == 1)) + int(paint[0])
            lit = float(np.median(bg))
            if lit < SHADE:
                cls = "shade"
            elif duty >= 0.80:
                cls = "solid"
            elif duty >= 0.20 and runs >= 3:
                cls = "dashed"
            elif duty < 0.20:
                cls = "none"
            else:
                cls = "mixed"
            rec[name] = {"cls": cls, "t": round(tc, 2), "duty": round(duty, 2), "runs": runs, "prom": round(prom, 1),
                         "bg": round(lit, 0)}
        if rec["L"].get("t") is not None and rec["P"].get("t") is not None:
            rec["spacing"] = round(rec["L"]["t"] - rec["P"]["t"], 2)
        out.append(rec)
    json.dump(out, open(sys.argv[2], "w"), indent=0)
    for r in out:
        print(r["km"], r.get("spacing"), *(f"{k}:{r[k]['cls']}:{r[k].get('t')}:{r[k].get('duty')}" for k in ("L", "C", "P")))


if __name__ == "__main__":
    main()
