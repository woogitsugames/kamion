"""Chunked terrain meshes with LODs and skirts.

Chunk = CHUNK_M x CHUNK_M metres (256 m -> 8 x 8 chunks on a 2048 m tile). LOD k samples every 2^k m.
LOD0 (1 m) is split into 4 sub-grids of 128 m so every primitive fits 16-bit indices (129^2 vertices).
Inside / next to the road footprint, LOD>0 heights are the MINIMUM of the 1 m conformed heights in
the node's window, so coarse terrain never pokes through a road. Skirts (vertical strips hanging
from every chunk border) hide LOD cracks between neighbours.
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage

CHUNK_M = 256
LODS = (1, 2, 4, 8)
SUB_M = 128


def lod_grid(zc, mask, step):
    if step == 1:
        return zc
    k = step + 1
    zmin = ndimage.minimum_filter(zc, size=k, mode="nearest")
    near = ndimage.maximum_filter(mask.astype(np.uint8), size=k + 2, mode="nearest").astype(bool)
    z = np.where(near, zmin, zc)
    return z[::step, ::step]


def normals(z, step):
    gy, gx = np.gradient(z, step)        # rows = -N, cols = +E
    dzdE = gx
    dzdN = -gy
    n = np.dstack([-dzdE, -dzdN, np.ones_like(z)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return n


def grid_mesh(z, nrm, e0, n0, step, i0, i1, j0, j1, skirt=1.0, col=None):
    """Vertices/tris for LOD-grid nodes [j0..j1] x [i0..i1] (inclusive). Node (j, i) is at
    E = e0 + i*step, N = n0 - j*step."""
    zz = z[j0:j1 + 1, i0:i1 + 1]
    nn = nrm[j0:j1 + 1, i0:i1 + 1]
    h, w = zz.shape
    I, Jg = np.meshgrid(np.arange(i0, i1 + 1), np.arange(j0, j1 + 1))
    E = e0 + I * step
    N = n0 - Jg * step
    V = np.column_stack([E.ravel(), N.ravel(), zz.ravel()])
    NR = nn.reshape(-1, 3)
    r, c = np.meshgrid(np.arange(h - 1), np.arange(w - 1), indexing="ij")
    a = (r * w + c).ravel()
    b = (r * w + c + 1).ravel()          # +E
    d = ((r + 1) * w + c).ravel()        # -N
    e = ((r + 1) * w + c + 1).ravel()
    # CCW seen from above in (E, N): a(E,N) -> d(E,N-1) -> e(E+1,N-1) ; a -> e -> b
    T = np.concatenate([np.column_stack([a, d, e]), np.column_stack([a, e, b])])
    # skirts along the 4 borders
    border = [np.arange(w), (h - 1) * w + np.arange(w)[::-1], np.arange(h)[::-1] * w, np.arange(h) * w + w - 1]
    # order each border so the skirt faces outward: walk the outline CW seen from above
    loops = [np.arange(w),                              # north edge, west->east
             np.arange(h) * w + (w - 1),                # east edge, north->south
             (h - 1) * w + np.arange(w)[::-1],          # south edge, east->west
             np.arange(h)[::-1] * w]                    # west edge, south->north
    del border
    Vs, Ns, Ts = [V], [NR], [T]
    CC = col[j0:j1 + 1, i0:i1 + 1].reshape(-1, col.shape[-1]) if col is not None else None
    Cs = [CC] if CC is not None else None
    base = len(V)
    for loop in loops:
        top = V[loop]
        bot = top.copy()
        bot[:, 2] -= skirt
        m = len(loop)
        Vs += [bot]
        Ns += [NR[loop]]
        if Cs is not None:
            Cs += [CC[loop]]
        ti = loop
        bi = base + np.arange(m)
        t1 = np.column_stack([ti[:-1], ti[1:], bi[1:]])
        t2 = np.column_stack([ti[:-1], bi[1:], bi[:-1]])
        Ts += [t1, t2]
        base += m
    if Cs is not None:
        return np.vstack(Vs), np.vstack(Ns), np.vstack(Ts), np.vstack(Cs)
    return np.vstack(Vs), np.vstack(Ns), np.vstack(Ts)


def build_chunks(zc, mask, e0, n0, size_m, col=None):
    """Return {(ci, cj): {lod: [primitive dicts]}} for the whole tile."""
    nch = int(size_m // CHUNK_M)
    out = {}
    lod_cache = {}
    for step in LODS:
        zl = lod_grid(zc, mask, step)
        lod_cache[step] = (zl, normals(zl, step), None if col is None else col[::step, ::step])
    for cj in range(nch):            # rows from north
        for ci in range(nch):        # columns from west
            lods = {}
            for li, step in enumerate(LODS):
                zl, nl, cl = lod_cache[step]
                per = CHUNK_M // step
                prims = []
                sub = SUB_M // step if step == 1 else per
                for sj in range(0, per, sub):
                    for si in range(0, per, sub):
                        i0 = ci * per + si
                        j0 = cj * per + sj
                        res = grid_mesh(zl, nl, e0, n0, step, i0, i0 + sub, j0, j0 + sub,
                                        skirt=1.0 + 0.5 * step, col=cl)
                        V, Nn, T = res[:3]
                        prims.append({"V": V, "N": Nn, "UV": V[:, :2].copy(), "T": T, "mat": "terrain_grass",
                                      "COL": res[3] if cl is not None else None})
                lods[li] = prims
            out[(ci, cj)] = lods
    return out
