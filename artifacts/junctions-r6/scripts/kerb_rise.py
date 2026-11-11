"""Kerb RISE above the carriageway (not the buried flange): vertical curb_concrete edges whose lower end sits on a
carriageway vertex (plan < 0.05 m, |dz| < 0.03). kerb_rise.py [cache] -> histogram + worst places."""
import pickle, sys, collections
import numpy as np
from scipy.spatial import cKDTree
CW = {"road_asphalt", "road_asphalt_new", "road_concrete", "road_paving", "road_sett", "road_gravel"}
d = pickle.load(open(sys.argv[1] if len(sys.argv) > 1 else "artifacts/junctions-r6/plan_cache.pkl", "rb"))
cw = np.vstack([V for layer, mat, src, V, T in d["parts"] if layer == "road" and mat in CW])
tree = cKDTree(cw[:, :2])
H, where = [], []
for layer, mat, src, V, T in d["parts"]:
    if layer != "road" or mat != "curb_concrete":
        continue
    for a, b in ((0, 1), (1, 2), (2, 0)):
        p, q = V[T[:, a]], V[T[:, b]]
        flat = np.hypot(*(p[:, :2] - q[:, :2]).T) < 1e-3
        dz = q[:, 2] - p[:, 2]
        m = flat & (np.abs(dz) > 0.02)
        lo = np.where((dz > 0)[:, None], p, q)[m]
        hz = np.abs(dz[m])
        if not len(lo):
            continue
        dist, idx = tree.query(lo[:, :2])
        on = (dist < 0.05) & (np.abs(cw[idx, 2] - lo[:, 2]) < 0.03)
        H += hz[on].tolist()
        where += [(round(float(x), 1), round(float(y), 1), round(float(h), 2), src[:48]) for (x, y, _), h in zip(lo[on], hz[on])]
H = np.array(H)
print("kerb rises", len(H), "p50 %.2f p95 %.2f max %.2f" % (np.percentile(H, 50), np.percentile(H, 95), H.max()))
for lo_, hi in ((0, .16), (.16, .25), (.25, .4), (.4, .7), (.7, 9)):
    print(f"  {lo_:.2f}-{hi:.2f}: {int(((H >= lo_) & (H < hi)).sum())}")
c = collections.Counter(w[3] for w in where if w[2] >= 0.25)
for s, n in c.most_common(12):
    ex = next(w for w in where if w[3] == s and w[2] >= 0.25)
    print(f"  {n:4d} {s}  e.g. E {ex[0]} N {ex[1]} h {ex[2]}")
