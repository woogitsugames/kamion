"""Low-tier budget on the control cameras: stats.txt of two rounds (editor estimate, before SRP batching).
    python budget.py <base Low dir> <round Low dir> [--all]"""
import re, sys
from pathlib import Path

def load(d):
    out = {}
    for ln in (Path(d) / "stats.txt").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(\S+): objects=(\d+) drawsEst=(\d+) shadowDrawsEst=(\d+) trisK=(\d+)", ln)
        if m:
            out[m.group(1)] = (int(m.group(3)), int(m.group(5)))
    return out

a, b = load(sys.argv[1]), load(sys.argv[2])
skip = {"r10_hall_1", "r10_shed_2"}          # cameras moved in ADR 0094
rows = [(c, a[c][0], b[c][0], a[c][1], b[c][1]) for c in a if c in b and c not in skip]
sd0, sd1 = sum(r[1] for r in rows), sum(r[2] for r in rows)
st0, st1 = sum(r[3] for r in rows), sum(r[4] for r in rows)
print(f"{len(rows)} cameras: draws {sd0} -> {sd1} ({100 * (sd1 / sd0 - 1):+.1f} %), tris {st0}k -> {st1}k ({100 * (st1 / st0 - 1):+.1f} %)")
worst_d = sorted(rows, key=lambda r: -(r[2] / r[1]))
worst_t = sorted(rows, key=lambda r: -(r[4] / max(r[3], 1)))
print("draws worst:", ", ".join(f"{r[0]} {r[1]}->{r[2]} ({100 * (r[2] / r[1] - 1):+.1f} %)" for r in worst_d[:5]))
print("draws best: ", ", ".join(f"{r[0]} {r[1]}->{r[2]} ({100 * (r[2] / r[1] - 1):+.1f} %)" for r in worst_d[-4:]))
print("tris worst: ", ", ".join(f"{r[0]} {r[3]}k->{r[4]}k ({100 * (r[4] / max(r[3], 1) - 1):+.1f} %)" for r in worst_t[:5]))
print("draws > 400:", sum(r[1] > 400 for r in rows), "->", sum(r[2] > 400 for r in rows))
for c in ("dk8-dk19-exit", "r10_fence_1", "putry-above", "r10_block_1", "r10_block_2", "r10_block_3", "r10_block_5", "r10_house_1", "r10_house_2"):
    r = next((r for r in rows if r[0] == c), None)
    if r:
        print(f"  {c}: draws {r[1]} -> {r[2]}, tris {r[3]}k -> {r[4]}k")
if "--all" in sys.argv:
    for r in rows:
        print(" ", r)
