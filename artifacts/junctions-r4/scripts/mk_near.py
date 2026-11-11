"""List generated marking parts in a box from the plan cache: mk_near.py E0 E1 N0 N1 [cache]"""
import pickle, sys
import numpy as np
e0, e1, n0, n1 = (float(v) for v in sys.argv[1:5])
d = pickle.load(open(sys.argv[5] if len(sys.argv) > 5 else "artifacts/junctions-r4/plan_cache.pkl", "rb"))
for layer, mat, src, V, T in d["parts"]:
    if layer != "markings":
        continue
    P = V[np.unique(T)][:, :2]
    m = (P[:, 0] > e0) & (P[:, 0] < e1) & (P[:, 1] > n0) & (P[:, 1] < n1)
    if m.sum() < 3:
        continue
    Q = P[m]
    # extreme points along the principal axis
    c = Q.mean(0); u, s, vt = np.linalg.svd(Q - c); ax = vt[0]; t = (Q - c) @ ax
    a, b = Q[t.argmin()], Q[t.argmax()]
    print(f"{src[:60]:60s} n={m.sum():5d} ends ({a[0]:.1f},{a[1]:.1f}) ({b[0]:.1f},{b[1]:.1f})")
