import sys
sys.path.insert(0, "tools/worldgen")
import numpy as np
from roads import pipeline
w = pipeline.build("bialystok-industrial-c")
for cid, end in (("c:w266084693:12620261934-2840742308", "b"), ("c:w173956083:2840742310-1852129066", "b"), ("c:w1101181473:10076968415-1847263305", "b")):
    c = next(c for c in w.net.chains if c.id == cid)
    n = len(c.line.s)
    idx = range(n - 1, n - 60, -6) if end == "b" else range(0, 60, 6)
    print("==", cid, "t_a", round(c.t_a, 1), "t_b", round(c.t_b, 1))
    for i in idx:
        print(f"  d {abs(c.line.s[i]-c.line.s[-1 if end=='b' else 0]):5.1f} z {c.z[i]:.3f} e {float(np.nan_to_num(c.e[i], nan=9.99)):+.3f} hw {c.hw[i]:.2f} xy {np.round(c.line.p[i],1)} zL {float(c.crossfall_z(c.line.s[i], c.hw[i])):.3f} zR {float(c.crossfall_z(c.line.s[i], -c.hw[i])):.3f}")
