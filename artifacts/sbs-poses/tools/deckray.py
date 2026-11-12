"""ADR 0130: vertical ray through generated chunk GLBs (road/bridge/road_collision) -> surface heights at E,N.
glTF axes: x = -E, y = U, z = N (verified against the stored 494288 deck hit U 140.188)."""
import json, struct, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[3]
WORLD = ROOT / 'Data/raw/derived/bialystok-industrial-c/world'
_cache = {}

def load(path):
    if path in _cache: return _cache[path]
    b = path.read_bytes(); l = struct.unpack('<I', b[12:16])[0]
    j = json.loads(b[20:20 + l]); off = 20 + l; bl = struct.unpack('<I', b[off:off + 4])[0]; bin_ = b[off + 8:off + 8 + bl]
    def acc(i):
        a = j['accessors'][i]; v = j['bufferViews'][a['bufferView']]
        dt = {5126: np.float32, 5125: np.uint32, 5123: np.uint16}[a['componentType']]
        n = {'VEC3': 3, 'SCALAR': 1}[a['type']]
        start = v.get('byteOffset', 0) + a.get('byteOffset', 0)
        return np.frombuffer(bin_, dtype=dt, count=a['count'] * n, offset=start).reshape(-1, n) if n > 1 else np.frombuffer(bin_, dtype=dt, count=a['count'], offset=start)
    meshes = {}
    for node in j['nodes']:
        if 'mesh' not in node: continue
        name = node.get('name')
        for prim in j['meshes'][node['mesh']]['primitives']:
            pos = acc(prim['attributes']['POSITION']).astype(float)
            idx = acc(prim['indices']).astype(np.int64).reshape(-1, 3)
            mat = j['materials'][prim['material']].get('name') if 'material' in prim else None
            meshes.setdefault(name, []).append((pos, idx, mat))
    _cache[path] = meshes
    return meshes

def heights(e, n, names=('road', 'bridge', 'road_collision'), low=True):
    x, z = -e, n
    out = []
    for f in sorted(WORLD.glob('chunk_*.low.glb' if low else 'chunk_*[0-9].glb')):
        for name, prims in load(f).items():
            if name not in names: continue
            for pos, idx, mat in prims:
                a, b, c = pos[idx[:, 0]], pos[idx[:, 1]], pos[idx[:, 2]]
                m = (np.minimum(np.minimum(a[:, 0], b[:, 0]), c[:, 0]) <= x) & (np.maximum(np.maximum(a[:, 0], b[:, 0]), c[:, 0]) >= x) & \
                    (np.minimum(np.minimum(a[:, 2], b[:, 2]), c[:, 2]) <= z) & (np.maximum(np.maximum(a[:, 2], b[:, 2]), c[:, 2]) >= z)
                for A, B, C in zip(a[m], b[m], c[m]):
                    v0, v1 = B - A, C - A; d = np.array([x - A[0], 0, z - A[2]])
                    den = v0[0] * v1[2] - v1[0] * v0[2]
                    if abs(den) < 1e-12: continue
                    s = (d[0] * v1[2] - v1[0] * d[2]) / den; t = (v0[0] * d[2] - d[0] * v0[2]) / den
                    if s >= -1e-9 and t >= -1e-9 and s + t <= 1 + 1e-9:
                        out.append((round(float(A[1] + s * v0[1] + t * v1[1]), 4), name, mat, f.name))
    return sorted(set(out), reverse=True)

if __name__ == '__main__':
    e, n = float(sys.argv[1]), float(sys.argv[2])
    for h in heights(e, n): print(h)
