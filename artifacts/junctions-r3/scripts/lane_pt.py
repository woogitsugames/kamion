"""Right-lane (or lane index) centre point of a chain nearest to E,N: lane_pt.py <chain> E,N [lane_from_left]"""
import sys
sys.path.insert(0, "tools/worldgen")
import numpy as np
from roads import pipeline
from roads.markings import lane_layout
net, *_ = pipeline.build_network("bialystok-industrial-c")
c = next(c for c in net.chains if sys.argv[1] in c.id)
for a in sys.argv[2:]:
    e, n, *k = a.split(",")
    s, lat = c.line.project(np.array([float(e), float(n)]))
    sec = net.sec_list[int(c.sec_idx[c.idx(s)])]
    d = int(c.dirn[c.idx(s)]) or 1
    cen = lane_layout(sec, float(c.hw_at(s)), d)[2]["fwd"]
    li = int(k[0]) if k else len(cen) - 1
    p = c.line.offset_point(s, cen[li]); t = c.line.frame(s)[0] * d
    q = np.asarray(p).reshape(-1) + np.asarray(t).reshape(-1) * 40.0
    print(f"{a}: s {s:.1f} lanes {len(cen)} lane {li} pos [{float(np.asarray(p).reshape(-1)[0]):.1f}, {float(np.asarray(p).reshape(-1)[1]):.1f}] ahead40 [{q[0]:.1f}, {q[1]:.1f}]")
