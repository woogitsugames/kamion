"""Compare fixed-camera SceneStats estimates, including instanced props/trees."""
import json
import re
from pathlib import Path

OUT = Path(__file__).resolve().parent


def stats(path):
    found = {}
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        m = re.match(r'(.*?): objects=(\d+) drawsEst=(\d+) shadowDrawsEst=(\d+) trisK=(\d+)', line)
        if m:
            cid, objects, draws, shadow, tris = m.groups()
            found[cid] = dict(draws=int(draws), shadow=int(shadow), tris=int(tris)*1000)
        m = re.match(r'\s+(.*?) instanced .*?: draws (\d+), instances (\d+), triangles (\d+)k', line)
        if m:
            cid, draws, instances, tris = m.groups()
            found[cid]['draws'] += int(draws)
            found[cid]['tris'] += int(tris)*1000
    return found


rows = []
for bp in sorted((OUT / 'before').glob('*/stats.txt')):
    ap = OUT / 'after' / bp.parent.name / 'stats.txt'
    if not ap.exists():
        continue
    before, after = stats(bp), stats(ap)
    assert before.keys() == after.keys(), (bp, before.keys(), after.keys())
    for cid in before:
        b, a = before[cid], after[cid]
        rows.append(dict(tier_light=bp.parent.name, camera=cid, before=b, after=a,
                         draws_delta=a['draws']-b['draws'],
                         tris_percent=round(100*(a['tris']/b['tris']-1), 3)))
(OUT / 'unity-budget.json').write_text(json.dumps(dict(
    source='Unity SceneStats CPU estimates before SRP batching; not hardware counters',
    rows=rows), indent=1)+'\n', encoding='utf-8')
for r in rows:
    print(r['tier_light'], r['camera'], 'draws delta', r['draws_delta'], 'triangles %', r['tris_percent'])
low = [r for r in rows if r['tier_light'].startswith('Low-')]
if low:
    print('LOW BUDGET', 'PASS' if all(r['draws_delta'] <= 0 and r['tris_percent'] <= 3 for r in low) else 'FAIL')
