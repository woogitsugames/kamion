"""Compare every captured camera; keep mesh and instance estimates separate."""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MESH = re.compile(r'^(.*?): objects=(\d+) drawsEst=(\d+) shadowDrawsEst=(\d+) trisK=(\d+)')
INST = re.compile(r'^\s+(.*?) instanced .*?: draws (\d+), instances (\d+), triangles (\d+)k')

def read(path):
    result = {}
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        if match := MESH.match(line):
            name, *values = match.groups()
            result.setdefault(name, {}).update(zip(('objects', 'draws', 'shadow_draws', 'tris_k'), map(int, values)))
        elif match := INST.match(line):
            name, *values = match.groups()
            result.setdefault(name, {}).update(zip(('instance_draws', 'instances', 'instance_tris_k'), map(int, values)))
    return result

before, after = sys.argv[1:3]
focus_subset = '--focus' in sys.argv[3:]
rows = []
for path in sorted((ROOT / before).glob('*/stats.txt')):
    condition = path.parent.name
    a, b = read(path), read(ROOT / after / condition / 'stats.txt')
    if focus_subset:
        if not b.keys() <= a.keys():
            raise RuntimeError(f'Unknown focus camera: {condition}')
        a = {name:a[name] for name in b}
    if a.keys() != b.keys():
        raise RuntimeError(f'Camera inventory mismatch: {condition}')
    for name in sorted(a):
        row = {'condition': condition, 'camera': name}
        for key in a[name]:
            row[f'{key}_before'] = a[name][key]
            row[f'{key}_after'] = b[name][key]
            row[f'{key}_delta'] = b[name][key] - a[name][key]
        for version, data in (('before', a[name]), ('after', b[name])):
            row[f'total_tris_k_{version}'] = data['tris_k'] + data.get('instance_tris_k', 0)
        row['total_tris_percent_delta'] = 100 * (row['total_tris_k_after'] / max(1, row['total_tris_k_before']) - 1)
        row['low_budget_ok'] = (not condition.startswith('Low') or
            (row['draws_delta'] <= 0 and row.get('instance_draws_delta', 0) <= 0 and row['total_tris_percent_delta'] <= 2.0))
        rows.append(row)
if not rows:
    raise RuntimeError('No camera statistics found')
with (ROOT / f'budget-{after}.csv').open('w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
(ROOT / f'budget-{after}.json').write_text(json.dumps({'camera_conditions': len(rows),
    'scope': 'focus subset only' if focus_subset else 'all captured cameras',
    'all_low_budget_ok': all(r['low_budget_ok'] for r in rows),
    'estimates_only_not_GPU': True, 'rows': rows}, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'{len(rows)} camera/conditions; Low budget: {all(r["low_budget_ok"] for r in rows)}')
