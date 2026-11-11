from pathlib import Path
import sys,numpy as np,json
from PIL import Image
sys.path.insert(0,'tools/worldgen')
from streetscape import life_cars as L
root=Path('artifacts/car-paint-r1')
a=np.asarray(Image.open('art-source/world/materials/car_grime/Medium/T_car_grime_MaskMap.png'))[:,:,3]/255
p=next(p for p in L.car('hatch','black')[0].out() if p['mat'].startswith('car_paint'))
v=np.asarray(p['V']);t=np.asarray(p['T']);uv=np.asarray(p['UV']);tr=v[t];n=np.cross(tr[:,1]-tr[:,0],tr[:,2]-tr[:,0]);area=np.linalg.norm(n,axis=1)/2;n=n/np.maximum(2*area[:,None],1e-8);uc=uv[t].mean(axis=1)
def ss(a,b,x):
 q=np.clip((x-a)/(b-a),0,1);return q*q*(3-2*q)
rows=[]
for level in [0,1/3,2/3,1]:
 phase=.471
 U=(uc[:,0]/4+phase)%1; V=(uc[:,1]/4)%1
 ma=a[np.minimum(((1-V)*a.shape[0]).astype(int),a.shape[0]-1),np.minimum((U*a.shape[1]).astype(int),a.shape[1]-1)]
 f=np.clip((.68-ma)/.35,0,1)*(1-ss(1.3,1.5,uc[:,1]));top=.32+.3*level;op=f*level*(1-ss(top-.08,top+.08,uc[:,1]))*.65
 side=np.abs(n[:,2])<.45
 rows.append(dict(level=level,vertical_painted_area_m2=float(sum(area[side])),mean_opacity=float(np.average(op[side],weights=area[side])),area_opacity_above_point1_m2=float(sum(area[side&(op>.1)])),max_opacity=float(op.max())))
print(json.dumps(rows,indent=2));(root/'r1-film-cpu-coverage.json').write_text(json.dumps(dict(note='CPU triangle-centroid samples, authored car_hatch_black LOD0 UV metres; Medium actual mask, source matches GLB export/import V double flip; not pixel/GPU proof. Phase illustrative .471, not each real instance.',samples=rows),indent=2)+'\n')
