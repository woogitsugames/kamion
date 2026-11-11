import sys, json
sys.path.insert(0, "tools/worldgen")
import numpy as np
from roads import pipeline
net, *_ = pipeline.build_network("bialystok-industrial-c")
c = next(c for c in net.chains if sys.argv[1] in c.id)
r = np.asarray(json.load(open("Data/Regions/bialystok-industrial-c/route_start.json"))["points_en"], float)
for a in sys.argv[2:]:
    p = np.array([float(v) for v in a.split(",")])
    s, lat = c.line.project(p)
    d = np.hypot(*(r - p).T); i = int(d.argmin())
    t = r[min(i + 1, len(r) - 1)] - r[max(i - 1, 0)]; t /= np.hypot(*t)
    q = p - r[i]; side = float(t[0] * q[1] - t[1] * q[0])
    print(f"{a}: chain s {s:.1f} lat {lat:+.2f} hw {float(c.hw_at(s)):.2f} | route dist {d.min():.2f} (target {'left' if side > 0 else 'right'} of route)")
