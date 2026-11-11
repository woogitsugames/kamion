import re, sys, pathlib
A = pathlib.Path(r"C:\Users\matma\Documents\Claude\kamion\artifacts")
W = pathlib.Path("artifacts/integration-s9/merged")
def parse(p):
    h = {}
    for l in pathlib.Path(p).read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"(\S+): objects=(\d+) drawsEst=(\d+) shadowDrawsEst=(\d+) trisK=(\d+)", l)
        if m: h[m[1]] = (int(m[3]), int(m[5]), int(m[4]))
    return h
new = parse(W / "Low-overcast/stats-main.txt")
base = parse(A / "buildings-r11/base/Low-overcast/stats.txt")
r3 = parse(A / "buildings-r11/r3/Low-overcast/stats.txt")
out = ["| kamera | draws | tris k | draws 0091-r3 | tris k r3 | d draws % | d tris % | draws przed 0091 |", "|---|---|---|---|---|---|---|---|"]
sd = st = od = ot = 0
for k in sorted(new):
    n = new[k]; o = r3.get(k); b = base.get(k)
    if o:
        sd += n[0]; st += n[1]; od += o[0]; ot += o[1]
        out.append(f"| {k} | {n[0]} | {n[1]} | {o[0]} | {o[1]} | {100*(n[0]-o[0])/o[0]:+.1f} | {100*(n[1]-o[1])/max(o[1],1):+.1f} | {b[0] if b else '-'} |")
    else:
        out.append(f"| {k} | {n[0]} | {n[1]} | - | - | - | - | - |")
out.append(f"| SUMA (wspolne) | {sd} | {st} | {od} | {ot} | {100*(sd-od)/od:+.1f} | {100*(st-ot)/ot:+.1f} | |")
pathlib.Path("artifacts/integration-s9/stats-low-compare.md").write_text("\n".join(out), encoding="utf-8")
print("\n".join(out)); print(len(new), len(r3), len(base))
