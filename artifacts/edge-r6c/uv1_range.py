"""ADR 0141 check: TEXCOORD_1.x range of ordinary far-field geometry (the skyline flag must not collide with it)."""
import sys, json, struct
from pathlib import Path
import numpy as np
p = Path(sys.argv[1]); b = p.read_bytes()
jl = struct.unpack_from('<I', b, 12)[0]; g = json.loads(b[20:20 + jl]); bin0 = 20 + jl + 8
def acc(i):
    a = g['accessors'][i]; bv = g['bufferViews'][a['bufferView']]
    n = {'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'SCALAR': 1}[a['type']]
    dt = {5126: 'f4', 5123: 'u2', 5125: 'u4', 5121: 'u1'}[a['componentType']]
    off = bin0 + bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    st = bv.get('byteStride')
    if st and st != np.dtype(dt).itemsize * n:
        raw = np.frombuffer(b, dtype='u1', count=st * a['count'], offset=off).reshape(a['count'], st)[:, :np.dtype(dt).itemsize * n]
        return np.frombuffer(raw.tobytes(), dtype=dt).reshape(a['count'], n)
    return np.frombuffer(b, dtype=dt, count=a['count'] * n, offset=off).reshape(a['count'], n)
for nd in g['nodes']:
    if 'mesh' not in nd: continue
    for pr in g['meshes'][nd['mesh']]['primitives']:
        if 'TEXCOORD_1' in pr['attributes']:
            u = acc(pr['attributes']['TEXCOORD_1'])
            print(nd['name'], 'verts', len(u), 'uv1.x min/max', float(u[:, 0].min()), float(u[:, 0].max()), 'uv1.y min/max', float(u[:, 1].min()), float(u[:, 1].max()))
