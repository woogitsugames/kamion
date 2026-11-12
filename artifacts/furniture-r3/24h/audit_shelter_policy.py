"""Stream serialized policy metadata only; no meshes, generation or image processing."""
import json
import re
import sys
from pathlib import Path

ev = Path(__file__).resolve().parent
root = ev.parents[2]
phase = sys.argv[1]
assert phase in ('before2', 'after2', 'after3')
path = root / 'game/Assets/_Generated/World/bialystok-industrial-c/Instances.asset'
policies, current, field, found = {}, None, None, False
with path.open(encoding='utf-8-sig') as handle:
    for line in handle:
        if not found:
            found = line.rstrip() == '  prototypes:'
            continue
        if re.match(r'^  [A-Za-z_]\w*:', line):
            break
        if line.startswith('  - name: '):
            current = line.strip()[8:]
            policies[current] = dict(lodEndM=[], lod_count=0)
            field = None
        elif current is not None:
            key = re.match(r'^    (\w+):\s*(.*)', line)
            if key:
                field = key[1]
                if field in ('shadowLodMask', 'count'):
                    policies[current][field] = int(key[2])
            elif line.startswith('    - '):
                if field == 'lods':
                    policies[current]['lod_count'] += 1
                elif field == 'lodEndM':
                    policies[current]['lodEndM'].append(float(line.strip()[2:]))
assert found and len(policies) > 10, 'No complete prototype policy section'
variant = 'bus_shelter_red_0120'
assert policies['bus_shelter']['lodEndM'] == [60., 300.]
assert variant in policies
result = dict(phase=phase, policies=policies, scope='Visibility policy, shadow mask, LOD count and instance count only; not mesh payloads')
if phase in ('after2', 'after3'):
    before = json.loads((ev / 'shelter-policy-before2.json').read_text())['policies']
    changed = [name for name in policies.keys() | before.keys() if policies.get(name) != before.get(name)]
    result['changed_prototypes'] = sorted(changed)
    result['variant_inherits_generic'] = policies[variant]['lodEndM'] == policies['bus_shelter']['lodEndM'] and policies[variant]['shadowLodMask'] == policies['bus_shelter']['shadowLodMask']
    assert set(changed) <= {variant}, changed
    assert result['variant_inherits_generic']
    assert policies[variant]['lod_count'] == before[variant]['lod_count']
    assert policies[variant]['count'] == before[variant]['count']
(ev / f'shelter-policy-{phase}.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
print(f'{phase}: {len(policies)} prototype policies; generic {policies["bus_shelter"]}; variant {policies[variant]}')
