"""Actual GLB payload scope, independent of buffer offsets and vertex renumbering.

Use inside the round's heavy batch after regeneration. No budget threshold is
raised here. Counts are evidence; route draws/tris and images remain separate.
"""
import hashlib
import json
import struct
import sys
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


def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else 'candidate'
    before = Library(OUT / 'baseline-street_props.glb')
    after = Library(ROOT / 'art-source/world/props/street_props.glb')
    assert before.nodes.keys() == after.nodes.keys(), 'Node inventory changed'
    assert before.doc['materials'] == after.doc['materials'], 'Material definitions changed'
    allowed = {f'pallets_empty_{n}{suffix}' for n in (4, 8, 12, 16) for suffix in ('', '.lod1')}
    changed, protected, counts = [], [], []
    for name in sorted(before.nodes):
        bn, an = before.nodes[name], after.nodes[name]
        assert {k: v for k, v in bn.items() if k not in ('mesh', 'children')} == {
            k: v for k, v in an.items() if k not in ('mesh', 'children')}, name
        bp, ap = before.primitives(name), after.primitives(name)
        assert len(bp) == len(ap), (name, 'Material group count changed')
        for b, a in zip(bp, ap):
            material = after.material(a)['name']
            assert before.material(b)['name'] == material, (name, 'Group order changed')
            nb, na = before.array(b['indices']).size // 3, after.array(a['indices']).size // 3
            if name in allowed:
                assert material == 'pallet_wood'
                vb, va = before.array(b['attributes']['POSITION']), after.array(a['attributes']['POSITION'])
                # Preserve footprint/envelope, accepting <=1mm removal of the
                # old inter-layer seam. Far LOD may inherit <=3cm layer jitter.
                assert np.all(va.min(0) >= vb.min(0) - .031001), name
                assert np.all(va.max(0) <= vb.max(0) + .031001), name
                assert abs(float(np.ptp(va[:, 1])) - .144*int(name.split('_')[2].split('.')[0])) < .0021
                counts.append(dict(node=name, before=nb, after=na, delta=na-nb))
            if before.signature(b) != after.signature(a):
                row = dict(node=name, material=material, before=nb, after=na)
                changed.append(row)
                if name not in allowed:
                    protected.append(row)
    proof = json.loads((OUT / 'baseline-generated-source-proof.json').read_text(encoding='utf-8-sig'))
    raw_changed = [p['file'] for p in proof['products'] if sha(ROOT / p['file']) != p['actual']]
    result = dict(schema='kamion/life5-pallet-scope/1', nodes=len(after.nodes), changed=changed,
                  protected_changes=protected, raw_changed=raw_changed, counts=counts,
                  materials_and_groups_identical=True, valid=not protected and not raw_changed,
                  note='Only four empty pallet stack prototypes, LOD0/LOD1. Collision, contact, all other props and raw instance products frozen. CPU library evidence, not route or GPU budget.')
    (OUT / f'{tag}-pallet-scope.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    assert not protected and not raw_changed
    expected = {r['node'] for r in changed}
    if tag.endswith('-prebuild'):
        assert not expected, 'Prebuild must still hold the exact baseline GLB'
    else:
        assert expected == allowed, 'Expected all eight pallet LODs to change'


if __name__ == '__main__':
    main()

