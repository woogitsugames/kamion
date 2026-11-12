"""CPU applicability/scope check in a temporary artifact tree; no C#/Unity PASS is implied."""
from pathlib import Path
import hashlib,json,struct
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'artifacts/surface-wear-r1'
pins=json.loads((OUT/'candidate-source-pins.json').read_text())
for name,sha in pins.items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha,name
scratch=OUT/'candidate-sandbox'
for name in pins:
    assert (scratch/name).exists()
    s=(scratch/name).read_text()
    assert 'RoadWearSentinel' in s
patch=(OUT/'candidate-r1.patch').read_text()
assert 'WorldPBR.shader' not in patch and 'tools/worldgen/roads/' not in patch
assert '_Tint' not in patch and '_WheelPolish' not in patch and '_CrackMap' not in patch
manifest=json.loads((ROOT/'Data/Regions/bialystok-industrial-c/generated/world_manifest.json').read_text())
allocations=[]
for c in manifest['chunks']:
    for tier,item in [('High',c),('Low',c['low'])]:
        data=(ROOT/item['file']).read_bytes();n=struct.unpack_from('<I',data,12)[0];g=json.loads(data[20:20+n])
        for node in g.get('nodes',[]):
            if node.get('name')!='road' or 'mesh' not in node:continue
            primitives=g['meshes'][node['mesh']]['primitives']
            road=[p for p in primitives if g['materials'][p['material']].get('name') in ('road_asphalt','road_asphalt_new')]
            if road and not any('TEXCOORD_1' in p['attributes'] for p in road):
                count=sum(g['accessors'][p['attributes']['POSITION']]['count'] for p in primitives)
                allocations.append(dict(tier=tier,file=item['file'],road_layer_vertices=count,predicted_extra_uv1_bytes=count*4))
result=dict(note='CPU patch applicability/scope only, not C# compilation, NUnit execution, visual result or GPU budget. Predicted extra UV1 buffer assumes source ROADWEAR channel policy; actual import must verify.',
            production_source_unchanged=True,sandbox_only=True,nunit_cases_prepared=3,
            expected_new_uv1_allocations=allocations,predicted_extra_bytes_by_tier={t:sum(x['predicted_extra_uv1_bytes'] for x in allocations if x['tier']==t) for t in ('Low','High')})
(OUT/'candidate-cpu-check.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
