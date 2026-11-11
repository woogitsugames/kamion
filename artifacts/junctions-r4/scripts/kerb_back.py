"""Kerb BACK faces (the 0.5 m buried flange behind a kerb) and what covers their top edge (ADR 0110, REVIEW s10-0100
P1-1: "wanna" / walls seen from the other carriageway). kerb_back.py <plan_cache.pkl>
A flange top vertex is COVERED when another ground surface (sidewalk, verge strip, island, asphalt) of the road layer
has a vertex within 5 cm of it; otherwise only the 1 m terrain grid stands behind the kerb (b0: 0.03-0.4 m lower)."""
import pickle, sys
import numpy as np
from scipy.spatial import cKDTree
d = pickle.load(open(sys.argv[1], "rb"))
other = [V for layer, mat, src, V, T in d["parts"] if layer == "road" and mat != "curb_concrete" and len(T)]
other = np.vstack([V[np.unique(T)] for (layer, mat, src, V, T) in d["parts"] if layer == "road" and mat != "curb_concrete" and len(T)])
tree = cKDTree(other)
tot = cov = 0
tops, rises = [], []
for layer, mat, src, V, T in d["parts"]:
    if layer != "road" or mat != "curb_concrete" or not len(T) or src.startswith("island:"):
        continue
    t = V[T]
    dz = t[:, :, 2].max(1) - t[:, :, 2].min(1)
    hor = np.hypot(t[:, :, 0].max(1) - t[:, :, 0].min(1), t[:, :, 1].max(1) - t[:, :, 1].min(1))
    a, b, c = t[:, 0], t[:, 1], t[:, 2]
    nrm = np.cross(b - a, c - a)
    nz = np.abs(nrm[:, 2]) / np.maximum(np.linalg.norm(nrm, axis=1), 1e-12)
    fl = (nz < 0.1) & (dz > 0.4)                 # flange faces (kerb rise faces are 0.04-0.2 m)
    rs = (nz < 0.1) & (dz > 0.03) & (dz < 0.3)
    if rs.any():
        rises.append(t[rs].reshape(-1, 3))
    if not fl.any():
        continue
    tf = t[fl]
    top = tf[np.arange(len(tf))[:, None], np.argsort(tf[:, :, 2], axis=1)[:, 1:]].reshape(-1, 3)   # the two upper vertices
    top = np.unique(np.round(top, 3), axis=0)
    tops.append(top)
top = np.vstack(tops)
rt = cKDTree(np.vstack(rises)[:, :2])
near, _ = rt.query(top[:, :2])
top = top[near < 0.17]                           # flange right behind the kerb top (kerb without a sidewalk)
dist, _ = tree.query(top)
tot, cov = len(top), int((dist < 0.05).sum())
print(f"kerb-only flange top vertices {tot}, covered by a ground surface {cov} ({100.0 * cov / max(tot, 1):.1f} %), bare (terrain only) {tot - cov}")
