"""ADR 0141 check: over every world GLB, the minimum TEXCOORD_1.x of primitives whose material has a window_grid
(= Kamion/World Surface + _FAR_FACADE in Unity). The skyline flag uses uv1.x <= -15.5, so this must stay > -15.5
everywhere except the far_skyline node."""
import sys, json, struct, glob
from pathlib import Path
import numpy as np
R = Path(__file__).resolve().parents[2]
wm = json.loads((R / 'Data/Regions/bialystok-industrial-c/generated/world_manifest.json').read_text(encoding='utf-8'))
ff = {k for k, v in wm['materials'].items() if isinstance(v, dict) and 'window_grid' in v}
print('window_grid materials:', sorted(ff))
worst = {}
for f in sorted(glob.glob(str(R / 'Data/raw/derived/bialystok-industrial-c/world/*.glb'))):
    b = Path(f).read_bytes()
    jl = struct.unpack_from('<I', b, 12)[0]; g = json.loads(b[20:20 + jl]); bin0 = 20 + jl + 8
    def acc(i):
        a = g['accessors'][i]; bv = g['bufferViews'][a['bufferView']]
        off = bin0 + bv.get('byteOffset', 0) + a.get('byteOffset', 0)
        st = bv.get('byteStride') or 8
        raw = np.frombuffer(b, dtype='u1', count=st * (a['count'] - 1) + 8, offset=off)
        idx = (np.arange(a['count'])[:, None] * st + np.arange(8)[None, :])
        return np.frombuffer(raw[idx].tobytes(), dtype='f4').reshape(a['count'], 2)
    for nd in g['nodes']:
        if 'mesh' not in nd: continue
        for pr in g['meshes'][nd['mesh']]['primitives']:
            mat = g['materials'][pr['material']]['name'] if 'material' in pr else '?'
            if mat in ff and 'TEXCOORD_1' in pr['attributes']:
                u = acc(pr['attributes']['TEXCOORD_1'])
                key = (mat, nd['name'] if nd['name'].startswith('far_') else 'chunks')
                worst[key] = min(worst.get(key, 1e9), float(u[:, 0].min()))
for k, v in sorted(worst.items()): print(k, 'min uv1.x', v)
bad = [k for k, v in worst.items() if v <= -15.5 and k[1] != 'far_skyline']
print('COLLISIONS:', bad)
sys.exit(1 if bad else 0)
