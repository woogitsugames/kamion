"""ADR 0220: runs of edge-line classes (lines.py output) per side + line spacing statistics.

    uv run --project tools/worldgen python artifacts/dk65-k1-0220/tools/runs.py LINES.json [LINES.json ...]
"""
import json
import sys

import numpy as np


def main():
    recs = []
    for f in sys.argv[1:]:
        recs += json.load(open(f))
    recs.sort(key=lambda r: r["km"])
    for side in ("L", "P"):
        runs, cur = [], None
        for r in recs:
            c = r[side]["cls"]
            c = {"none?": "none", "mixed": "dashed?"}.get(c, c)
            if cur and cur[2] == c and abs(r["km"] - cur[1] - 0.01) < 0.006:
                cur[1] = r["km"]
            else:
                if cur:
                    runs.append(cur)
                cur = [r["km"], r["km"], c]
        runs.append(cur)
        print(side, " ".join(f"{a:.2f}-{b + 0.01:.2f}:{c}" for a, b, c in runs if c != "solid"))
    sp = np.array([r["spacing"] for r in recs if r.get("spacing") and r["L"]["cls"] in ("solid", "dashed")
                   and r["P"]["cls"] in ("solid", "dashed")])
    print("spacing n=%d median %.2f p10 %.2f p90 %.2f" % (len(sp), np.median(sp), np.percentile(sp, 10), np.percentile(sp, 90)))


if __name__ == "__main__":
    main()
