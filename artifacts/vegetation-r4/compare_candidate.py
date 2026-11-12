"""Read-only exact source, instance and decoded collision provenance checks."""
import argparse
import json
from pathlib import Path

here = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('label')
args = parser.parse_args()
before = here/'snapshot-baseline'
after = here/('snapshot-'+args.label)
read = lambda path: json.loads(path.read_text(encoding='utf-8'))
b, a = read(before/'sha256.json'), read(after/'sha256.json')
changed = lambda old, new: sorted(k for k in old.keys() | new.keys() if old.get(k) != new.get(k))
source_changes = changed(b['source_files'], a['source_files'])
instance_changes = changed(b['instance_files'], a['instance_files'])
bc, ac = read(before/'collision-geometry.json'), read(after/'collision-geometry.json')
collision_changes = changed(bc['chunks'], ac['chunks'])
outputs = changed(b['files'], a['files'])
far_field_changes = [p for p in outputs if 'far_field' in p and p.endswith('.glb')]
bq, aq = read(before/'streetscape_qa.json'), read(after/'streetscape_qa.json')
plantings = lambda qa: qa.get('plantings', qa.get('vegetation', {}).get('plantings'))
mega = aq['furniture']['megascans']
result = dict(label=args.label, source_changes=source_changes, instance_changes=instance_changes,
    collision_changes=collision_changes, collision_low_chunks=ac['chunk_count'],
    generated_changes=outputs, far_field_glb_changes=far_field_changes,
    plantings_before=plantings(bq), plantings_after=plantings(aq),
    megascans_available=len(mega.get('available', [])), megascans_fallback=mega.get('fallback', False),
    collision_note='Exact decoded geometry/transform/material digests; not a PhysX runtime measurement.')
result['pass'] = (source_changes == ['tools/worldgen/streetscape/plantings.py']
    and not instance_changes and not collision_changes and ac['chunk_count'] == 64
    and not far_field_changes and plantings(bq) == plantings(aq)
    and result['megascans_available'] >= 15 and not result['megascans_fallback'])
(here/(args.label+'-input-proof.json')).write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
print(json.dumps(result, indent=2))
if not result['pass']:
    raise SystemExit('Candidate provenance mismatch; inspect before import')
