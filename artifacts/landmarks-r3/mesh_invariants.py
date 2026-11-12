"""Compare actual GLB primitive bytes independently of global accessor/material indices.

Capture after the isolated EC build only if all128 chunk SHA hashes still match
the fresh baseline. Check later permits just the three underdeck paint materials
in the bridge node; roads, barriers, terrain, buildings and collision stay exact.
"""
import hashlib
import json
import struct
import sys
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
WIDTH={5120:1,5121:1,5122:2,5123:2,5125:4,5126:4}
COMPONENTS={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}
ALLOWED={('bridge','pier_yellow'),('bridge','bridge_soffit'),('bridge','bridge_concrete')}

def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))

def read_primitives(path):
    payload=path.read_bytes()
    size,kind=struct.unpack_from('<II',payload,12)
    assert kind==0x4e4f534a
    doc=json.loads(payload[20:20+size]); binary=memoryview(payload)[28+size:]
    def accessor(index):
        a=doc['accessors'][index]; v=doc['bufferViews'][a['bufferView']]
        width=WIDTH[a['componentType']]*COMPONENTS[a['type']]
        start=v.get('byteOffset',0)+a.get('byteOffset',0); stride=v.get('byteStride',width)
        digest=hashlib.sha256()
        if stride==width:
            digest.update(binary[start:start+a['count']*width])
        else:
            assert saved['files'][key]['sha256']==orig['sha256'],('Snapshot not from fresh baseline',key)
            for i in range(a['count']): digest.update(binary[start+i*stride:start+i*stride+width])
        return dict(type=a['type'],componentType=a['componentType'],count=a['count'],
                    normalized=a.get('normalized',False),sha256=digest.hexdigest())
    records=[]
    for node in doc['nodes']:
        if 'mesh' not in node: continue
        for p in doc['meshes'][node['mesh']]['primitives']:
            name=doc['materials'][p['material']]['name']
            data=dict(attributes={k:accessor(v) for k,v in sorted(p['attributes'].items())},
                      indices=accessor(p['indices']),mode=p.get('mode',4),
                      transform={k:node[k] for k in ('matrix','rotation','translation','scale') if k in node})
            digest=hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()
            records.append(dict(node=node['name'],material=name,sha256=digest))
    return hashlib.sha256(payload).hexdigest(),records

mode=sys.argv[1]
assert mode in ('capture','check')
base=load(OUT/'baseline-generated/world_manifest.json')
current=load(ROOT/'Data/Regions/bialystok-industrial-c/generated/world_manifest.json')
old={c['id']:c for c in base['chunks']}
saved=load(OUT/'baseline-mesh-invariants.json') if mode=='check' else None
records={}; changed=[]; checked=0
for chunk in current['chunks']:
    for tier,entry,orig in [('High',chunk,old[chunk['id']]),('Low',chunk['low'],old[chunk['id']]['low'])]:
        key=f'{chunk["id"]}/{tier}'
        digest,prims=read_primitives(ROOT/entry['file'])
        assert digest==entry['sha256'],('Current runtime cache stale',key)
        if mode=='capture':
            assert digest==orig['sha256'],('EC-only build changed chunk mesh',key)
            records[key]=dict(file=entry['file'],sha256=digest,primitives=prims)
        else:
            before=saved['files'][key]['primitives']
            clean=lambda items:sorted((p['node'],p['material'],p['sha256']) for p in items
                                      if (p['node'],p['material']) not in ALLOWED)
            assert clean(before)==clean(prims),('Non-underdeck mesh changed',key)
            checked+=len(clean(prims))
            if digest!=saved['files'][key]['sha256']: changed.append(key)
if mode=='capture':
    assert len(records)==128
    result=dict(complete=True,scope='All128 chunks exactly identical to fresh baseline before EC',files=records)
    target=OUT/'baseline-mesh-invariants.json'
else:
    result=dict(complete=True,all_non_underdeck_primitives_identical=True,files_checked=128,
                current_manifest_sha256=hashlib.sha256((ROOT/'Data/Regions/bialystok-industrial-c/generated/world_manifest.json').read_bytes()).hexdigest(),
                exact_primitives_checked=checked,changed_chunk_files=changed,
                exclusions=[dict(node=n,material=m) for n,m in sorted(ALLOWED)],
                limitation='Underdeck paint material groups excluded only in bridge node; deck-buffer hashes and collision tests are separate evidence')
    target=OUT/'mesh-invariants-after-pier-correction.json'
target.write_text(json.dumps(result,indent=2),encoding='utf-8')
print(mode,':',len(records) if mode=='capture' else checked,'records; saved',target)
