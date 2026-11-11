"""Road-layer parts whose triangles contain plan point(s): parts_at.py E,N ... [cache] -> mat, src, UV / UV1 gradients"""
import pickle, sys
import numpy as np
pts = [tuple(float(v) for v in a.split(",")) for a in sys.argv[1:] if "," in a]
d = pickle.load(open("artifacts/junctions-r3/plan_cache.pkl", "rb"))
for e, n in pts:
    print(f"== {e},{n}")
    for layer, mat, src, V, T in d["parts"]:
        if layer not in ("road", "bridge"):
            continue
        A = V[T][:, :, :2]
        v0, v1, v2 = A[:, 1] - A[:, 0], A[:, 2] - A[:, 0], np.array([e, n]) - A[:, 0]
        den = v0[:, 0] * v1[:, 1] - v0[:, 1] * v1[:, 0]
        a = (v2[:, 0] * v1[:, 1] - v2[:, 1] * v1[:, 0]) / np.where(np.abs(den) < 1e-12, 1e-12, den)
        b = (v0[:, 0] * v2[:, 1] - v0[:, 1] * v2[:, 0]) / np.where(np.abs(den) < 1e-12, 1e-12, den)
        hit = (a >= 0) & (b >= 0) & (a + b <= 1)
        for k in np.where(hit)[0]:
            z = V[T[k]][:, 2]
            print(f"   {layer} {mat:18s} {src[:50]:50s} z {z.min():.2f}-{z.max():.2f} tri-area {abs(den[k])/2:.2f}")
