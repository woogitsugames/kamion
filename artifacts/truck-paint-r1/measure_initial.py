from pathlib import Path
import json,numpy as np
from PIL import Image
root=Path('artifacts/truck-paint-r1')
rois={'front_glass':('truck-front',(335,70,590,170)),'threequarter_glass':('truck-34',(372,155,436,197)),'gate_glass':('truck-at-gate',(654,177,704,213)),'flat_door':('truck-34',(479,208,505,234)),'roof_deflector':('truck-34',(370,110,459,131)),'day_lamp_left':('truck-front',(298,276,333,299)),'day_lamp_right':('truck-front',(600,276,629,299))}
def crop(stage,cond,cam,box):
 im=Image.open(root/stage/cond/(cam+'.png')).convert('RGB');k=im.width/960
 return np.asarray(im.crop(tuple(round(x*k) for x in box)),dtype=np.float64)
rows=[]
for cond in ['Low-overcast','High-overcast','Low-clear','High-clear','Low-lowsun','High-lowsun']:
 for name,(cam,box) in rois.items():
  a=crop('before',cond,cam,box);y=a@np.array([.2126,.7152,.0722])/255*100
  r={'condition':cond,'roi':name,'camera':cam,'roi960':box,'rgb':a.mean((0,1)).tolist(),'p50_luma_pct':float(np.median(y)),'sd_luma_pct':float(y.std()),'clip250':float(np.any(a>=250,axis=2).mean())}
  if 'glass' in name:
   b=crop('before-no-pane-fixed',cond,cam,box);z=b@np.array([.2126,.7152,.0722])/255*100
   r['no_pane_sd_pct']=float(z.std());r['sd_ratio']=float(y.std()/max(z.std(),1e-8));r['D44_threshold_pct']=.7*z.std() if 'overcast' in cond else 8.;r['D44_pass']=bool(y.std()>=r['D44_threshold_pct']);r['D34_pass']=bool(23<=np.median(y)<=45)
  if name in ['flat_door','roof_deflector']:
   b=crop('before-coat-radiance-off',cond,cam,box);d=((a-b)@np.array([.2126,.7152,.0722]))/255*100
   r['coat_delta_mean_pct']=float(d.mean());r['coat_delta_p95_pct']=float(np.percentile(d,95));r['coat_delta_max_pct']=float(d.max())
  rows.append(r)
(root/'baseline-roi-valid.json').write_text(json.dumps(rows,indent=2)+'\n')
for r in rows:
 if 'glass' in r['roi']:print(r['condition'],r['roi'],'p50/sd',round(r['p50_luma_pct'],2),round(r['sd_luma_pct'],2),'noPane',round(r['no_pane_sd_pct'],2),'ratio',round(r['sd_ratio'],2),'D34',r['D34_pass'],'D44',r['D44_pass'])
 else:print(r['condition'],r['roi'],'p50',round(r['p50_luma_pct'],2),'clip',round(r['clip250'],3),'coatMean/p95',round(r.get('coat_delta_mean_pct',0),2),round(r.get('coat_delta_p95_pct',0),2))
