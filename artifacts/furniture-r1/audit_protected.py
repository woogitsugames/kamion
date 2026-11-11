"""Compare protected road/bridge/barrier primitive payloads in A/B products, not just source diffs."""
import hashlib
import json
import sys
import numpy as np
from pathlib import Path
sys.path.insert(0, 'tests/gis')
from route_corridor import read_glb

base = Path('Data/raw/derived/bialystok-industrial-c')


def _acc(doc, data, off, idx):
    a = doc['accessors'][idx]; v = doc['bufferViews'][a['bufferView']]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
    dtype = np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5122:'<i2',5121:'<u1',5120:'<i1'}[a['componentType']])
    start = off + v.get('byteOffset',0) + a.get('byteOffset',0)
    return np.ndarray((a['count'],n), dtype=dtype, buffer=data, offset=start,
                      strides=(v.get('byteStride',n*dtype.itemsize),dtype.itemsize))


def payloads(phase):
    result = {}
    for f in sorted((base / f'furniture-r1-{phase}' / 'world').glob('*.glb')):
        doc, data, off = read_glb(f)
        for ni, node in enumerate(doc.get('nodes', [])):
            if 'mesh' not in node:
                continue
            for pi, p in enumerate(doc['meshes'][node['mesh']]['primitives']):
                mat = doc['materials'][p['material']]['name']
                if not mat.startswith(('road_', 'bridge_', 'barrier_', 'marking', 'curb_', 'kerb_',
                                       'collision_asphalt', 'collision_curb', 'collision_paving', 'collision_grass')):
                    continue
                h = hashlib.sha256()
                for name, idx in sorted(p['attributes'].items()):
                    h.update(name.encode()); h.update(_acc(doc, data, off, idx).tobytes())
                h.update(_acc(doc, data, off, p['indices']).tobytes())
                key = f'{f.name}/{node["name"]}/{pi}/{mat}'
                result[key] = h.hexdigest()
    return result


b, a = payloads('before'), payloads('after')
diff = [k for k in sorted(b.keys() | a.keys()) if b.get(k) != a.get(k)]
out = {'protected_primitives_before': len(b), 'protected_primitives_after': len(a), 'different': diff,
       'contract': 'Raw POSITION/NORMAL/UV/COLOR/index payloads: road_, bridge_, barrier_, marking, curb_/kerb_, road collision materials'}
Path('artifacts/furniture-r1/protected-geometry.json').write_text(json.dumps(out, indent=2)+'\n')
print(json.dumps(out))
if diff:
    sys.exit(1)
