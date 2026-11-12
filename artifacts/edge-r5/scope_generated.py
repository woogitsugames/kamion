"""Retain only edge-owned fields from the required whole-world regeneration."""
import hashlib
import json
import subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
REGION='bialystok-industrial-c'
relative=f'Data/Regions/{REGION}/generated/world_manifest.json'
qa=json.loads((ROOT/f'Data/Regions/{REGION}/generated/far_field_qa.json').read_text())
for tier in qa['tiers'].values():
    actual=hashlib.sha256((ROOT/tier['file']).read_bytes()).hexdigest()
    if actual != tier['sha256']:
        raise RuntimeError('Far-field metadata does not describe the raw mesh; regenerate it before scoping.')
fresh=json.loads((ROOT/relative).read_text())
base=json.loads(subprocess.check_output(['git','show',f'HEAD:{relative}'],cwd=ROOT))
base['far_field']=fresh['far_field']
base['materials']['far_field_buildings']=fresh['materials']['far_field_buildings']
(ROOT/relative).write_text(json.dumps(base,ensure_ascii=False,indent=1,sort_keys=True,allow_nan=False)+'\n',
                           encoding='utf-8',newline='\n')
restore=[f'Data/Regions/{REGION}/generated/landmarks/viaduct_putry_underdeck.spec.json',
         f'Data/Regions/{REGION}/generated/roads_qa.json',
         f'Data/Regions/{REGION}/generated/streetscape_qa.json',
         'art-source/world/props/props_meta.json',
         'art-source/world/props/street_props.glb']
subprocess.run(['git','restore','--',*restore],cwd=ROOT,check=True)
receipt=dict(retained_world_manifest_fields=['far_field','materials.far_field_buildings'],
             restored_unrelated_generated_files=restore,verified_raw_far_field_hashes=2,
             note='No source files from roads, buildings, vegetation or Claude changed.')
(HERE/'generated-scope.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=False))
