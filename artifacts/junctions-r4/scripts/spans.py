"""List chain spans (edges) of given highway classes inside a local E/N box: spans.py E0,N0,E1,N1 [hw,hw..]"""
import sys
sys.path.insert(0, "tools/worldgen")
import numpy as np
from roads import pipeline
net, graph, ov, stats = pipeline.build_network("bialystok-industrial-c")
e0, n0, e1, n1 = (float(v) for v in sys.argv[1].split(","))
hws = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else None
for c in net.chains:
    for (s0, s1, eid, rev) in c.raw_spans:
        sec = net.sections[eid]
        if hws and sec.highway not in hws:
            continue
        sm = 0.5 * (s0 + s1) * c.length / max(c.raw_spans[-1][1], 1e-6)
        p = c.line.point(sm)
        if e0 <= p[0] <= e1 and n0 <= p[1] <= n1:
            print(f"SPAN {c.id} {s0:.0f} {s1:.0f} mid {p[0]:.0f},{p[1]:.0f} {eid} rev {int(rev)} {sec.highway} lanes {sec.lanes} w {sec.width} off {sec.center_offset} dirn {int(c.dirn[c.idx(sm)])}")
