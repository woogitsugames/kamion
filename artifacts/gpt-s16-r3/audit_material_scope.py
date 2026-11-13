import json,struct,hashlib,collections
from pathlib import Path
r=Path(__file__).resolve().parent;root=r.parents[1]
policy_path=root/'Data/Regions/bialystok-industrial-c/shadow_caster_bias.json';policy=json.loads(policy_path.read_text());targets=set(policy['materials']);uses={m:collections.Counter() for m in targets}
manifest=json.loads((root/'Data/Regions/bialystok-industrial-c/generated/world_manifest.json').read_text())
for chunk in manifest['chunks']:
 for item in [chunk,chunk['low']]:
  with (root/item['file']).open('rb') as f:
   head=f.read(20);doc=json.loads(f.read(struct.unpack_from('<I',head,12)[0]))
  for node in doc['nodes']:
   if 'mesh' not in node:continue
   for primitive in doc['meshes'][node['mesh']]['primitives']:
    mat=doc['materials'][primitive['material']]['name']
    if mat in targets:uses[mat][node['name']]+=1
report={'policy_sha256':hashlib.sha256(policy_path.read_bytes()).hexdigest(),'chunk_material_node_uses':{m:dict(c) for m,c in uses.items()},'note':'Material slots in raw chunk nodes, not renderer draws; native shadow flags must also be checked. No geometry parsed or modified.'}
(r/'material-scope.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
