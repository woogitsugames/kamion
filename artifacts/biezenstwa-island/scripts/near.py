"""List road sections / chains near region-local E,N points: near.py E,N,R ..."""
import sys
sys.path.insert(0, "tools/worldgen")
import numpy as np
from roads import pipeline
net, graph, ov, stats = pipeline.build_network("bialystok-industrial-c")
pts = [tuple(float(v) for v in a.split(",")) for a in sys.argv[1:]]
from shapely.geometry import Point
for c in net.chains:
    ln = c.line
    for p in pts:
        xy = ln.p
        d = np.hypot(xy[:, 0] - p[0], xy[:, 1] - p[1])
        if d.min() < p[2]:
            i=int(d.argmin()); print("== chain", c.id, "L", round(c.length, 1), "near", p[:2], "dmin", round(float(d.min()), 1), "s", round(float(ln.s[i]),1), "hw", float(c.hw[i]) if c.hw is not None else None, "abreast", c.meta.get("abreast_of"))
            for (s0, s1, si, rev) in c.raw_spans:
                s = net.sections[si]
                print(f"   span {s0:.0f}-{s1:.0f} rev {rev} {s.edge_id} hw {s.highway} lanes {s.lanes} lw {s.lane_w} width {s.width} ow {s.oneway} off {s.center_offset} prov {dict(list(s.provenance.items())[:6])}")
for k in ("fork_tapers", "fork_shifts", "fork_abreast"):
    for x in stats[k]:
        print(k, x)
