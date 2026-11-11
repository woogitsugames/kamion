"""Matched complete-frame QA, <=960px sheets and camera-by-camera estimates; no hidden image calibration."""
import argparse,csv,json,re
from pathlib import Path
from PIL import Image,ImageDraw
p=argparse.ArgumentParser();p.add_argument('phase');a=p.parse_args();O=Path(__file__).resolve().parent;dest=O/(a.phase+'-sheets');dest.mkdir(exist_ok=True);rows=[];inventory={}

def stats(path):
 lines=path.read_text().splitlines();out={}
 for line in lines:
  m=re.match(r'([^:]+): objects=\d+ drawsEst=(\d+) shadowDrawsEst=(\d+) trisK=(\d+)',line)
  if m:out[m[1]]={'static_draws':int(m[2]),'shadow_draws':int(m[3]),'static_trisK':int(m[4]),'instance_draws':0,'instance_trisK':0}
  m=re.match(r'  (.+) instanced .*?: draws (\d+),.*?triangles (\d+)k',line)
  if m and m[1] in out:out[m[1]].update(instance_draws=int(m[2]),instance_trisK=int(m[3]))
 for x in out.values():x['total_drawsEst']=x['static_draws']+x['instance_draws'];x['total_trisK']=x['static_trisK']+x['instance_trisK']
 return out

for tier in ('Low','High'):
 for light in ('clear','overcast'):
  condition=tier+'-'+light;folder=O/a.phase/condition
  if not (folder/'stats.txt').exists():continue
  before=stats(O/'before'/condition/'stats.txt');after=stats(folder/'stats.txt');imgs=sorted(folder.glob('*.png'));inventory[condition]={'PNGs':len(imgs),'camera_ids':[im.stem for im in imgs]}
  for cam,new in after.items():
   old=before[cam];row={'condition':condition,'camera':cam}
   for k in new:row[k+'_before']=old[k];row[k+'_after']=new[k];row[k+'_delta']=new[k]-old[k]
   rows.append(row)
  for page in range((len(imgs)+7)//8):
   sheet=Image.new('RGB',(960,960),'white');d=ImageDraw.Draw(sheet);d.text((5,5),a.phase+' '+condition+' / complete frames / NO crop or exposure normalization',fill='black')
   for i,path in enumerate(imgs[page*8:page*8+8]):
    im=Image.open(path).convert('RGB');im.thumbnail((470,215));x=(i%2)*480;y=30+(i//2)*230;sheet.paste(im,(x,y));d.text((x+4,y+215),path.stem,fill='black')
   sheet.save(dest/(condition+f'-contact{page+1:02}.jpg'),quality=92)
  for cam in ('fire-station-ref7197','fire-station-route','fire-station-abeam','fire-station-above'):
   if not (folder/(cam+'.png')).exists():continue
   sheet=Image.new('RGB',(960,940),'white');d=ImageDraw.Draw(sheet)
   for row,phase in enumerate(('before',a.phase)):
    im=Image.open(O/phase/condition/(cam+'.png')).convert('RGB');im.thumbnail((960,440));sheet.paste(im,(0,row*470+25));d.text((5,row*470+4),condition+' '+cam+' / '+phase,fill='black')
   sheet.save(dest/(condition+'-'+cam+'-before-after.jpg'),quality=95)
assert rows,'No completed conditions'
with (dest/'comparison.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
low=[r for r in rows if r['condition'].startswith('Low')];high=[r for r in rows if r['condition'].startswith('High')]
summary={'phase':a.phase,'inventory':inventory,'matched_views':len(rows),'notes':['Estimates before SRP batching; actual shader pass/GPU cost may differ.','No device/temporal inference from staticEditor frames.'],'Low':{'views':len(low),'max_local_draw_delta':max([r['total_drawsEst_delta'] for r in low],default=None),'max_local_trisK_delta':max([r['total_trisK_delta'] for r in low],default=None),'peak_before_draws':max([r['total_drawsEst_before'] for r in low],default=None),'peak_after_draws':max([r['total_drawsEst_after'] for r in low],default=None)},'High':{'views':len(high),'max_local_draw_delta':max([r['total_drawsEst_delta'] for r in high],default=None),'max_local_trisK_delta':max([r['total_trisK_delta'] for r in high],default=None)}}
(dest/'comparison.json').write_text(json.dumps({'summary':summary,'views':rows},indent=2));print(json.dumps(summary,indent=2))
