"""Straightened orthophoto strip along a generated chain: x = station, y = lateral offset (left = up).
   xsec.py <chain-id> <s0> <s1> <lat_half> <name> [raw]   -> artifacts/junctions-r2/xsec/<name>.png + lateral profile peaks
   'raw' = use the chain's raw OSM polyline (before centre offsets) instead of the built centre line."""
import sys
sys.path.insert(0, "tools/worldgen")
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw
from roads import pipeline
from roads.geom import Polyline
from fidelity import ortho as O
RID = "bialystok-industrial-c"
cid, s0, s1, lh, name = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
raw = len(sys.argv) > 6 and sys.argv[6] == "raw"
net, graph, ov, stats = pipeline.build_network(RID)
c = next(c for c in net.chains if c.id == cid or cid in c.id)
ln = Polyline(c.raw) if raw else c.line
reg = pipeline.load_region(RID)
ox, oy = reg["origin"]["x"], reg["origin"]["y"]
RES = 0.05
ss = np.arange(s0, s1, RES)
lat = np.arange(lh, -lh, -RES)
P = ln.point(ss); _, N = ln.frame(ss)
X = P[None, :, 0] + lat[:, None] * N[None, :, 0]
Y = P[None, :, 1] + lat[:, None] * N[None, :, 1]
bb = (ox + X.min() - 1, oy + Y.min() - 1, ox + X.max() + 1, oy + Y.max() + 1)
import os
rgb, src = O.Ortho(reg).window(bb, 0.08, prefer_hr=not os.environ.get("XSEC_SHEET"))
H, W = rgb.shape[:2]
u = np.clip(((X + ox - bb[0]) / (bb[2] - bb[0]) * W).astype(int), 0, W - 1)
v = np.clip(((bb[3] - (Y + oy)) / (bb[3] - bb[1]) * H).astype(int), 0, H - 1)
img = rgb[v, u]
k = 2
im = Image.fromarray(img).resize((img.shape[1], img.shape[0] * k), Image.LANCZOS)
d = ImageDraw.Draw(im)
for m in range(int(-lh), int(lh) + 1):
    y = (lh - m) / RES * k
    d.line([(0, y), (10 if m % 5 else 22, y)], fill=(255, 255, 0))
    if m % 5 == 0:
        d.text((24, y - 5), f"{m:+d}", fill=(255, 255, 0))
for st in np.arange(np.ceil(s0 / 5) * 5, s1, 5):
    x = (st - s0) / RES
    d.line([(x, 0), (x, 8)], fill=(255, 255, 0)); d.text((x + 2, 8), f"{st:.0f}", fill=(255, 255, 0))
# generated centre lines (magenta) and carriageway edges (cyan) of every chain crossing the strip
for c2 in net.chains:
    q = c2.line.p[::2]
    if len(q) < 2:
        continue
    lo, hi = np.array([X.min(), Y.min()]) - 5, np.array([X.max(), Y.max()]) + 5
    if (q.max(0) < lo).any() or (q.min(0) > hi).any():
        continue
    sq = c2.line.s[::2]
    _, nq = c2.line.frame(sq)
    hwq = np.asarray(c2.hw_at(sq), float)
    for off, col in ((0.0, (255, 0, 255)), (1.0, (0, 255, 255)), (-1.0, (0, 255, 255))):
        pts = q + nq * (off * hwq)[:, None]
        prev = None
        for pt in pts:
            st, la = ln.project(pt)
            if st <= s0 + 0.01 or st >= s1 - 0.01 or abs(la) > lh:
                prev = None
                continue
            cur = ((st - s0) / RES, (lh - la) / RES * k)
            if prev is not None and abs(cur[0] - prev[0]) < 200:
                d.line([prev, cur], fill=col, width=1)
            prev = cur
out = Path("artifacts/junctions-r2/xsec"); out.mkdir(parents=True, exist_ok=True)
if im.width > 1900:
    im = im.resize((1900, int(im.height * 1900 / im.width)), Image.LANCZOS)
im.save(out / f"{name}.png")
g = img.astype(float)
lum = g.mean(2); sat = g.max(2) - g.min(2)
pl = np.median(lum, axis=1); ps = np.median(sat, axis=1)
print(name, src, "chain", c.id, "L", round(c.length, 1), "sec hw", float(c.hw[c.idx((s0 + s1) / 2)]),
      "centre_offset", None if c.meta.get("center_offset") is None else float(np.asarray(c.meta["center_offset"])[c.idx((s0 + s1) / 2)]))
# lateral profile, 0.25 m bins
for m in np.arange(lh, -lh, -0.25):
    i0 = int((lh - m) / RES); sl = slice(i0, i0 + 5)
    print(f"{m - 0.125:+6.2f} lum {pl[sl].mean():5.1f} sat {ps[sl].mean():4.1f} " + "#" * int(pl[sl].mean() / 6))
