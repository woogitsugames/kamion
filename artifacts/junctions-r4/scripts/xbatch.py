"""Montage of straightened orthophoto strips (x = station, y = lateral, left = up; 1 m ticks, labels every 5 m;
magenta = generated centre lines, cyan = generated carriageway edges).
   xbatch.py <name> <chain-substr>,<s0>,<s1>,<lat_half>[,sm] ...   'sm' = stations given as fraction of chain length*100
"""
import os, sys
sys.path.insert(0, "tools/worldgen")
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw
from roads import pipeline
from fidelity import ortho as O
RID = "bialystok-industrial-c"
net, graph, ov, stats = pipeline.build_network(RID)
reg = pipeline.load_region(RID)
ox, oy = reg["origin"]["x"], reg["origin"]["y"]
ORT = O.Ortho(reg)
RES, K = 0.05, 2


def strip(cid, s0, s1, lh):
    c = next(c for c in net.chains if cid in c.id)
    ln = c.line
    ss = np.arange(s0, s1, RES)
    lat = np.arange(lh, -lh, -RES / K)
    P = ln.point(ss); _, N = ln.frame(ss)
    X = P[None, :, 0] + lat[:, None] * N[None, :, 0]
    Y = P[None, :, 1] + lat[:, None] * N[None, :, 1]
    bb = (ox + X.min() - 1, oy + Y.min() - 1, ox + X.max() + 1, oy + Y.max() + 1)
    rgb, src = ORT.window(bb, 0.08, prefer_hr=not os.environ.get("XSEC_SHEET"))
    H, W = rgb.shape[:2]
    u = np.clip(((X + ox - bb[0]) / (bb[2] - bb[0]) * W).astype(int), 0, W - 1)
    v = np.clip(((bb[3] - (Y + oy)) / (bb[3] - bb[1]) * H).astype(int), 0, H - 1)
    im = Image.fromarray(rgb[v, u])
    d = ImageDraw.Draw(im)
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
            prev = None
            for pt in q + nq * (off * hwq)[:, None]:
                st, la = ln.project(pt)
                if st <= s0 + 0.01 or st >= s1 - 0.01 or abs(la) > lh:
                    prev = None
                    continue
                cur = ((st - s0) / RES, (lh - la) / RES * K)
                if prev is not None and abs(cur[0] - prev[0]) < 200:
                    d.line([prev, cur], fill=col, width=1)
                prev = cur
    for m in range(int(-lh), int(lh) + 1):
        y = (lh - m) / RES * K
        d.line([(0, y), (8 if m % 5 else 20, y)], fill=(255, 255, 0))
        if m % 5 == 0:
            d.text((22, y - 5), f"{m:+d}", fill=(255, 255, 0))
    for st in np.arange(np.ceil(s0 / 5) * 5, s1, 5):
        x = (st - s0) / RES
        d.line([(x, 0), (x, 8)], fill=(255, 255, 0)); d.text((x + 2, 8), f"{st:.0f}", fill=(255, 255, 0))
    sm = 0.5 * (s0 + s1)
    sec = net.sec_list[int(c.sec_idx[c.idx(sm)])]
    d.text((40, 22), f"{sec.edge_id} dirn {int(c.dirn[c.idx(sm)])} hw {float(c.hw_at(sm)):.2f} {src}", fill=(255, 255, 0))
    return im


ims = []
for spec in sys.argv[2:]:
    a = spec.split(",")
    ims.append(strip(a[0], float(a[1]), float(a[2]), float(a[3])))
Wt = sum(i.width for i in ims) + 6 * (len(ims) - 1)
out = Image.new("RGB", (Wt, max(i.height for i in ims)))
x = 0
for i in ims:
    out.paste(i, (x, 0)); x += i.width + 6
d = Path("artifacts/junctions-r4/xsec"); d.mkdir(parents=True, exist_ok=True)
out.save(d / f"{sys.argv[1]}.png")
print(sys.argv[1], out.size)
