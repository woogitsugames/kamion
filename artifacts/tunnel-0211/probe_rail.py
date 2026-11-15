import sys
sys.path.insert(0, "tools/worldgen"); sys.path.insert(0, "tools/worldgen/qa")
import numpy as np
import junction_topview as jt
R = "bialystok-kleeberga"
jt.colour = lambda n: (0, 0, 0)
W = jt.load_world(R)
p = np.array([-128.0, -219.0])
for nm, tr, lo, hi in W:
    c = tr.mean(1)
    d = np.hypot(c[:, 0] - p[0], c[:, 1] - p[1])
    m = (d < 14) & (c[:, 2] > 117.5) & (c[:, 2] < 121.0)
    if m.any():
        t = c[m]
        print(nm, int(m.sum()), "x", t[:, 0].min().round(1), t[:, 0].max().round(1), "y", t[:, 1].min().round(1), t[:, 1].max().round(1), "z", t[:, 2].min().round(2), t[:, 2].max().round(2))
