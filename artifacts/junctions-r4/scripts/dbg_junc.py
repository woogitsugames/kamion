import sys
sys.path.insert(0, "tools/worldgen")
import numpy as np
from roads import pipeline
w = pipeline.build("bialystok-industrial-c")
pts = [tuple(float(v) for v in a.split(",")) for a in sys.argv[1:]]
for j in w.junctions:
    cen = np.asarray(j.center, float)
    if not any(np.hypot(cen[0] - p[0], cen[1] - p[1]) < p[2] for p in pts):
        continue
    print("==", j.id, np.round(cen, 1), "sig", j.signalized, "rb", j.roundabout, "arms", len(j.arms), "nodes", getattr(j, "nodes", None))
    for i, a in enumerate(j.arms):
        c = a.chain
        print(f" arm{i} {c.id} end {a.end} L {c.length:.0f} trim {j.trims[i]:.1f} t_a {c.t_a:.1f} t_b {c.t_b:.1f} hw_end {float(c.hw_at(0 if a.end=='a' else c.length)):.2f} absorbed {c.meta.get('absorbed')} abreast {c.meta.get('abreast_of')} z_end {float(c.z[0 if a.end=='a' else -1]):.2f}")
    for c in j.corners:
        print("  corner", c.kind, c.k, c.k1, "tau", round(float(c.tau_k), 1), round(float(c.tau_k1), 1), "R", getattr(c, "R", None))
    print("  notes", j.notes)
    for i, a in enumerate(j.arms):
        for d in (5, 10, 15, 20, 30, 40, 50):
            if d < a.L:
                print(f"   arm{i} d {d}: gutter+ {np.round(a.gutter(d, +1), 1)} gutter- {np.round(a.gutter(d, -1), 1)}")
