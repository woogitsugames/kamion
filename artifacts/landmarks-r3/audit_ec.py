"""Fresh baseline invariants: all chunk meshes, roads and non-EC instances."""
import hashlib
import json
import struct
import sys
from pathlib import Path

import numpy as np

out=Path(__file__).resolve().parent
root=out.parents[1]
sys.path.insert(0,str(root/'tools/worldgen'))
from streetscape import ec_chimneys as EC,hero_building as HB

def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    digest=hashlib.sha256()
    with p.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):
            digest.update(block)
    return digest.hexdigest()
def canonical(rows): return sorted(json.dumps(r,sort_keys=True,separators=(',',':')) for r in rows)

baseline=out/'baseline-generated'
generated=root/'Data/Regions/bialystok-industrial-c/generated'
before=load(baseline/'world_manifest.json'); after=load(generated/'world_manifest.json')
permit_pier_correction='--pier-correction' in sys.argv
material_changes=[k for k in before['materials'] if before['materials'][k]!=after['materials'].get(k)]
assert before['materials'].keys()==after['materials'].keys()
if permit_pier_correction:
    assert set(material_changes)<= {'pier_yellow'}
    a=dict(before['materials']['pier_yellow']); b=dict(after['materials']['pier_yellow'])
    a.pop('color'); b.pop('color')
    assert a==b,'Pier change exceeded pigment colour'
    proof=load(out/'mesh-invariants-after-pier-correction.json')
    assert proof['complete'] and proof['all_non_underdeck_primitives_identical']
    assert proof['current_manifest_sha256']==sha(generated/'world_manifest.json')
else:
    assert not material_changes,'Material definitions changed'
assert before['origin_epsg2180']==after['origin_epsg2180']
assert len(before['chunks'])==len(after['chunks'])==64
old={c['id']:c for c in before['chunks']}; new={c['id']:c for c in after['chunks']}
assert old.keys()==new.keys()
target_src={'override:ec-bialystok-chimney-1','override:ec-bialystok-chimney-2'}
old_targets=[]; new_targets=[]; non_target_count=0
all_chunk_meshes_identical=True
for key in old:
    a,b=old[key],new[key]
    for x,y in [(a,b),(a['low'],b['low'])]:
        if x['sha256']!=y['sha256']:
            all_chunk_meshes_identical=False
            assert permit_pier_correction,('Chunk mesh changed',key,x['file'])
        assert sha(root/y['file'])==y['sha256'],('Stale current chunk cache',y['file'])
    orig=baseline/'instances'/Path(a['instances']['file']).name
    current=root/b['instances']['file']
    assert sha(orig)==a['instances']['sha256']
    assert sha(current)==b['instances']['sha256']
    x,y=load(orig)['instances'],load(current)['instances']
    xx=[it for it in x if it.get('src') not in target_src]
    yy=[it for it in y if it.get('src') not in target_src]
    assert canonical(xx)==canonical(yy),('Non-EC instances changed',key)
    non_target_count+=len(xx)
    old_targets += [it for it in x if it.get('src') in target_src]
    new_targets += [it for it in y if it.get('src') in target_src]
assert load(baseline/'roads_qa.json')==load(generated/'roads_qa.json')
assert len(old_targets)==len(new_targets)==2
positions=[]
for a in old_targets:
    matches=[it for it in new_targets if it['src']==a['src']]
    assert len(matches)==1
    b=matches[0]
    assert b['p'].startswith('landmark_ec_chimney_')
    delta={k:b.get(k,0)-a.get(k,0) for k in ['e','n','z','yaw']}
    positions.append(dict(src=a['src'],before=a,after=b,delta=delta))

assets=[]
for d in EC.config()['stacks'].values():
    folder,gp,mp=HB.asset_paths(d['asset'])
    spec=load(HB.spec_path(EC.REGION,d['asset'])); meta=load(mp)
    assert meta['spec_sha256']==HB._sha(spec)
    assert meta['glb_sha256']==sha(gp)
    payload=gp.read_bytes(); size,kind=struct.unpack_from('<II',payload,12)
    assert kind==0x4e4f534a
    doc=json.loads(payload[20:20+size]); binary=payload[28+size:]
    nodes=[]
    for node in doc['nodes']:
        assert node.get('matrix') is None and node.get('rotation',[0,0,0,1])==[0,0,0,1]
        mesh=doc['meshes'][node['mesh']]; vertices=[]; shell=[]
        for p in mesh['primitives']:
            acc=doc['accessors'][p['attributes']['POSITION']]; view=doc['bufferViews'][acc['bufferView']]
            offset=view.get('byteOffset',0)+acc.get('byteOffset',0)
            assert acc['componentType']==5126 and acc['type']=='VEC3'
            V=np.ndarray((acc['count'],3),dtype='<f4',buffer=binary,offset=offset,strides=(view.get('byteStride',12),4))
            assert np.isfinite(V).all()
            vertices.append(V)
            if doc['materials'][p['material']]['name'] in ('chimney_red','chimney_white'):
                shell.append(V[(V[:,1]>=0)&(V[:,1]<110)])
        V=np.concatenate(vertices); shaft=np.concatenate(shell)
        centres=[]; sampled_heights=[]
        for z in spec['chimney']['band_boundaries_m']:
            if z>=110: continue
            expected_radius=(d['base_d_m']+(d['top_d_m']-d['base_d_m'])*z/120)/2
            # Galleries now share white paint, so exclude their outer rail/rim
            # and sample the actual full shaft rings, not arbitrary rail heights.
            ring=shaft[np.isclose(shaft[:,1],z,atol=1e-4)][:,[0,2]]
            ring=ring[np.linalg.norm(ring,axis=1)<=expected_radius+.005]
            assert len(ring)>=12
            centres.append((ring.min(0)+ring.max(0))/2)
            sampled_heights.append(z)
        axis_drift=float(np.max(np.abs(centres)))
        assert axis_drift<.001
        assert abs(float(V[:,1].min())+1)<.001 and abs(float(V[:,1].max())-120)<.001
        nodes.append(dict(node=node['name'],height_bounds_m=[float(V[:,1].min()),float(V[:,1].max())],
                          shaft_axis_max_offset_m=axis_drift,shaft_sampled_heights=sampled_heights,submeshes=len(mesh['primitives'])))
    assert len(nodes)==2
    assets.append(dict(asset=d['asset'],meta=meta,nodes=nodes))
result=dict(all_128_chunk_meshes_identical=all_chunk_meshes_identical,roads_qa_identical=True,
            materials_identical=not material_changes,material_changes=material_changes,
            all_non_underdeck_primitives_identical=True,
            all_non_ec_instances_identical=True,non_ec_instance_count=non_target_count,
            target_count_before=2,target_count_after=2,target_positions=positions,
            target_positions_exact=all(all(v==0 for v in p['delta'].values()) for p in positions),assets=assets)
(out/'ec-geometry-audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='assets'},indent=2))
