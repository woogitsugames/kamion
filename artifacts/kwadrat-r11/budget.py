"""Low-tier frame estimate before / after from the visual-qa stats.txt (ADR 0071 r11).
uv run --project tools/worldgen python artifacts/kwadrat-r11/budget.py <before dir> <after dir>"""
import re, sys
def read(p):
    out = {}
    for ln in open(p + "/stats.txt", encoding="utf-8"):
        m = re.match(r"(\S+): objects=(\d+) drawsEst=(\d+) shadowDrawsEst=(\d+) trisK=(\d+)", ln)
        if m:
            cam = m.group(1); out[cam] = {"draws": int(m.group(3)), "shadow": int(m.group(4)), "trisK": int(m.group(5))}
        m = re.match(r"\s+(\S+) editor frame time: ([\d,\.]+) ms", ln)
        if m: out[m.group(1)]["ms"] = float(m.group(2).replace(",", "."))
        m = re.match(r"\s+(\S+) instanced \(props\+trees\): draws (\d+), instances (\d+), triangles (\d+)k", ln)
        if m: out[m.group(1)].update(idraws=int(m.group(2)), inst=int(m.group(3)), itrisK=int(m.group(4)))
    return out
b, a = read(sys.argv[1]), read(sys.argv[2])
print(f"{'camera':20s} {'draws b/a':>12s} {'%':>6s} {'tris k b/a':>12s} {'%':>6s} {'ms b/a':>12s}")
tb = ta = db = da = 0
for c in sorted(b):
    x, y = b[c], a[c]
    d0, d1 = x["draws"] + x["idraws"], y["draws"] + y["idraws"]
    t0, t1 = x["trisK"] + x["itrisK"], y["trisK"] + y["itrisK"]
    db += d0; da += d1; tb += t0; ta += t1
    print(f"{c:20s} {d0:5d}/{d1:5d} {100*(d1-d0)/d0:+6.1f} {t0:5d}/{t1:5d} {100*(t1-t0)/t0:+6.1f} {x.get('ms',0):5.2f}/{y.get('ms',0):5.2f}")
print(f"{'SUM':20s} {db:5d}/{da:5d} {100*(da-db)/db:+6.1f} {tb:5d}/{ta:5d} {100*(ta-tb)/tb:+6.1f}")
