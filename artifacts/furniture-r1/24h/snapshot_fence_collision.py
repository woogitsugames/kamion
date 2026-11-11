"""Hash actual exported fence collision accessors, without reading unrelated GLB buffers."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('phase',choices=['before4','after4'])
parser.add_argument('--compare',choices=['before4'])
args = parser.parse_args()
result = {}
components = {'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
sizes = {5120:1,5121:1,5122:2,5123:2,5125:4,5126:4}
for path in sorted((ROOT/'Data/raw/derived/bialystok-industrial-c/world').glob('chunk_*.glb')):
    with path.open('rb') as stream:
        assert struct.unpack('<III',stream.read(12))[:2] == (0x46546c67,2)
        json_length,json_kind = struct.unpack('<II',stream.read(8))
        assert json_kind == 0x4e4f534a
        doc = json.loads(stream.read(json_length))
        _,binary_kind = struct.unpack('<II',stream.read(8))
        assert binary_kind == 0x004e4942
        binary_offset = stream.tell()

        def update_accessor(digest,index):
            accessor = doc['accessors'][index]
            view = doc['bufferViews'][accessor['bufferView']]
            assert view.get('buffer',0) == 0 and not accessor.get('sparse')
            width = components[accessor['type']]*sizes[accessor['componentType']]
            stride = view.get('byteStride',width)
            assert stride >= width
            digest.update(json.dumps({key:accessor.get(key,False) for key in
                                      ('type','count','componentType','normalized')},sort_keys=True).encode())
            stream.seek(binary_offset+view.get('byteOffset',0)+accessor.get('byteOffset',0))
            count = accessor['count']
            span = (count-1)*stride+width if count else 0
            data = stream.read(span)
            assert len(data) == span,'Truncated collision accessor'
            if stride == width:
                digest.update(data)
            else:
                for row in range(count):
                    digest.update(data[row*stride:row*stride+width])

        for node in doc.get('nodes',[]):
            if 'mesh' not in node:
                continue
            for index,primitive in enumerate(doc['meshes'][node['mesh']]['primitives']):
                material = doc['materials'][primitive['material']]['name']
                if material != 'collision_fence':
                    continue
                digest = hashlib.sha256()
                for name,accessor_index in sorted(primitive['attributes'].items()):
                    digest.update(name.encode())
                    update_accessor(digest,accessor_index)
                if 'indices' in primitive:
                    update_accessor(digest,primitive['indices'])
                result[f"{path.name}/{node.get('name','')}/{material}/{index}"] = digest.hexdigest()
assert result,'No fence collision primitives found'
(HERE/f'fence-collision-{args.phase}.json').write_text(json.dumps(result,indent=2)+'\n')
print(f'{args.phase}: fence collision payloads {len(result)}')
if args.compare:
    before = json.loads((HERE/f'fence-collision-{args.compare}.json').read_text())
    changed = sorted(key for key in before.keys()|result.keys() if before.get(key)!=result.get(key))
    (HERE/'fence-collision-comparison.json').write_text(json.dumps(
        dict(before=len(before),after=len(result),changed=changed),indent=2)+'\n')
    if changed:
        raise SystemExit(f'Fence collision changed: {len(changed)} payloads')
