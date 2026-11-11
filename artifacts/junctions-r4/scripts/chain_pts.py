"""Built centre line of a chain every N m (+ half width): chain_pts.py <chain-id-substr> [step] [lat]"""
import sys
sys.path.insert(0, "tools/worldgen")
import numpy as np
from roads import pipeline
net, graph, ov, stats = pipeline.build_network("bialystok-industrial-c")
step = float(sys.argv[2]) if len(sys.argv) > 2 else 5.0
lat = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
for c in net.chains:
    if sys.argv[1] in c.id:
        print("chain", c.id, "L", round(c.length, 1), "trim", getattr(c, "trim", None))
        for s in np.arange(0, c.length + 1e-6, step):
            p = np.asarray(c.line.offset_point(s, lat), float).reshape(-1)
            print(f"  s {s:6.1f}  E {p[0]:8.2f} N {p[1]:8.2f}  hw {float(c.hw_at(s)):.2f}")
