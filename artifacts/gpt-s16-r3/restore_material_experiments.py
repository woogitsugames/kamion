"""Undo only verified diagnostic normal-bias/cache changes before the production import."""
from pathlib import Path
import json,hashlib,shutil,difflib,re
r=Path(__file__).resolve().parent;root=r.parents[1];folder=root/'game/Assets/_Generated/World/bialystok-industrial-c/Materials';backup=r/'private-native-baseline'
base=json.loads((r/'baseline-native-materials.json').read_text());ledger=[]
for name,sha in base.items():
 p=folder/name;current=hashlib.sha256(p.read_bytes()).hexdigest()
 if current==sha:continue
 old=backup/name;assert hashlib.sha256(old.read_bytes()).hexdigest()==sha,name
 before=old.read_text();after=p.read_text()
 clean='\n'.join(line for line in after.splitlines() if line.strip() not in ('- _SHADOW_NORMAL_BIAS_SCALE','- _ShadowNormalBiasScale: 0','- _ShadowNormalBiasScale: 1'))+'\n'
 pattern=r'(?m)^  m_InvalidKeywords:.*\n(?:  - [^\n]*\n)*'
 original_invalid=re.search(pattern,before).group();current_invalid=re.search(pattern,clean).group()
 old_keys=set(re.findall(r'^  - (.+)$',original_invalid,re.M));new_keys=set(re.findall(r'^  - (.+)$',current_invalid,re.M))
 assert old_keys<=new_keys and new_keys-old_keys<={'_RECEIVESHADOWS_ON','_ZWRITE_ON'}, 'Unknown invalid-keyword change: '+name
 clean=clean.replace(current_invalid,original_invalid,1)
 if name in ('M_car_dirt_1.mat','M_car_dirt_2.mat'):clean=clean.replace('- _SrcBlend: 1\n','- _SrcBlend: 5\n')
 if clean!=before:
  (r/'unexpected-material-diff.txt').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='baseline',tofile=name)))
  raise AssertionError('Unexpected material edit, refusing restore: '+name)
 shutil.copy2(old,p);assert hashlib.sha256(p.read_bytes()).hexdigest()==sha
 ledger.append({'file':name,'experiment_sha256':current,'restored_sha256':sha})
(r/'diagnostic-material-restore.json').write_text(json.dumps(ledger,indent=2)+'\n');print('Verified experiment/cache resets:',len(ledger))
