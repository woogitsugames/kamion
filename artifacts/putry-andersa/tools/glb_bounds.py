"""Bounds of named nodes of a GLB from the POSITION accessor min/max (ADR 0146). Usage: glb_bounds.py file.glb prefix [prefix...]"""
import sys, json, struct
def load(path):
    b = open(path, 'rb').read()
    n = struct.unpack('<I', b[12:16])[0]
    return json.loads(b[20:20 + n])
def bounds(g, prefixes):
    out = {}
    for nd in g['nodes']:
        nm = nd.get('name', '')
        if 'mesh' not in nd or not any(nm.startswith(p) for p in prefixes):
            continue
        lo, hi = [1e9] * 3, [-1e9] * 3
        for pr in g['meshes'][nd['mesh']]['primitives']:
            a = g['accessors'][pr['attributes']['POSITION']]
            lo = [min(x, y) for x, y in zip(lo, a['min'])]; hi = [max(x, y) for x, y in zip(hi, a['max'])]
        out[nm] = (lo, hi, nd.get('translation'), nd.get('rotation'), nd.get('scale'))
    return out
if __name__ == '__main__':
    for k, v in sorted(bounds(load(sys.argv[1]), sys.argv[2:]).items()):
        print(k, [round(x, 3) for x in v[0]], [round(x, 3) for x in v[1]], v[2:])
