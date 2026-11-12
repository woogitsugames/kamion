"""Compare ADR 0112 cab evidence; estimates are not device GPU counters."""
import argparse,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--before',default='baseline');parser.add_argument('--after',default='result-0112-scan1');parser.add_argument('--output',default='comparison-0112-r2.json');options=parser.parse_args()
AFTER=ROOT/options.after
failures=[]

def read_stats(path):
 text=path.read_text(encoding='utf-8-sig');result={}
 for name,d,s,t in re.findall(r'^([^:\n]+): objects=\d+ drawsEst=(\d+) shadowDrawsEst=(\d+) trisK=(\d+)',text,re.M):
  result[name]={'regular_draws':int(d),'shadow_draws':int(s),'regular_triangles':int(t)*1000}
 for name,d,t,k in re.findall(r'^  (\S+) instanced[^:]*: draws (\d+),.*triangles (\d+)(k?)',text,re.M):
  result[name].update(instanced_draws=int(d),instanced_triangles=int(t)*(1000 if k else 1))
 for name,row in result.items():
  if 'instanced_draws' not in row or 'instanced_triangles' not in row:raise ValueError('missing instanced submission row: '+name)
 return result

def tsv(path):
 lines=[x for x in path.read_text(encoding='utf-8-sig').splitlines() if x and not x.startswith('#')]
 columns=lines[0].split('\t');return {r[0]:dict(zip(columns,r)) for r in (x.split('\t') for x in lines[1:])}

result={'scope':'Editor CPU visibility estimates, regular and instanced draws separately; rounded regular triangles. Device times UNVERIFIED.','stage_after':options.after,'states':{}}
for tier in ('Low','High'):
 for light in ('clear','overcast'):
  key=f'{tier}-{light}';a=ROOT/options.before/key;b=AFTER/key
  try:
   before=read_stats(a/'stats.txt');after=read_stats(b/'stats.txt')
   if set(before)!=set(after):failures.append(key+': camera list differs')
   if len(before)!=7:failures.append(key+': expected seven cab cameras')
   delta={n:{f:after[n][f]-v for f,v in row.items()} for n,row in before.items()}
   if tier=='Low':
    for n,d in delta.items():
     if d['regular_draws']+d.get('instanced_draws',0)>0:failures.append(key+' '+n+': draws increased')
     old=before[n]['regular_triangles']+before[n].get('instanced_triangles',0)
     new=after[n]['regular_triangles']+after[n].get('instanced_triangles',0)
     if new>old*1.02:failures.append(key+' '+n+': triangles over +2%')
   oldcfg=tsv(a/'native-mirrors/configuration.tsv');newcfg=tsv(b/'native-mirrors/configuration.tsv')
   if len(oldcfg)!=6 or set(oldcfg)!=set(newcfg):failures.append(key+': six-mirror coverage incomplete')
   for n,values in oldcfg.items():
    for field,v in values.items():
     if newcfg[n][field]!=v:failures.append(key+' '+n+': unexpected change '+field)
   oldmask=tsv(a/'native-mirrors/interior-pixels.tsv');mask=tsv(b/'native-mirrors/interior-pixels.tsv')
   if set(oldmask)!=set(oldcfg) or set(mask)!=set(oldcfg):failures.append(key+': six interior masks required before and after')
   for stage,rows in (('baseline',oldmask),('after',mask)):
    for n,row in rows.items():
     if int(row['interiorPixels'])!=0:failures.append(key+' '+n+': own interior visible in '+stage)
   oldbudget=read_stats(a/'native-mirrors/budgets.txt');newbudget=read_stats(b/'native-mirrors/budgets.txt')
   if set(oldbudget)!=set(oldcfg) or set(newbudget)!=set(oldcfg):failures.append(key+': six native mirror budgets required before and after')
   native_delta={n:{f:newbudget[n][f]-v for f,v in row.items()} for n,row in oldbudget.items()}
   if tier=='Low':
    for n,d in native_delta.items():
     if d['regular_draws']+d.get('instanced_draws',0)>0:failures.append(key+' '+n+': native mirror draws increased')
     old=oldbudget[n]['regular_triangles']+oldbudget[n].get('instanced_triangles',0)
     new=newbudget[n]['regular_triangles']+newbudget[n].get('instanced_triangles',0)
     if new>old*1.02:failures.append(key+' '+n+': native mirror triangles over +2%')
   result['states'][key]={'before':before,'after':after,'delta':delta,'mirror_configuration_before':oldcfg,'mirror_configuration_after':newcfg,'interior_before':oldmask,'interior_after':mask,'native_budget_before':oldbudget,'native_budget_after':newbudget,'native_budget_delta':native_delta}
  except (FileNotFoundError,KeyError,ValueError) as e:
   failures.append(key+': incomplete evidence: '+str(e))
try:
 before=read_stats(ROOT/options.before/'Low-route-all/stats.txt');after=read_stats(AFTER/'Low-route-all/stats.txt')
 if len(before)!=78:failures.append('route: expected complete 78-camera baseline')
 if set(before)!=set(after):failures.append('route: camera list differs')
 delta={n:{f:after[n][f]-v for f,v in row.items()} for n,row in before.items()}
 for n,d in delta.items():
  if d['regular_draws']+d['instanced_draws']>0:failures.append('route '+n+': draws increased')
  old=before[n]['regular_triangles']+before[n]['instanced_triangles'];new=after[n]['regular_triangles']+after[n]['instanced_triangles']
  if new>old*1.02:failures.append('route '+n+': triangles over +2%')
 result['all_route_cameras']={'count':len(before),'before':before,'after':after,'delta':delta}
except (FileNotFoundError,KeyError,ValueError) as e:
 failures.append('route: incomplete evidence: '+str(e))
result['failures']=failures;result['result']='FAIL' if failures else 'PASS'
(ROOT/options.output).write_text(json.dumps(result,indent=2),encoding='utf-8')
print(result['result']);print('\n'.join(failures));raise SystemExit(bool(failures))
