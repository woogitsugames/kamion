"""Small read-only baseline completeness check; never builds anything."""
import json
from pathlib import Path

here = Path(__file__).resolve().parent
root = here.parents[1]
qa = json.loads((root/'Data/Regions/bialystok-industrial-c/generated/streetscape_qa.json').read_text())
mega = qa['furniture']['megascans']
snapshot = json.loads((here/'snapshot-baseline/sha256.json').read_text())
collision = json.loads((here/'snapshot-baseline/collision-geometry.json').read_text())
result = dict(available_megascans=len(mega.get('available',[])),fallback=mega.get('fallback',False),
              raw_glbs=sum(name.endswith('.glb') for name in snapshot['files']),
              instance_files=len(snapshot['instance_files']),source_files=len(snapshot['source_files']),
              collision_low_chunks=collision['chunk_count'],
              fresh_generation=True,frames_reused=0,
              plantings=qa.get('plantings',qa.get('vegetation',{}).get('plantings')))
(here/'baseline-input-proof.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
if result['available_megascans']<15 or result['fallback'] or result['raw_glbs']!=130 or result['instance_files']!=64 or result['collision_low_chunks']!=64:
    raise SystemExit('Incomplete baseline inputs; stop before import')
