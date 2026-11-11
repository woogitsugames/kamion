"""E,N -> (station, lateral) on a chain's raw OSM polyline and on its current line: en2sl.py <chain> E,N ..."""
import sys
sys.path.insert(0, "tools/worldgen")
import numpy as np
from roads import pipeline
from roads.geom import Polyline
net, *_ = pipeline.build_network("bialystok-industrial-c")
c = next(c for c in net.chains if sys.argv[1] in c.id)
raw = Polyline(np.asarray(c.raw, float))
for a in sys.argv[2:]:
    p = np.array([float(v) for v in a.split(",")])
    s0, l0 = raw.project(p)
    s1, l1 = c.line.project(p)
    print(f"{a}: raw s {s0:.1f} lat {l0:+.2f} | line s {s1:.1f} lat {l1:+.2f} hw {float(c.hw_at(s1)):.2f} dirn {int(c.dirn[c.idx(s1)])}")
