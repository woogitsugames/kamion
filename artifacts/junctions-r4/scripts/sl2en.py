"""(station, lateral) on a chain's RAW OSM polyline -> region-local E,N (stable under centre-offset overrides).

    sl2en.py <chain-substr> [--off X] s,lat s,lat ...      lateral: left +, in the chain frame
    --off X    the xsec image the values were read from was drawn on a line X m left of the raw polyline (existing
               center_offset in the chain frame when the image was made)
    --round r  after the points, also emit a rounded strip: s0,s1,lat0,lat1 (given as --strip s0,s1,lat0,lat1)
Prints a YAML flow list of [E, N]."""
import sys
sys.path.insert(0, "tools/worldgen")
import numpy as np
from roads import pipeline
from roads.geom import Polyline

a = sys.argv[1:]
cid = a.pop(0)
off = 0.0
strip = None
pts = []
while a:
    x = a.pop(0)
    if x == "--off":
        off = float(a.pop(0))
    elif x == "--strip":
        strip = [float(v) for v in a.pop(0).split(",")]
    else:
        pts.append(tuple(float(v) for v in x.split(",")))
net, *_ = pipeline.build_network("bialystok-industrial-c")
c = next(c for c in net.chains if cid in c.id)
ln = Polyline(np.asarray(c.raw, float))
dev = float(np.max(np.hypot(*(ln.point(np.linspace(0, ln.length, 50)) - c.line.point(np.linspace(0, c.line.length, 50))).T)))
print(f"# chain {c.id} raw L {ln.length:.1f} line L {c.line.length:.1f} max dev raw vs current line {dev:.2f} m", file=sys.stderr)
if strip:
    s0, s1, l0, l1 = strip
    r = abs(l1 - l0) / 2
    lm = 0.5 * (l0 + l1)
    sg = 1 if l1 > l0 else -1
    pts = []
    for k in range(7):
        t = -math.pi / 2 + k * math.pi / 6 if False else None
    import math
    for k in range(7):                                   # cap at s1
        t = -math.pi / 2 + k * math.pi / 6
        pts.append((s1 - r + r * math.cos(t), lm + r * math.sin(t)))
    for k in range(7):                                   # cap at s0
        t = math.pi / 2 + k * math.pi / 6
        pts.append((s0 + r + r * math.cos(t), lm + r * math.sin(t)))
out = []
for s, lat in pts:
    p = ln.offset_point(s, lat + off)
    p = np.asarray(p, float).reshape(-1)
    out.append(f"[{p[0]:.1f}, {p[1]:.1f}]")
print("[" + ", ".join(out) + "]")
