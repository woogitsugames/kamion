"""seams-fix-s23: painted lines along a road across a tile seam, read off the generated chunk GLBs (node `markings`).

For a seam point sp (EPSG:2180) and travel direction d (unit, from tile A into tile B): cross-sections every STEP m from
-RANGE to +RANGE m along d (negative = tile A, positive = tile B), lateral -LAT_M..+LAT_M (left of travel = +), 0.02 m;
per section the painted-line runs (centre, width). Prints one row per section and returns the list; a line that stops
at the seam shows as a lateral present on one side for the whole range and absent on the other.
    uv run --project tools/worldgen python tools/worldgen/qa/seam_marking_strip.py <tileA> <tileB> <E> <N> <dE> <dN> [range]
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import seam_section as S  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
STEP = 0.5
LAT_M = 8.0


def strip(a, b, sp, d, rng=30.0):
    sp = np.asarray(sp, float); d = np.asarray(d, float); d = d / np.linalg.norm(d)
    n = np.array([-d[1], d[0]])
    lat = np.arange(-LAT_M, LAT_M + 1e-4, 0.02)
    rows = []
    for t, sign in ((a, -1.0), (b, 1.0)):
        o, _, _ = S.region(ROOT, t)
        loc = sp - np.array([o["x"], o["y"]])
        mk = S.tris(ROOT, t, "markings", loc, rad=rng + 10.0)
        road = S.tris(ROOT, t, "road", loc, rad=rng + 10.0)
        asp = [v for k, v in road.items() if k.startswith("road_asphalt")]
        asp = np.concatenate(asp) if asp else np.zeros((0, 3, 3))
        M = np.concatenate(list(mk.values())) if mk else np.zeros((0, 3, 3))
        for x in np.arange(STEP, rng + 1e-6, STEP):
            c = loc + sign * x * d
            pts = c[None, :] + lat[:, None] * n[None, :]
            zm = S.locate(M, pts)
            za = S.locate(asp, pts)
            lines = [(round((x0 + x1) / 2, 2), round(x1 - x0 + 0.02, 2)) for x0, x1 in S.runs(~np.isnan(zm), lat)]
            ar = [(round(x0, 2), round(x1, 2)) for x0, x1 in S.runs(~np.isnan(za), lat) if x1 - x0 > 1.0]
            rows.append({"tile": t, "along_m": round(float(sign * x), 2), "lines": lines, "asphalt": ar})
    rows.sort(key=lambda r: r["along_m"])
    return rows


if __name__ == "__main__":
    a, b = sys.argv[1], sys.argv[2]
    E, N, dE, dN = map(float, sys.argv[3:7])
    rng = float(sys.argv[7]) if len(sys.argv) > 7 else 30.0
    for r in strip(a, b, (E, N), (dE, dN), rng):
        print(f"{r['tile']:>24} {r['along_m']:7.2f}  asph {r['asphalt']}  lines {r['lines']}")
