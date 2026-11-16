"""ADR 0216: compare visual-qa stats.txt before/after (world cameras: not cab/truck/trailer/plate/lamp-*)."""
import re, sys, pathlib, json
def load(p):
    out = {}; cam = None
    for l in pathlib.Path(p).read_text(encoding="utf-8").splitlines():
        m = re.match(r"(\S+): objects=(\d+) drawsEst=(\d+) shadowDrawsEst=(\d+) trisK=\d+ trisExact=(\d+)", l)
        if m: cam = m[1]; out[cam] = dict(draws=int(m[3]), tris=int(m[5]), inst_draws=0, inst_tris=0); continue
        m = re.match(r"\s+(\S+) instanced.*draws (\d+), instances (\d+).*trianglesExact (\d+)", l)
        if m and m[1] in out: out[m[1]].update(inst_draws=int(m[2]), inst=int(m[3]), inst_tris=int(m[4]))
    return out
a, b = load(sys.argv[1]), load(sys.argv[2])
skip = ("cab-", "truck-", "trailer-", "plate-", "lamp-", "chase")
cams = [c for c in a if c in b and not c.startswith(skip)]
def tot(d, k): return sum(d[c][k] for c in cams)
def mx(d, k): return max(d[c][k] + d[c]["inst_" + k] for c in cams)
r = {"cams": len(cams)}
for k in ("draws", "tris", "inst_draws", "inst_tris"): r[k] = [tot(a, k), tot(b, k)]
r["max_draws_total"] = [mx(a, "draws"), mx(b, "draws")]; r["max_tris_total"] = [mx(a, "tris"), mx(b, "tris")]
print(json.dumps(r))
