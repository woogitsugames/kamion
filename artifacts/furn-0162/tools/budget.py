"""ADR 0162: Low budget, baseline (main world) vs after, from visual-qa stats.txt (CPU estimates before SRP batching;
instanced props/trees reported separately). Usage: python budget.py <before dir> <after dir> [out.txt]"""
import re
import sys
from pathlib import Path

LINE = re.compile(r"^(\S+): objects=(\d+) drawsEst=(\d+) shadowDrawsEst=(\d+) trisK=(\d+)")
INST = re.compile(r"^\s+(\S+) instanced \(props\+trees\): draws (\d+), instances (\d+), triangles (\d+)k")


def read(d):
    out = {}
    for ln in (Path(d) / "stats.txt").read_text(encoding="utf-8").splitlines():
        m = LINE.match(ln)
        if m:
            out.setdefault(m[1], {}).update(draws=int(m[3]), shadow=int(m[4]), tris=int(m[5]))
        m = INST.match(ln)
        if m:
            out.setdefault(m[1], {}).update(idraws=int(m[2]), itris=int(m[4]))
    return out


b, a = read(sys.argv[1]), read(sys.argv[2])
rows = ["camera                               draws b>a (d)     trisK b>a (%)        shadow b>a  inst.draws b>a  inst.trisK b>a"]
worst_d, worst_t = (0, ""), (0.0, "")
for k in sorted(set(a) & set(b)):
    x, y = b[k], a[k]
    td = x["draws"] + x.get("idraws", 0)
    ta = y["draws"] + y.get("idraws", 0)
    tb, tt = x["tris"] + x.get("itris", 0), y["tris"] + y.get("itris", 0)
    pct = 100.0 * (tt - tb) / max(tb, 1)
    worst_d = max(worst_d, (ta - td, k))
    worst_t = max(worst_t, (pct, k))
    rows.append(f"{k:36s} {td:5d}>{ta:5d} ({ta - td:+4d})  {tb:5d}>{tt:5d} ({pct:+5.1f} %)  {x['shadow']:4d}>{y['shadow']:4d}"
                f"   {x.get('idraws', 0):4d}>{y.get('idraws', 0):4d}      {x.get('itris', 0):4d}>{y.get('itris', 0):4d}")
rows.append(f"cameras compared: {len(set(a) & set(b))}; max draws delta (regular + instanced): {worst_d[0]:+d} ({worst_d[1]}); "
            f"max tris delta: {worst_t[0]:+.1f} % ({worst_t[1]})")
txt = "\n".join(rows)
print(txt)
if len(sys.argv) > 3:
    Path(sys.argv[3]).write_text(txt + "\n", encoding="utf-8")
