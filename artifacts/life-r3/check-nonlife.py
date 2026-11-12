"""Compare actual GLB node payloads, independent of changed buffer offsets."""
import hashlib,json,struct,sys
from pathlib import Path
import numpy as np
root=Path(__file__).resolve().parents[2]; out=Path(__file__).parent

def nodes(path):
    raw=path.read_bytes(); assert raw[:4]==b'glTF'
    chunks={}; offset=12
    while offset<len(raw):
        size,kind=struct.unpack_from('<II',raw,offset);offset+=8
        chunks[kind]=raw[offset:offset+size];offset+=size
    doc=json.loads(chunks[0x4e4f534a]); data=chunks[0x004e4942]
    types={5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}
    widths={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
    def accessor(index):
        a=doc['accessors'][index]; assert 'sparse' not in a
        v=doc['bufferViews'][a['bufferView']]; dtype=np.dtype(types[a['componentType']]); n=widths[a['type']]
        array=np.ndarray((a['count'],n),dtype=dtype,buffer=data,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',n*dtype.itemsize),dtype.itemsize))
        return dict(type=a['type'],component=a['componentType'],count=a['count'],normalized=a.get('normalized',False),sha=hashlib.sha256(array.tobytes()).hexdigest())
    result={}; details={}
    for node in doc['nodes']:
        if 'mesh' not in node:continue
        sig={k:v for k,v in node.items() if k not in ('mesh','children')}
        prims=[]
        for p in doc['meshes'][node['mesh']]['primitives']:
            item=dict(mode=p.get('mode',4),attributes={k:accessor(v) for k,v in sorted(p['attributes'].items())})
            if 'indices' in p:item['indices']=accessor(p['indices'])
            if 'material' in p:item['material']=doc['materials'][p['material']]
            prims.append(item)
        sig['primitives']=prims
        result[node['name']]=hashlib.sha256(json.dumps(sig,sort_keys=True).encode()).hexdigest()
        details[node['name']]=prims
    return result,details

before,bd=nodes(out/'baseline-street_props.glb')
after,ad=nodes(root/'art-source/world/props/street_props.glb')
changed=[n for n in sorted(before.keys()|after.keys()) if before.get(n)!=after.get(n)]
protected=[n for n in changed if not n.startswith(('car_','van_'))]
collision_changed=[n for n in changed if n.endswith(('.col','.contact'))]
primitive_changes=[]; unexpected_primitives=[]
for name in changed:
    if not name.startswith(('car_','van_')): continue
    old,new=bd[name],ad[name]
    assert len(old)==len(new),(name,'Material group count changed')
    for b,a in zip(old,new):
        assert b.get('material',{}).get('name')==a.get('material',{}).get('name'),(name,'Material group order changed')
        if b==a: continue
        material=a.get('material',{}).get('name','')
        entry=dict(node=name,material=material,triangles_before=b.get('indices',{}).get('count',0)//3,
                   triangles_after=a.get('indices',{}).get('count',0)//3)
        primitive_changes.append(entry)
        if material not in ('rim','rim_dark','rim_dusty'): unexpected_primitives.append(entry)
old=json.loads((out/'baseline-generated-source-proof.json').read_text())
raw_changed=[p['file'] for p in old['products'] if hashlib.sha256((root/p['file']).read_bytes()).hexdigest()!=p['actual']]
report=dict(before_nodes=len(before),after_nodes=len(after),changed=changed,changed_outside_passenger_vehicles=protected,
            collision_or_contact_changed=collision_changed,primitive_changes=primitive_changes,unexpected_primitives=unexpected_primitives,
            raw_products_checked=len(old['products']),raw_products_changed=raw_changed)
suffix='-'+sys.argv[1] if len(sys.argv)>1 else ''
(out/f'nonlife-glb-audit{suffix}.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(dict(nodes=len(after),changed=len(changed),protected_changed=len(protected),raw_changed=len(raw_changed))))
assert not protected,protected
assert not collision_changed,collision_changed
assert not unexpected_primitives,unexpected_primitives
assert not raw_changed,raw_changed

