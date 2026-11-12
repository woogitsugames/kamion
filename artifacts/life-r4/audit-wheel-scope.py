"""Actual GLB payload scope, independent of buffer offsets and vertex renumbering.

Use inside the round's heavy batch after regeneration. No budget threshold is
raised here. Counts are evidence; route draws/tris and images remain separate.
"""
import hashlib
import json
import struct
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Library:
    def __init__(self, path):
        raw = path.read_bytes()
        assert raw[:4] == b'glTF'
        version, length = struct.unpack_from('<II', raw, 4)
        assert version == 2 and length == len(raw)
        chunks, offset = {}, 12
        while offset < len(raw):
            size, kind = struct.unpack_from('<II', raw, offset)
            offset += 8
            chunks[kind] = raw[offset:offset + size]
            offset += size
        self.doc = json.loads(chunks[0x4e4f534a])
        self.data = chunks[0x004e4942]
        self.nodes = {n['name']: n for n in self.doc['nodes'] if 'mesh' in n}
        assert len(self.nodes) == sum('mesh' in n for n in self.doc['nodes'])

    def array(self, index):
        a = self.doc['accessors'][index]
        assert 'sparse' not in a
        view = self.doc['bufferViews'][a['bufferView']]
        dtype = np.dtype({5120: 'i1', 5121: 'u1', 5122: '<i2', 5123: '<u2',
                          5125: '<u4', 5126: '<f4'}[a['componentType']])
        width = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a['type']]
        return np.ndarray((a['count'], width), dtype=dtype, buffer=self.data,
                          offset=view.get('byteOffset', 0) + a.get('byteOffset', 0),
                          strides=(view.get('byteStride', width * dtype.itemsize), dtype.itemsize))

    def primitives(self, name):
        return self.doc['meshes'][self.nodes[name]['mesh']]['primitives']

    def material(self, p):
        return self.doc['materials'][p['material']]

    def signature(self, p):
        attrs = {}
        for key, index in sorted(p['attributes'].items()):
            a = self.doc['accessors'][index]
            attrs[key] = {'componentType': a['componentType'], 'type': a['type'],
                          'normalized': a.get('normalized', False),
                          'sha': hashlib.sha256(self.array(index).tobytes()).hexdigest()}
        return {'mode': p.get('mode', 4), 'material': self.material(p), 'attributes': attrs,
                'indices': hashlib.sha256(self.array(p['indices']).tobytes()).hexdigest()}

    def outside_wheels(self, p, proto):
        arrays = {k: self.array(v) for k, v in sorted(p['attributes'].items())}
        indices = self.array(p['indices']).reshape(-1, 3)
        vertices = arrays['POSITION']
        if proto.startswith('trailer_'):
            boxes = [(s * (1.275 - .27), y, .535, .385, .535)
                     for s in (-1, 1) for y in (3.05, 4.36, 5.67)]
        else:
            boxes = [(s * (2.49 / 2 - .18 - (.12 if w > .5 else 0)), y, .51, w, .51)
                     for s in (-1, 1) for y, w in ((3.15, .32), (-.55, .62))]
        result = Counter()
        for tri in indices:
            # streetscape/export.py declares glTF x=-source.x, y=source.z,
            # z=source.y. Wheel boxes below are in the source (right,front,up)
            # frame; preserve raw glTF attributes in the protected-face hashes.
            xyz = vertices[tri][:, [0, 2, 1]].copy()
            xyz[:, 0] *= -1
            containing = [box for box in boxes
                          if np.all(np.abs(xyz[:, 0] - box[0]) <= box[3] / 2 + .025001)
                          and np.all(np.abs(xyz[:, 1] - box[1]) <= box[4] + .000001)
                          and np.all(np.abs(xyz[:, 2] - box[2]) <= box[4] + .000001)]
            wheel = bool(containing)
            # The existing tread spans the tyre width. Protect its actual
            # triangle attributes too; only the sidewall/rim/recess can change.
            if wheel and self.material(p)['name'] == 'tyre':
                if any(np.ptp(xyz[:, 0]) > box[3] * .5 for box in containing):
                    wheel = False
            if wheel:
                continue
            corners = [b''.join(a[i].tobytes() for a in arrays.values()) for i in tri]
            # Ignore cyclic corner rotation, preserve winding and all attributes.
            value = min(b''.join(corners[i:] + corners[:i]) for i in range(3))
            result[hashlib.sha256(value).hexdigest()] += 1
        return result


def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else 'candidate'
    before = Library(OUT / 'baseline-street_props.glb')
    after = Library(ROOT / 'art-source/world/props/street_props.glb')
    assert before.nodes.keys() == after.nodes.keys(), 'Node inventory changed'
    assert before.doc['materials'] == after.doc['materials'], 'Material definitions changed'
    changes, protected, unexpected, counts = [], [], [], []
    for name in sorted(before.nodes):
        bnode, anode = before.nodes[name], after.nodes[name]
        assert {k: v for k, v in bnode.items() if k not in ('mesh', 'children')} == {
            k: v for k, v in anode.items() if k not in ('mesh', 'children')}, name
        bp, ap = before.primitives(name), after.primitives(name)
        assert len(bp) == len(ap), (name, 'Group count changed')
        static = name.startswith(('trailer_', 'tractor_')) and not name.endswith(('.col', '.contact'))
        total_b = total_a = 0
        for b, a in zip(bp, ap):
            material = after.material(a)['name']
            assert before.material(b)['name'] == material, (name, 'Group order changed')
            nb, na = before.array(b['indices']).size // 3, after.array(a['indices']).size // 3
            total_b += nb
            total_a += na
            if before.signature(b) == after.signature(a):
                continue
            change = dict(node=name, material=material, triangles_before=nb, triangles_after=na)
            changes.append(change)
            if not static or name.endswith(('.lod1', '.lod2')):
                protected.append(change)
            elif material not in ('tyre', 'rim', 'trailer_alu'):
                unexpected.append(change)
            elif before.outside_wheels(b, name) != after.outside_wheels(a, name):
                unexpected.append(change | {'reason': 'Triangle attributes outside nominal wheel boxes changed'})
        if static:
            counts.append(dict(node=name, before=total_b, after=total_a, delta=total_a-total_b))
    proof = json.loads((OUT / 'baseline-generated-source-proof.json').read_text(encoding='utf-8-sig'))
    raw_changed = [p['file'] for p in proof['products'] if sha(ROOT / p['file']) != p['actual']]
    result = dict(schema='kamion/life4-wheel-scope/1', node_count=len(after.nodes),
                  changed_primitives=changes, changed_outside_static_wheels=protected + unexpected,
                  materials_identical=True, groups_identical=True, raw_count=len(proof['products']),
                  raw_changed=raw_changed, static_counts=counts,
                  valid=not protected and not unexpected and not raw_changed,
                  note='Only near sidewall/rim/recess geometry inside nominal boxes is allowed. Existing tread triangle attributes, distant LODs and all other triangles are protected. This is scope evidence, not visual acceptance or frame/GPU cost.')
    (OUT / f'{tag}-wheel-scope.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(dict(nodes=len(after.nodes), changed_primitives=len(changes),
                          protected=len(protected), unexpected=len(unexpected), raw_changed=len(raw_changed))))
    assert not protected and not unexpected, protected + unexpected
    assert not raw_changed, raw_changed


if __name__ == '__main__':
    main()
