"""Compare emitted material maps to the locked baseline, protecting all unintended atlas cells."""
from pathlib import Path
import json,numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
layout=json.loads((ROOT/'art-source/world/landmarks/fire_station_jrg2/atlas_layout.json').read_text())['atlas'];results={}
for tier in ('High','Medium','Low'):
 for name in ('BaseColor','Normal','MaskMap','Var'):
  filename='T_fire_station_'+name+'.png';before=np.array(Image.open(OUT/'baseline-materials'/tier/filename));after=np.array(Image.open(ROOT/'art-source/world/materials/fire_station'/tier/filename));assert before.shape==after.shape
  delta=np.any(before!=after,axis=2);row={'changed_pixels':int(delta.sum())}
  if name!='BaseColor':assert not delta.any(),(tier,name)
  else:
   h,w=before.shape[:2];X=(np.arange(w)+.5)/w*14;v=14-(np.arange(h)+.5)/h*14;X,v=np.meshgrid(X,v);allowed=(v>2.85)&(v<4.10)
   for key in ('brick','win_arch','win_round'):
    r=layout[key];allowed|=(X>=r['u'][0]-.12)&(X<r['u'][1]+.12)&(v>=r['v'][0]-.12)&(v<r['v'][1]+.12)
   assert not delta[~allowed].any(),(tier,'protected cell changed')
   clean=(v>=1.2)&(v<=2.6);assert not delta[clean].any(),(tier,'clean paint changed')
   row.update(protected_cells_exact=True,clean_plaster_1p2to2p6_exact=True,allowed='top flashing runoff only; brick, arch and round glass plus filter gutters')
  results[tier+'/'+name]=row
(OUT/'facade-protected-pixels.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
