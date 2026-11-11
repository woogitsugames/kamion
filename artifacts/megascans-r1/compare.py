"""Compare fixed-camera editor estimates, including instanced draws (not GPU counters)."""
import csv,json,re,sys
from pathlib import Path
from PIL import Image,ImageChops,ImageStat
ROOT=Path(__file__).parent
STAGE=sys.argv[1] if len(sys.argv)>1 else 'after'
STATIC=re.compile(r'^([^:]+): objects=(\d+) drawsEst=(\d+) shadowDrawsEst=(\d+) trisK=(\d+)')
INSTANCED=re.compile(r'^  (.+) instanced .*: draws (\d+), instances (\d+), triangles (\d+)k')
def stats(path):
 out={}
 for line in path.read_text().splitlines():
  if m:=STATIC.match(line):out[m[1]]=dict(zip(['objects','static_draws','shadow_draws','static_trisK'],map(int,m.groups()[1:])))
  elif m:=INSTANCED.match(line):out[m[1]].update(dict(zip(['instanced_draws','instances','instanced_trisK'],map(int,m.groups()[1:]))))
 for row in out.values():
  row['total_draws']=row['static_draws']+row.get('instanced_draws',0)
  row['total_trisK']=row['static_trisK']+row.get('instanced_trisK',0)
 return out
rows=[]
for tier in ['Low','High']:
 before=ROOT/'before'/(tier+'-overcast');after=ROOT/STAGE/(tier+'-overcast')
 a,b=stats(before/'stats.txt'),stats(after/'stats.txt')
 for key in sorted(a.keys()&b.keys()):
  row={'tier':tier,'camera':key}
  for field in a[key]:
   row[field+'_before']=a[key][field];row[field+'_after']=b[key][field];row[field+'_delta']=b[key][field]-a[key][field]
  p,q=before/(key+'.png'),after/(key+'.png')
  if p.exists() and q.exists():
   x,y=Image.open(p).convert('RGB'),Image.open(q).convert('RGB');diff=ImageChops.difference(x,y);row['rgb_mean_abs_delta']=sum(ImageStat.Stat(diff).mean)/3
  rows.append(row)
with (ROOT/(STAGE+'-comparison.csv')).open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
summary={tier:{'views':len(rs:=[r for r in rows if r['tier']==tier]),'total_draw_increases':[r['camera'] for r in rs if r['total_draws_delta']>0],'total_triangle_increases':[r['camera'] for r in rs if r['total_trisK_delta']>0],'max_total_draw_delta':max(r['total_draws_delta'] for r in rs),'max_total_trisK_delta':max(r['total_trisK_delta'] for r in rs)} for tier in ['Low','High']}
(ROOT/(STAGE+'-comparison.json')).write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
