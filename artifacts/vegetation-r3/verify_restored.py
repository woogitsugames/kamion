"""Verify regeneration after rejecting R3 experiments; no production writes."""
import argparse
import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
root = here.parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('stage', choices=['world', 'probe'])
args = parser.parse_args()
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
if args.stage == 'world':
    raw = root/'Data/raw/derived/bialystok-industrial-c/world'
    expected = json.loads((here/'snapshot-baseline/sha256.json').read_text())['files']
    meshes = {name: digest(root/name) == sha for name, sha in expected.items() if name.endswith('.glb')}
    inputs = {p.name: json.loads(p.read_text()) == json.loads((raw/p.name).read_text())
              for p in (here/'snapshot-baseline/instances').glob('instances_*.json')}
    result = dict(stage=args.stage, mesh_count=len(meshes), instance_files=len(inputs),
                  all_meshes_match=all(meshes.values()), all_instances_match=all(inputs.values()),
                  mismatched_meshes=[k for k,v in meshes.items() if not v],
                  mismatched_instance_files=[k for k,v in inputs.items() if not v])
    passed = len(meshes) == 130 and len(inputs) == 64 and all(meshes.values()) and all(inputs.values())
else:
    relative = Path('Low-overcast-photo-2048x1536/sbs-g3-b-297817221966185.png')
    before, after = here/'before'/relative, here/'restored-probe'/relative
    result = dict(stage=args.stage, before_sha256=digest(before), after_sha256=digest(after),
                  byte_identical=digest(before)==digest(after),
                  note='One probe only. Rejected candidates were not certified across all cameras.')
    passed = result['byte_identical']
result['passed'] = passed
(here/('restored-'+args.stage+'-proof.json')).write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
print(json.dumps(result, indent=2))
raise SystemExit(0 if passed else 1)
