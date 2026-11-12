"""walls_at.py E,N,R [cache]: near-vertical triangles (|nz| < 0.3) of the road / bridge layers within R of a point: material,
src, plan extent, z range (lone kerb flanges, ADR 0123)."""
import pickle, sys
import numpy as np
e, n, r = (float(v) for v in sys.argv[1].split(","))
d = pickle.load(open(sys.argv[2] if len(sys.argv) > 2 else "artifacts/junctions-r6/plan_cache.pkl", "rb"))
for layer, mat, src, V, T in d["parts"]:
    if layer not in ("road", "bridge") or not len(T):
        continue
    t = V[T]
    c = t.mean(1)
    nrm = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    nz = np.abs(nrm[:, 2]) / np.maximum(np.linalg.norm(nrm, axis=1), 1e-12)
    m = (np.hypot(c[:, 0] - e, c[:, 1] - n) < r) & (nz < 0.3) & ((t[:, :, 2].max(1) - t[:, :, 2].min(1)) > 0.25)
    if m.any():
        tt = t[m].reshape(-1, 3)
        print(f"{layer:6s} {mat:16s} {src[:60]:60s} tris {int(m.sum()):3d} E {tt[:,0].min():.1f}..{tt[:,0].max():.1f} N {tt[:,1].min():.1f}..{tt[:,1].max():.1f} z {tt[:,2].min():.2f}..{tt[:,2].max():.2f}")
