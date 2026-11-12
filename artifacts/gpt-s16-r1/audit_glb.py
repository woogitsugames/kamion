"""Audit actual exported buffers, ignoring accessor offsets and material-index renumbering."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

import numpy as np

DTYPE = {5120: 'i1', 5121: 'u1', 5122: '<i2', 5123: '<u2', 5125: '<u4', 5126: '<f4'}
WIDTH = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}
VEHICLE = ('car_', 'van_', 'tractor_', 'trailer_')


def load(path):
    data = path.read_bytes()
    length = struct.unpack_from('<I', data, 12)[0]
    doc = json.loads(data[20:20 + length])
    start = 20 + length
    bin_len = struct.unpack_from('<I', data, start)[0]
    blob = data[start + 8:start + 8 + bin_len]

    def accessor(index):
        a = doc['accessors'][index]
        view = doc['bufferViews'][a['bufferView']]
        count, width = a['count'], WIDTH[a['type']]
        dtype = np.dtype(DTYPE[a['componentType']])
        offset = view.get('byteOffset', 0) + a.get('byteOffset', 0)
        stride = view.get('byteStride', width * dtype.itemsize)
        values = np.ndarray((count, width), dtype=dtype, buffer=blob, offset=offset,
                            strides=(stride, dtype.itemsize)).copy()
        return values

    out = {}
    for node in doc['nodes']:
        if 'mesh' not in node:
            continue
        prims = []
        for p in doc['meshes'][node['mesh']]['primitives']:
            attrs = {key:accessor(index) for key,index in p['attributes'].items()}
            attrs['indices'] = accessor(p['indices']).reshape(-1)
            attrs['material'] = doc['materials'][p['material']]['name']
            prims.append(attrs)
        out[node['name']] = prims
    return out


def digest(prims):
    h = hashlib.sha256()
    for prim in prims:
        for key,value in sorted(prim.items()):
            h.update(key.encode())
            h.update(value.encode() if isinstance(value,str) else value.tobytes())
    return h.hexdigest()


def tris(prims):
    return sum(len(p['indices'])//3 for p in prims)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('before', type=Path)
    p.add_argument('after', type=Path)
    p.add_argument('output', type=Path)
    args = p.parse_args()
    before, after = load(args.before), load(args.after)
    unchanged, changed, failures = [], [], []
    for name,prims in before.items():
        if name not in after:
            failures.append(f'missing: {name}'); continue
        target = after[name]
        allowed = name.startswith(VEHICLE) and name.endswith(('.lod1', '.lod2'))
        if not allowed:
            if digest(prims) != digest(target):
                failures.append(f'protected buffers changed: {name}')
            else:
                unchanged.append(name)
            continue
        changed.append(dict(name=name, submeshes_before=len(prims), submeshes_after=len(target),
                            tris_before=tris(prims), tris_after=tris(target)))
        if len(target) > 2 or tris(target) > tris(prims):
            failures.append(f'LOD budget: {name}')
        # Compare the unordered triangle positions after serialization/axis conversion.
        def triangle_positions(parts):
            values = np.concatenate([q['POSITION'][q['indices']].reshape(-1, 9) for q in parts])
            return sorted(tuple(t) for t in values)
        if triangle_positions(prims) != triangle_positions(target):
            failures.append(f'geometry changed: {name}')
    added = sorted(after.keys()-before.keys())
    for name in added:
        previous = name.removesuffix('.lod2') + '.lod1'
        if not name.startswith(('tractor_', 'trailer_')) or not name.endswith('.lod2') or previous not in after:
            failures.append(f'unexpected added node: {name}')
        elif digest(after[name]) != digest(after[previous]) or len(after[name]) > 2:
            failures.append(f'yard alias differs: {name}')
    result = dict(protected_nodes=len(unchanged), lods=changed,
                  added_nodes=added, failures=failures)
    args.output.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(protected_nodes=len(unchanged), lods=len(changed), failures=failures)))
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
