import json,hashlib,argparse
from pathlib import Path
r=Path(__file__).resolve().parent;root=r.parents[1]
p=argparse.ArgumentParser();p.add_argument('stage',choices=['baseline','after']);a=p.parse_args()
m=json.loads((root/'Data/Regions/bialystok-industrial-c/generated/world_manifest.json').read_text());files=[]
for c in m['chunks']:
 files += [c['file'],c['low']['file'],c['instances']['file']]
files += ['art-source/world/landmarks/viaduct_biezenstwa/viaduct_biezenstwa.glb']
result={f:hashlib.sha256((root/f).read_bytes()).hexdigest() for f in sorted(set(files))}
(r/(a.stage+'-raw-sha256.json')).write_text(json.dumps(result,indent=2)+'\n')
print('Fingerprinted',len(result),'raw world files')
if a.stage=='after':
 base=json.loads((r/'baseline-raw-sha256.json').read_text());changed=[f for f in result if result[f]!=base.get(f)]
 (r/'raw-integrity.json').write_text(json.dumps({'files':len(result),'changed':changed},indent=2)+'\n');print('Changed raw files',changed)
