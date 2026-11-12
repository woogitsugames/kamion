"""Compare every recorded camera, keeping renderer estimates and instance counters separate."""
from pathlib import Path
import csv
import json
import re

ROOT = Path(__file__).resolve().parent
RENDERERS = re.compile(r'^(.*?): objects=(\d+) drawsEst=(\d+) shadowDrawsEst=(\d+) trisK=(\d+)')
INSTANCES = re.compile(r'^\s+(.*?) instanced \(props\+trees\): draws (\d+), instances (\d+), triangles (\d+)k, cells (\d+), forest HLOD cells (\d+)')

def read(stage):
    result = {}
    for file in sorted((ROOT / stage).rglob('stats.txt')):
        condition = file.parent.relative_to(ROOT / stage).as_posix()
        for line in file.read_text(encoding='utf-8-sig').splitlines():
            if match := RENDERERS.search(line):
                camera, *numbers = match.groups()
                result.setdefault((condition, camera), {}).update(dict(zip(
                    ['objects', 'renderer_draws_est', 'shadow_draws_est', 'renderer_tris_k'], map(int, numbers))))
            elif match := INSTANCES.search(line):
                camera, *numbers = match.groups()
                result.setdefault((condition, camera), {}).update(dict(zip(
                    ['instance_draws', 'instances', 'instance_tris_k', 'visible_cells', 'hlod_cells'], map(int, numbers))))
    return result

before, after = read('before-all'), read('after-all')
if not before or before.keys() != after.keys():
    raise RuntimeError(f'Camera set mismatch: before={len(before)}, after={len(after)}, missing={sorted(before.keys()-after.keys())}, added={sorted(after.keys()-before.keys())}')
rows = []
for (condition, camera), old in sorted(before.items()):
    new = after[(condition, camera)]
    if old.keys() != new.keys() or 'renderer_draws_est' not in old:
        raise RuntimeError(f'Counter set mismatch: {condition} {camera}')
    row = {'condition': condition, 'camera': camera}
    for key in old:
        row[key+'_before'] = old[key]
        row[key+'_after'] = new[key]
        row[key+'_delta'] = new[key] - old[key]
    # Missing instance rows remain absent, never silently become a measured zero.
    row['instance_row_present'] = 'instance_draws' in old
    rows.append(row)
fields = list(dict.fromkeys(key for row in rows for key in row))
with (ROOT / 'all-cameras-counters.csv').open('w', newline='', encoding='utf-8-sig') as file:
    writer = csv.DictWriter(file, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
summary = {
    'camera_condition_rows': len(rows),
    'renderer_draw_increase_max': max(row['renderer_draws_est_delta'] for row in rows),
    'instance_draw_increase_max': max((row['instance_draws_delta'] for row in rows if row['instance_row_present']), default=None),
    'all_recorded_counters_identical': all(value == 0 for row in rows for key, value in row.items() if key.endswith('_delta')),
    'note': 'Renderer draws and shadows are CPU estimates before SRP batching. Triangle counts are rounded to thousands. Instance counters are recorded separately. These are not phone GPU measurements.',
}
(ROOT / 'all-cameras-counters.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
print(json.dumps(summary, indent=2, ensure_ascii=False))
