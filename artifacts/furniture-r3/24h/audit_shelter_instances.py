"""Small JSON-only instance audit; no mesh loading, generation or image processing."""
import hashlib
import json
import sys
from pathlib import Path

EV = Path(__file__).resolve().parent
ROOT = EV.parents[2]
phase = sys.argv[1]
assert phase in ('before', 'after')
evidence = json.loads((EV / 'shelter-camera-evidence.json').read_text(encoding='utf-8-sig'))
selected = [row['selected_instance'] for row in evidence['selected']]
chunks, shelters, variants = {}, [], []
for item in evidence['instances_inputs']:
    path = ROOT / item['file']
    raw = path.read_bytes()
    if phase == 'before':
        assert hashlib.sha256(raw).hexdigest() == item['sha256'], 'Baseline already changed; do not overwrite evidence'
    packet = json.loads(raw)
    for instance in packet['instances']:
        if instance['p'] == 'bus_shelter_red_0120':
            variants.append(dict(instance))
            instance['p'] = 'bus_shelter'
        if instance['p'] == 'bus_shelter':
            shelters.append(dict(instance))
    canonical = json.dumps(packet, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    chunks[item['file']] = hashlib.sha256(canonical).hexdigest()
result = dict(phase=phase, normalized_chunks=chunks, shelters=shelters, red_variants=variants,
              caveat='JSON instance identity only; does not measure mesh, collision, draws or GPU')
if phase == 'after':
    before = json.loads((EV / 'instances-before.json').read_text())
    result['changed_normalized_chunks'] = [k for k in chunks.keys() | before['normalized_chunks'].keys()
                                           if chunks.get(k) != before['normalized_chunks'].get(k)]
    normal_variants = [dict(v, p='bus_shelter') for v in variants]
    result['exactly_two_selected_variants'] = len(variants) == 2 and sorted(normal_variants, key=lambda x: x['e']) == sorted(selected, key=lambda x: x['e'])
    result['shelters_unchanged_except_prototype'] = sorted(shelters, key=lambda x: (x['e'], x['n'])) == sorted(before['shelters'], key=lambda x: (x['e'], x['n']))
(EV / f'instances-{phase}.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
if phase == 'after':
    assert not result['changed_normalized_chunks'], result['changed_normalized_chunks']
    assert result['exactly_two_selected_variants'] and result['shelters_unchanged_except_prototype']
else:
    assert not variants, 'Baseline unexpectedly contains the new variant'
print(f'{phase}: {len(chunks)} chunk JSONs, {len(shelters)} shelters, {len(variants)} red variants; identity audit saved')
