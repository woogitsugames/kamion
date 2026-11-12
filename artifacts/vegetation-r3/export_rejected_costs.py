"""All baseline cameras plus labelled probes; no fabricated after matrix."""
import csv
import json
import runpy
from pathlib import Path

here = Path(__file__).resolve().parent
stats = runpy.run_path(str(here/'review_images.py'))['stats']
rows = []
for stage in ('before', 'candidate-a-rejected', 'probe', 'diagnostic-maple-height', 'restored-probe'):
    for path in sorted((here/stage).rglob('stats.txt')):
        group = path.parent.name
        for camera, values in stats(path).items():
            rows.append(dict(stage=stage, group=group, camera=camera, **values))
with (here/'all-camera-costs.csv').open('w', newline='', encoding='utf-8') as stream:
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
counts = {stage: sum(r['stage']==stage for r in rows) for stage in sorted({r['stage'] for r in rows})}
if counts.get('before') != 368:
    raise SystemExit(f'Unexpected baseline camera count: {counts}')
result = dict(rows_by_stage=counts,
    note='Baseline includes 268 reused control frames with provenance and 100 fresh B-pose frames. Candidates have probes only; no full after matrix or all-camera candidate budget acceptance. Static and instance draws are separate; integer trisK precision; not GPU timing.')
(here/'camera-cost-scope.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
print(json.dumps(result, indent=2))
