"""stats_cmp.py <before stats.txt> <after stats.txt> [prefixes,...]: drawsEst / trisK per camera, deltas (ADR 0110 budget)."""
import re, sys
def load(p):
    out = {}
    for ln in open(p, encoding="utf-8"):
        m = re.match(r"(\S+): objects=(\d+) drawsEst=(\d+) shadowDrawsEst=(\d+) trisK=(\d+)", ln)
        if m:
            out[m.group(1)] = (int(m.group(3)), int(m.group(5)), int(m.group(2)))
    return out
a, b = load(sys.argv[1]), load(sys.argv[2])
pref = tuple(sys.argv[3].split(",")) if len(sys.argv) > 3 else ("",)
worst_d = worst_t = None
print(f"{'camera':34s} draws b->a   d    tris(k) b->a    %")
for k in sorted(a):
    if k not in b or not k.startswith(pref):
        continue
    dd, dt = b[k][0] - a[k][0], (b[k][1] - a[k][1]) / max(a[k][1], 1) * 100
    print(f"{k:34s} {a[k][0]:5d} {b[k][0]:5d} {dd:+4d}   {a[k][1]:5d} {b[k][1]:5d} {dt:+6.1f}")
    worst_d = max(worst_d or -9999, dd); worst_t = max(worst_t or -9999, dt)
print("max draws delta", worst_d, "max tris delta %", None if worst_t is None else round(worst_t, 1))
