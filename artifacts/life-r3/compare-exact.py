"""Compare validated integer CPU estimates; retain both count components."""
import json
import sys
from validate_exact import validate, ROOT

before_stage, after_stage, tag = sys.argv[1:4]
route = set(json.loads((ROOT / 'route-camera-ids.json').read_text(encoding='utf-8-sig'))['ids'])
result, summary = {}, {}
for condition in ('Low-clear', 'Low-overcast', 'High-clear', 'High-overcast'):
    before, bm = validate(before_stage, condition)
    after, am = validate(after_stage, condition)
    assert before.keys() == after.keys()
    rows = []
    for camera, b in before.items():
        a = after[camera]
        assert b['aspect'] == a['aspect'] and b['fov'] == a['fov']
        total_b = b['worldTriangles'] + b['instanceTriangles']
        total_a = a['worldTriangles'] + a['instanceTriangles']
        delta = {k: a[k] - b[k] for k in ('worldTriangles', 'instanceTriangles', 'worldDraws', 'instanceDraws')}
        rows.append(dict(camera=camera, is_route=camera in route, before=b, after=a, delta=delta,
                         total_draw_delta=delta['worldDraws'] + delta['instanceDraws'],
                         total_tris_percent=100 * (total_a - total_b) / total_b))
    result[condition] = rows
    selected = [r for r in rows if r['is_route']]
    summary[condition] = dict(cameras=len(rows), route_cameras=len(selected), missing_route=sorted(route - before.keys()),
        max_all_tris_percent=max(r['total_tris_percent'] for r in rows),
        max_route_tris_percent=max(r['total_tris_percent'] for r in selected),
        max_world_draw_delta=max(r['delta']['worldDraws'] for r in rows),
        max_instance_draw_delta=max(r['delta']['instanceDraws'] for r in rows),
        route_over_budget=[r['camera'] for r in selected if r['total_draw_delta'] > 0 or r['total_tris_percent'] > 2])
note = 'Exact integers for the existing CPU estimate contract. World uses post-capture SceneStats frustum; instances use render-time snapshot. No GPU or phone measurement.'
(ROOT / f'{tag}-all-camera-budget.json').write_text(json.dumps(dict(note=note, conditions=result), indent=2), encoding='utf-8')
(ROOT / f'{tag}-budget-summary.json').write_text(json.dumps(dict(note=note, conditions=summary), indent=2), encoding='utf-8')
print(json.dumps(summary, indent=2))

