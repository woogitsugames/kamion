"""Exposed kerb faces from the plan cache: vertical curb_concrete edges (same plan xy, dz) next to a carriageway.
   kerb_faces.py [cache] -> histogram of face heights and the worst places (E/N, src)"""
import pickle, sys, collections
import numpy as np
d = pickle.load(open(sys.argv[1] if len(sys.argv) > 1 else "artifacts/junctions-r3/plan_cache.pkl", "rb"))
H, where = [], []
for layer, mat, src, V, T in d["parts"]:
    if layer != "road" or mat != "curb_concrete":
        continue
    for a, b in ((0, 1), (1, 2), (2, 0)):
        p, q = V[T[:, a]], V[T[:, b]]
        flat = np.hypot(*(p[:, :2] - q[:, :2]).T) < 1e-3
        dz = np.abs(p[:, 2] - q[:, 2])
        m = flat & (dz > 0.02)
        H += dz[m].tolist()
        where += [(round(float(x), 1), round(float(y), 1), round(float(h), 2), src[:48]) for (x, y, _), h in zip(p[m], dz[m])]
H = np.array(H)
print("faces", len(H), "p50 %.2f p95 %.2f max %.2f" % (np.percentile(H, 50), np.percentile(H, 95), H.max()))
for lo, hi in ((0, .16), (.16, .25), (.25, .4), (.4, .7), (.7, 9)):
    print(f"  {lo:.2f}-{hi:.2f}: {int(((H >= lo) & (H < hi)).sum())}")
c = collections.Counter(w[3] for w in where if w[2] >= 0.25)
for s, n in c.most_common(15):
    ex = next(w for w in where if w[3] == s and w[2] >= 0.25)
    print(f"  {n:4d} {s}  e.g. E {ex[0]} N {ex[1]} h {ex[2]}")
