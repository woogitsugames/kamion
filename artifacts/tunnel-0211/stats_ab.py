"""A/B of visual-qa stats.txt: python stats_ab.py <A dir> <B dir> -> per camera drawsEst / trisK"""
import re, sys
from pathlib import Path
def load(d):
    out = {}
    for line in (Path(d) / "stats.txt").read_text(encoding="utf-8").splitlines():
        m = re.match(r"(\S+): objects=\d+ drawsEst=(\d+) shadowDrawsEst=(\d+) trisK=(\d+)", line)
        if m: out[m[1]] = (int(m[2]), int(m[3]), int(m[4]))
    return out
A, B = load(sys.argv[1]), load(sys.argv[2])
keys = [k for k in B if k in A and (k.startswith(("route", "underpass", "roundabout", "produkcyjna", "collector", "tertiary")))]
keys += [k for k in B if k not in A]
print(f"{'camera':36s} {'draws A':>8s} {'draws B':>8s} {'shadow A':>9s} {'shadow B':>9s} {'trisK A':>8s} {'trisK B':>8s}")
for k in keys:
    a = A.get(k, ("-", "-", "-")); b = B[k]
    print(f"{k:36s} {a[0]!s:>8s} {b[0]!s:>8s} {a[1]!s:>9s} {b[1]!s:>9s} {a[2]!s:>8s} {b[2]!s:>8s}")
