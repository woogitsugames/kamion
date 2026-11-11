"""Hash exported geometry outside furniture ownership; licensed payloads stay outside git."""
import hashlib
import json
import struct
import sys
from pathlib import Path

phase = sys.argv[1]
result = {}
for path in sorted(Path('Data/raw/derived/bialystok-industrial-c/world').glob('chunk_*.glb')):
    raw = path.read_bytes()
    size = struct.unpack_from('<I', raw, 12)[0]
    doc = json.loads(raw[20:20+size])
    binary = raw[28+size:]

    def accessor(index):
        a = doc['accessors'][index]
        view = doc['bufferViews'][a['bufferView']]
        components = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a['type']]
        width = components * {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}[a['componentType']]
        stride = view.get('byteStride', width)
        start = view.get('byteOffset', 0) + a.get('byteOffset', 0)
        assert stride >= width and not a.get('sparse')
        if stride == width:
            return binary[start:start+a['count']*width]
        return b''.join(binary[start+i*stride:start+i*stride+width] for i in range(a['count']))

    for node in doc.get('nodes', []):
        if 'mesh' not in node:
            continue
        name = node.get('name', '')
        for k, primitive in enumerate(doc['meshes'][node['mesh']]['primitives']):
            mat = doc['materials'][primitive['material']]['name']
            if 'furniture' in name and not (mat.startswith(('barrier', 'noise_')) or mat == 'concrete_wall'):
                continue
            if mat == 'collision_fence':
                continue
            digest = hashlib.sha256()
            for attribute, index in sorted(primitive['attributes'].items()):
                digest.update(attribute.encode())
                digest.update(accessor(index))
            if 'indices' in primitive:
                digest.update(accessor(primitive['indices']))
            result[f'{path.name}/{name}/{mat}/{k}'] = digest.hexdigest()
out = Path(__file__).with_name(f'protected-geometry-{phase}.json')
out.write_text(json.dumps(result, indent=2)+'\n')
print(f'{phase}: protected primitive payloads {len(result)}')
if phase == 'after':
    before = json.loads(out.with_name('protected-geometry-before.json').read_text())
    changed = [key for key in before.keys() | result.keys() if before.get(key) != result.get(key)]
    summary = dict(before=len(before), after=len(result), changed=changed)
    out.with_name('protected-geometry-comparison.json').write_text(json.dumps(summary, indent=2)+'\n')
    if changed:
        raise SystemExit(f'Protected geometry changed: {len(changed)} keys; inspect comparison')
