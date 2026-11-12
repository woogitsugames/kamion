"""Read-only final audit plus copies of own generator side effects as evidence."""
import hashlib
import json
import shutil
from pathlib import Path

here = Path(__file__).resolve().parent
root = here.parents[1]
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
snapshot = json.loads((here/'snapshot-restored/sha256.json').read_text())['files']
pins = json.loads((here/'baseline-provenance.json').read_text())['exact_source_hashes']
changed = [name for name,sha in snapshot.items() if not (root/name).exists() or digest(root/name)!=sha]
drift = [name for name,sha in pins.items() if digest(root/name)!=sha]
if changed or drift:
    raise SystemExit('Stop: output/source differs. Preserve the earlier audit and backups; do not rerun after canonical cleanup.')
side_effects = [
    'Data/Regions/bialystok-industrial-c/generated/far_field_qa.json',
    'Data/Regions/bialystok-industrial-c/generated/landmarks/viaduct_putry_underdeck.spec.json',
    'Data/Regions/bialystok-industrial-c/generated/roads_qa.json',
    'Data/Regions/bialystok-industrial-c/generated/streetscape_qa.json',
    'Data/Regions/bialystok-industrial-c/generated/world_manifest.json',
    'Data/SourceManifests/bialystok-industrial-c-far-field.manifest.json',
    'art-source/world/props/props_meta.json',
]
backups = {}
for name in side_effects:
    target = here/'generator-side-effects'/name
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(root/name,target)
    backups[name] = digest(target)
for source,target in [
    ('artifacts/logs/import-region-bialystok-industrial-c-20261112-025130.log','unity-logs/import-restored.log'),
    ('artifacts/logs/visual-qa-WorldC-20261112-025406.log','unity-logs/probe-restored.log'),
    ('artifacts/logs/test-editmode-20261112-025424.log','unity-logs/editmode-final.log'),
    ('artifacts/tests/editmode-20261112-025424.xml','test-results/editmode-final.xml'),
]:
    dest = here/target
    dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(root/source,dest)
result = dict(changed_outputs_after_final_gis_and_unity=changed,
              source_drift_since_baseline=drift,source_count=len(pins),
              backed_up_generator_side_effects=backups,
              note='Recorded before restoring tracked generator side effects to HEAD. Snapshot-restored describes the generated/imported world; canonical tracked metadata will then return to the pre-round state.')
(here/'posttests-audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
if changed or drift:
    raise SystemExit('Stop before closing: investigate output/source drift')
