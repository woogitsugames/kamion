"""Reuse locked material/UV clean-paint masks; report heights separately to expose plant occlusion."""
import argparse,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
p=argparse.ArgumentParser();p.add_argument('phase');a=p.parse_args();O=Path(__file__).resolve().parent;records={};out=O/(a.phase+'-paint');out.mkdir(exist_ok=True)
for tier in ('Low','High'):
 data=np.load(O/'before-roi'/(tier+'-paint-material-masks.npz'));label,height=data['label'],data['height']
 for light in ('clear','overcast'):
  path=O/a.phase/(tier+'-'+light)/'fire-station-ref7197.png'
  if not path.exists():continue
  im=Image.open(path).convert('RGB');rgb=np.array(im);view=rgb.copy();row={}
  for k,name in {1:'gable',2:'wing',3:'tower'}.items():
   row[name]={}
   for band,keep in {'all_clean_above2m':label==k,'matched_z2to5':(label==k)&(height>=2)&(height<5),'matched_z5to8':(label==k)&(height>=5)&(height<8)}.items():
    pixels=rgb[keep]
    if not len(pixels):continue
    row[name][band]={'pixels':len(pixels),'median_rgb_srgb':np.median(pixels,axis=0).tolist(),'mean_rgb_srgb':pixels.mean(0).tolist(),'median_luma_srgb':float(np.median(pixels@np.array([.2126,.7152,.0722])))}
   keep=(label==k)&(height>=5)&(height<8);color={1:[255,0,0],2:[0,255,0],3:[255,0,255]}[k];view[keep]=(.5*view[keep]+.5*np.array(color)).astype('uint8')
  view=Image.fromarray(view);view.thumbnail((960,960));view.save(out/(tier+'-'+light+'-z5to8-masks.jpg'),quality=95);records[tier+'-'+light]=row
(out/'metrics.json').write_text(json.dumps({'method':'EXACT locked baseline material/UV clean-paint masks reused. Report z5-8 band to avoid lower changedplants; overlays require validation. No RGB threshold filters hide dark paint.','results':records},indent=2));print(json.dumps({k:{n:b.get('matched_z5to8') for n,b in r.items()} for k,r in records.items()},indent=2))
