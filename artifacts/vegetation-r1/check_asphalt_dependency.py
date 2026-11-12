import hashlib, json, subprocess
from pathlib import Path
root=Path.cwd(); main=Path('C:/Users/matma/Documents/Claude/kamion')
p='art-source/world/materials/materials_spec.json'
original=json.loads(subprocess.check_output(['git','show','4c9905b1:'+p],text=True))
current=json.loads((root/p).read_text(encoding='utf-8-sig'))
a=original['sets'].get('asphalt_detail_photo'); b=current['sets'].get('asphalt_detail_photo')
files=[]
if a:
 for tier,entry in a['files'].items():
  for name in entry['files']:
   rel=Path('art-source/world/materials')/entry['dir']/name
   local,source=root/rel,main/rel
   same=local.exists() and source.exists() and hashlib.sha256(local.read_bytes()).digest()==hashlib.sha256(source.read_bytes()).digest()
   files.append({'file':str(rel),'matches_main':same})
report={'spec_entry_retained':a is not None and a==b,'files':files,'all_files_match_main':bool(files) and all(f['matches_main'] for f in files)}
Path('artifacts/vegetation-r1/asphalt-dependency-proof.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
if not(report['spec_entry_retained'] and report['all_files_match_main']): raise SystemExit(1)
