"""Semantic hashes of protected world meshes and exact non-High instance records."""
import argparse,hashlib,json,sys
from pathlib import Path
r=Path(__file__).resolve().parent;root=r.parents[1]
sys.path.insert(0,str(r.parent/'gpt-s16-r1'))
from audit_glb import load,digest,tris
p=argparse.ArgumentParser();p.add_argument('stage',choices=['baseline','after']);args=p.parse_args()
m=json.loads((root/'Data/Regions/bialystok-industrial-c/generated/world_manifest.json').read_text())
record={'protected':{},'plots':{},'non_high':{},'gardens':[]}
for chunk in m['chunks']:
 for item in [chunk,chunk.get('low')]:
  if not item:continue
  file=item['file'];nodes=load(root/file)
  for name,prims in nodes.items():
   key=file+':'+name
   if name in ('plots','plots_low'):
    record['plots'][key]={'tris':tris(prims),'materials':[x['material'] for x in prims]}
   else:record['protected'][key]=digest(prims)
 f=chunk['instances']['file'];rows=json.loads((root/f).read_text())['instances']
 low=[x for x in rows if str(x.get('tier','')).lower()!='high']
 record['non_high'][f]={'count':len(low),'sha256':hashlib.sha256(json.dumps(low,sort_keys=True,separators=(',',':')).encode()).hexdigest()}
 record['gardens'] += [x for x in rows if str(x.get('tier','')).lower()=='high' and x.get('src','').startswith('plot:')]
(r/f'{args.stage}-world-audit.json').write_text(json.dumps(record,indent=2)+'\n')
if args.stage=='after':
 base=json.loads((r/'baseline-world-audit.json').read_text());fail=[]
 if base['protected']!=record['protected']:fail.append('Protected mesh changed')
 if base['non_high']!=record['non_high']:fail.append('Non-high instance records changed')
 libraries=json.loads((r/'baseline-libraries.json').read_text())
 changed_libraries=[file for file,value in libraries.items() if hashlib.sha256((root/file).read_bytes()).hexdigest()!=value]
 if changed_libraries:fail.append('Prototype or atlas library changed: '+str(changed_libraries))
 if base['plots'].keys()!=record['plots'].keys():fail.append('Plot renderer groups changed')
 for key,value in base['plots'].items():
  if record['plots'].get(key,{}).get('materials')!=value['materials']:fail.append('Plot material group changed: '+key)
 def identity(rows):return [{k:v for k,v in x.items() if k not in ('h','garden_canopy_width')} for x in rows]
 if identity(base['gardens'])!=identity(record['gardens']):fail.append('Garden identity/placement/tier changed')
 result={'protected_meshes':len(base['protected']),'non_high_instances':sum(x['count'] for x in record['non_high'].values()),'garden_instances':len(record['gardens']),'plot_groups':len(record['plots']),'plot_tri_delta':sum(x['tris'] for x in record['plots'].values())-sum(x['tris'] for x in base['plots'].values()),'failures':fail}
 (r/'world-integrity.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));assert not fail,fail
else:print(json.dumps({'protected_meshes':len(record['protected']),'non_high_chunks':len(record['non_high']),'garden_instances':len(record['gardens']),'plot_groups':len(record['plots'])}))
