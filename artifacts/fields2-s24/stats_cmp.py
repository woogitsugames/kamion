import re, sys
from pathlib import Path
R = Path("artifacts/fields2-s24/vqa")
def read(p):
    out = {}; cam = None
    for ln in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = re.match(r"^(\S+): objects=(\d+) drawsEst=(\d+) .*trisExact=(\d+)", ln)
        if m: cam = m.group(1); out[cam] = {"draws": int(m.group(3)), "tris": int(m.group(4))}; continue
        m = re.search(r"instanced \(props\+trees\): draws (\d+), instances (\d+), .*trianglesExact (\d+), shadowCasterDraws (\d+)", ln)
        if m and cam: out[cam].update(idraws=int(m.group(1)), inst=int(m.group(2)), itris=int(m.group(3)), sdraws=int(m.group(4)))
    return out
for t in ("knyszyn-w", "dk65-07"):
    b, a = read(R / f"before/{t}-clear/stats.txt"), read(R / f"after/{t}-clear/stats.txt")
    print(f"## {t} (clear; before -> after)")
    print("| kamera | trójkąty siatek | draw calle siatek | instancje | draw calle inst. | trójkąty inst. |")
    print("|---|---|---|---|---|---|")
    for c in a:
        if c not in b: continue
        x, y = b[c], a[c]
        print(f"| `{c}` | {x['tris']} -> {y['tris']} ({y['tris']-x['tris']:+d}) | {x['draws']} -> {y['draws']} | {x.get('inst')} -> {y.get('inst')} | {x.get('idraws')} -> {y.get('idraws')} | {x.get('itris')} -> {y.get('itris')} ({y.get('itris',0)-x.get('itris',0):+d}) |")
