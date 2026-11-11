from pathlib import Path
import json
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[1]
GEN=REPO/'Data/Regions/bialystok-industrial-c/generated'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
a=read(ROOT/'baseline-generated/world_manifest.json')
b=read(GEN/'world_manifest.json')
print('Manifest keys',a.keys())
proof={}
for key in ('chunks',):
    proof[key+'_exact']=a[key]==b[key]
proof['roads_qa_exact']=read(ROOT/'baseline-generated/roads_qa.json')==read(GEN/'roads_qa.json')
proof['changed_material_names']=[k for k in a['materials'] if a['materials'][k]!=b['materials'].get(k)]
old=np.asarray(Image.open(ROOT/'baseline-asset/fire_station_alpha.png'))
new=np.asarray(Image.open(REPO/'art-source/world/textures/fire_station_alpha.png'))
proof['alpha_channel_every_pixel_exact']=bool(np.array_equal(old[:,:,3],new[:,:,3]))
proof['hero_tris_before']=read(ROOT/'baseline-asset/fire_station_jrg2_meta.json')['tris']
proof['hero_tris_after']=read(REPO/'art-source/world/landmarks/fire_station_jrg2/fire_station_jrg2_meta.json')['tris']
budget=read(ROOT/'budget-after.json')
low=[r for r in budget['rows'] if r['condition'].startswith('Low')]
proof['Low_conditions']=len(low)
proof['Low_max_mesh_draw_delta']=max(r['draws_delta'] for r in low)
proof['Low_max_instance_draw_delta']=max(r['instance_draws_delta'] for r in low)
proof['Low_max_total_tris_percent_delta']=max(r['total_tris_percent_delta'] for r in low)
proof['all_192_camera_conditions']=budget['camera_conditions']==192
proof['all_low_budget_ok']=budget['all_low_budget_ok']
proof['world_fallback_true']='fallback=True' in (ROOT/'round2-world.log').read_text(encoding='utf-8-sig')
(ROOT/'final-protected-proof.json').write_text(json.dumps(proof,indent=2),encoding='utf-8')
print(json.dumps(proof,indent=2))
