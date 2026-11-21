"""Budget table r0 -> rN from visual-qa stats.txt (editor estimate, before SRP batching). usage: budget.py rN > budget-rN.md"""
import re, sys
from pathlib import Path
A = Path(__file__).resolve().parent
R = sys.argv[1]
rx = re.compile(r"^(\S+): objects=(\d+) drawsEst=(\d+) shadowDrawsEst=(\d+) trisK=(\d+) trisExact=(\d+)")
rxi = re.compile(r"^\s+(\S+) instanced.*draws (\d+), instances (\d+), triangles .*trianglesExact (\d+)")


def load(p):
    out = {}
    if not p.exists():
        return out
    for ln in p.read_text(encoding="utf-8", errors="replace").splitlines():
        m = rx.match(ln)
        if m:
            out[m.group(1)] = {"draws": int(m.group(3)), "tris": int(m.group(6)), "idraws": 0, "itris": 0}
        m = rxi.match(ln)
        if m and m.group(1) in out:
            out[m.group(1)].update(idraws=int(m.group(2)), itris=int(m.group(4)))
    return out


print(f"# Budżet kamer r0 -> {R} (visual-qa stats.txt, edytor, 1920x1080, szacunek przed SRP batching)\n")
for tier, lit in (("High", "clear"), ("Low", "clear")):
    print(f"## {tier} {lit}\n\n| kafel | kamera | draws r0 | draws {R} | Δ | tris r0 (tys.) | tris {R} (tys.) | Δ % | inst. tris r0 -> {R} (tys.) |\n|---|---|---|---|---|---|---|---|---|")
    tot = [0, 0, 0, 0]
    for t in ("tykocin", "dk65-07", "knyszyn-w"):
        a, b = load(A / "r0" / f"{t}-{tier}-{lit}" / "stats.txt"), load(A / R / f"{t}-{tier}-{lit}" / "stats.txt")
        for cam in sorted(set(a) & set(b)):
            x, y = a[cam], b[cam]
            tot = [tot[0] + x["draws"], tot[1] + y["draws"], tot[2] + x["tris"], tot[3] + y["tris"]]
            print(f"| {t} | {cam} | {x['draws']} | {y['draws']} | {y['draws'] - x['draws']:+d} | {x['tris'] / 1e3:.0f} | {y['tris'] / 1e3:.0f} | "
                  f"{100.0 * (y['tris'] - x['tris']) / max(x['tris'], 1):+.1f} | {x['itris'] / 1e3:.0f} -> {y['itris'] / 1e3:.0f} |")
    if tot[2]:
        print(f"| **suma** | | {tot[0]} | {tot[1]} | {tot[1] - tot[0]:+d} | {tot[2] / 1e3:.0f} | {tot[3] / 1e3:.0f} | {100.0 * (tot[3] - tot[2]) / tot[2]:+.1f} | |")
    print()
