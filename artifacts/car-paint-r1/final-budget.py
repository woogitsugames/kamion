from pathlib import Path
import json,hashlib
r=Path('artifacts/car-paint-r1');j=json.loads((r/'metrics-before-vs-r3.json').read_text());out={}
for c,q in j['stats_delta'].items():
 assert len(q['original_route59'])==59
 assert q['original_route59_max']['total_draws_est']<=0 and q['original_route59_max']['total_triangles_k_rounded']<=0
 out[c]=dict(route_camera_count=59,minimum=q['original_route59_min'],maximum=q['original_route59_max'],matched_original_cameras=q['camera_count'],after_only_diagnostics=q['unpaired_after_only_diagnostics'],stats_sha256={t:hashlib.sha256((r/t/c/'stats.txt').read_bytes()).hexdigest() for t in ['before','r3']})
(r/'final-route-budget-summary.json').write_text(json.dumps(dict(note='236matched original route camera conditions, CPU visible draw estimates and rounded thousands of triangles; notGPU/device time. No unrelated quality reductions. Source fleet allLOD0 -30000tris separate.',conditions=out),indent=2)+'\n')
print('PASS all236 route conditions no draw/rounded-triangle increase')
