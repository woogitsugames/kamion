import sys, json, pickle
import numpy as np
d = pickle.load(open("artifacts/junctions-r2/plan_cache.pkl", "rb"))
r = json.load(open("Data/Regions/bialystok-industrial-c/route_start.json"))
P = np.asarray(r["points_en"], float)
s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
s0, s1 = float(sys.argv[1]), float(sys.argv[2])
lat = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
ss = np.arange(s0, s1, 0.25)
Q = np.column_stack([np.interp(ss, s, P[:, 0]), np.interp(ss, s, P[:, 1])])
T = np.gradient(Q, axis=0); T /= np.hypot(*T.T)[:, None]
Q = Q + np.column_stack([-T[:, 1], T[:, 0]]) * lat
tris = []
for layer, mat, src, V, Tt in d["parts"]:
    if layer != "road" or mat == "curb_concrete":
        continue
    t = V[Tt]
    m = (t[:, :, 0].max(1) > Q[:, 0].min() - 1) & (t[:, :, 0].min(1) < Q[:, 0].max() + 1) & (t[:, :, 1].max(1) > Q[:, 1].min() - 1) & (t[:, :, 1].min(1) < Q[:, 1].max() + 1)
    for x in t[m]:
        tris.append((x, mat, src))
prev = None
for q, st in zip(Q, ss):
    best = None
    for x, mat, src in tris:
        a, b, c = x[:, :2]
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        w0 = ((b[1] - c[1]) * (q[0] - c[0]) + (c[0] - b[0]) * (q[1] - c[1])) / den
        w1 = ((c[1] - a[1]) * (q[0] - c[0]) + (a[0] - c[0]) * (q[1] - c[1])) / den
        w2 = 1 - w0 - w1
        if min(w0, w1, w2) >= -1e-9:
            z = w0 * x[0, 2] + w1 * x[1, 2] + w2 * x[2, 2]
            if best is None or z > best[0]:
                best = (z, mat, src)
    if best:
        print(f"s {st:7.2f} en {q[0]:8.2f} {q[1]:8.2f} z {best[0]:.3f} dz {0 if prev is None else best[0]-prev:+.3f} {best[1]} {best[2]}")
        prev = best[0]
    else:
        print(f"s {st:7.2f} en {q[0]:8.2f} {q[1]:8.2f} NO SURFACE")
