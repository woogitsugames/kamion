import csv,json,hashlib,subprocess,shutil
from pathlib import Path
from datetime import datetime
p=Path(__file__).resolve().parent;root=p.parents[1]
comparisons=json.loads((p/'stats-comparison.json').read_text())
fields=['variant','camera','before_static_draws','after_static_draws','before_instance_draws','after_instance_draws','before_triangles_k','after_triangles_k','delta_draws','delta_triangles_percent']
with (p/'all-camera-costs.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
 for variant,rows in comparisons.items():
  for camera,r in rows.items():
   w.writerow(dict(variant=variant,camera=camera,before_static_draws=r['before']['static_draws'],after_static_draws=r['after']['static_draws'],before_instance_draws=r['before'].get('instance_draws',0),after_instance_draws=r['after'].get('instance_draws',0),before_triangles_k=r['before']['total_triangles_k'],after_triangles_k=r['after']['total_triangles_k'],delta_draws=r['delta_draws'],delta_triangles_percent=r['delta_triangles_percent']))
paths=['tools/worldgen/streetscape/vegetation.py','tools/worldgen/streetscape/plantings.py','game/Assets/_Project/Rendering/Shaders/VegetationGround.hlsl','game/Assets/_Project/Environment/Shaders/WorldPBR.shader','game/Assets/_Project/Rendering/Shaders/WorldSurface.shader','game/Assets/_Project/Rendering/Shaders/Vegetation.shader','Data/Regions/bialystok-industrial-c/buildings_r10_cameras.json']
proof=dict(candidate='D51 tree points',sha=subprocess.check_output(['git','rev-parse','HEAD'],text=True,cwd=root).strip(),files={x:hashlib.sha256((root/x).read_bytes()).hexdigest() for x in paths},counts={stage:len(list((p/stage).rglob('*.png'))) for stage in ['before','after']},paired_photos=len(list((p/'photo-pairs').glob('*.jpg'))),camera_comparisons=sum(len(x) for x in comparisons.values()),all_draw_deltas_zero=all(r['delta_draws']==0 for rows in comparisons.values() for r in rows.values()),all_triangle_deltas_zero=all(r['delta_triangles_percent']==0 for rows in comparisons.values() for r in rows.values()),notes=['Editor estimates only; no A16 GPU timing','Photo poses class B WORKING_VALUE; sources and licenses in photo-references.json','Control baseline reuses verified r1 B; SBS images are fresh'])
low=[r for variant, rows in comparisons.items() if variant.startswith('Low-') for r in rows.values()]
proof.update(max_low_draw_delta=max((r['delta_draws'] for r in low),default=None),
             max_low_triangle_percent=max((r['delta_triangles_percent'] for r in low),default=None),
             budget_precision='Editor draws estimates and integer trisK; not GPU timings')
(p/'test-results').mkdir(exist_ok=True)
started=datetime.fromisoformat(json.loads((p/'session.json').read_text())['started_at']).timestamp()
results=[f for f in (root/'artifacts/tests').glob('editmode-*.xml') if f.stat().st_mtime >= started]
if results:
 f=max(results,key=lambda f:f.stat().st_mtime)
 shutil.copyfile(f,p/'test-results'/f.name)
 proof['editmode_evidence']=f.name
else:
 proof['editmode_evidence']='PENDING: no EditMode result from this round'
(p/'evidence-summary.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in proof.items() if k not in ['files','notes']}))
