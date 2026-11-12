"""Cross-section of the generated chunk GLBs (ADR 0146): highest surface + material under points along a line in
local E,N. Usage: xsec.py E0 N0 E1 N1 [step]. glTF axes: x = -E, y = up, z = N (world_manifest gltf_axes)."""
import sys, json, struct, glob
import numpy as np
from pathlib import Path
REPO = Path(__file__).resolve().parents[3]
W = REPO / 'Data/raw/derived/bialystok-industrial-c/world'
CT = {5126: '<f4', 5125: '<u4', 5123: '<u2', 5121: 'u1'}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}

def tris(path):
    b = open(path, 'rb').read()
    n = struct.unpack('<I', b[12:16])[0]
    g = json.loads(b[20:20 + n]); bin_ = b[20 + n + 8:]
    def acc(i):
        a = g['accessors'][i]; bv = g['bufferViews'][a['bufferView']]
        off = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
        return np.frombuffer(bin_, CT[a['componentType']], a['count'] * NC[a['type']], off).reshape(a['count'], NC[a['type']])
    for nd in g['nodes']:
        if 'mesh' not in nd:
            continue
        t = np.array(nd.get('translation', [0, 0, 0]), float)
        for pr in g['meshes'][nd['mesh']]['primitives']:
            V = acc(pr['attributes']['POSITION']).astype(float) + t
            I = acc(pr['indices']).reshape(-1, 3)
            yield nd.get('name', ''), g['materials'][pr['material']]['name'], V, I

def section(e0, n0, e1, n1, step=0.5):
    man = json.loads((REPO / 'Data/Regions/bialystok-industrial-c/generated/world_manifest.json').read_text())
    L = float(np.hypot(e1 - e0, n1 - n0)); k = int(L / step) + 1
    P = np.column_stack([np.linspace(e0, e1, k), np.linspace(n0, n1, k)])
    best = [(-1e9, '') for _ in P]
    lo, hi = P.min(0) - 1, P.max(0) + 1
    for f in sorted(W.glob('chunk_*_*.glb')):
        if '.low' in f.name:
            continue
        for node, mat, V, I in tris(f):
            if mat.startswith('collision') or 'collision' in node:
                continue
            E, N, U = -V[:, 0], V[:, 2], V[:, 1]
            if E.max() < lo[0] or E.min() > hi[0] or N.max() < lo[1] or N.min() > hi[1]:
                continue
            A, B, C = (np.column_stack([E[I[:, j]], N[I[:, j]]]) for j in range(3))
            UA, UB, UC = (U[I[:, j]] for j in range(3))
            den = (B[:, 1] - C[:, 1]) * (A[:, 0] - C[:, 0]) + (C[:, 0] - B[:, 0]) * (A[:, 1] - C[:, 1])
            ok = np.abs(den) > 1e-9
            for q, p in enumerate(P):
                with np.errstate(divide='ignore', invalid='ignore'):
                    w0 = ((B[:, 1] - C[:, 1]) * (p[0] - C[:, 0]) + (C[:, 0] - B[:, 0]) * (p[1] - C[:, 1])) / den
                    w1 = ((C[:, 1] - A[:, 1]) * (p[0] - C[:, 0]) + (A[:, 0] - C[:, 0]) * (p[1] - C[:, 1])) / den
                w2 = 1 - w0 - w1
                m = ok & (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
                if m.any():
                    z = (w0 * UA + w1 * UB + w2 * UC)[m].max()
                    if z > best[q][0]:
                        best[q] = (float(z), mat)
    return P, best

if __name__ == '__main__':
    a = [float(x) for x in sys.argv[1:5]]
    P, best = section(*a, *( [float(sys.argv[5])] if len(sys.argv) > 5 else []))
    prev = None
    for p, (z, m) in zip(P, best):
        d = float(np.hypot(p[0] - a[0], p[1] - a[1]))
        print(f'{d:5.1f}  {z:8.2f}  {m}')
