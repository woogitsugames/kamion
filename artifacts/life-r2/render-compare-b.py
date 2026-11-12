"""Explicit arguments without PowerShell -File array-parameter ambiguity."""
import runpy
import sys
import hashlib
import json
from pathlib import Path

sys.argv = ['compare.py', '--before', 'before-exact', '--after', 'after-b-exact', '--tag', 'b', '--exact']
runpy.run_path(str(Path(__file__).with_name('compare.py')), run_name='__main__')
root = Path(__file__).parent
checks = []
for condition in ('Low-clear', 'Low-overcast', 'High-clear', 'High-overcast'):
    for before in sorted((root / 'after-a-exact' / condition).glob('*.png')):
        if not before.stem.startswith(('g_dirt_', 'g_current_', 'g_r4_', 'r10b_', 'r10_wheel', 'r10_front', 'r10_rear')):
            continue
        after = root / 'after-b-exact' / condition / before.name
        assert after.is_file()
        b = hashlib.sha256(before.read_bytes()).hexdigest()
        a = hashlib.sha256(after.read_bytes()).hexdigest()
        checks.append(dict(condition=condition, camera=before.stem, before_sha=b, after_sha=a, png_identical=b == a))
result = dict(note='Whole PNG equality for inherited passenger-car close views. Differences may include background yard vehicles; unequal frames require inspection, not a claim of car regression.',
              count=len(checks), identical=sum(r['png_identical'] for r in checks), rows=checks)
(root / 'passenger-car-frame-check-b.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps({k: v for k, v in result.items() if k != 'rows'}))
