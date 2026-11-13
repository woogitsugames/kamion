"""Restore only proven Unity serialization noise in this worktree's cached materials."""
from pathlib import Path
import json,hashlib,shutil,difflib
r=Path(__file__).resolve().parent;root=r.parents[1]
folder=root/'game/Assets/_Generated/World/bialystok-industrial-c/Materials';backup=r/'private-native-baseline'
base=json.loads((r/'baseline-native-materials.json').read_text());ledger=[]
for name,sha in base.items():
 if name=='M_viaduct_concrete.mat':continue
 p=folder/name;current=hashlib.sha256(p.read_bytes()).hexdigest()
 if current==sha:continue
 old=backup/name;assert hashlib.sha256(old.read_bytes()).hexdigest()==sha,name
 before=old.read_text();after=p.read_text()
 clean='\n'.join(line for line in after.splitlines() if line.strip()!='- _ShadowNormalBiasScale: 1')+'\n'
 if name in ('M_car_dirt_1.mat','M_car_dirt_2.mat'):clean=clean.replace('- _SrcBlend: 1\n','- _SrcBlend: 5\n')
 assert clean==before, 'Unexpected material modification; refusing restore: '+name
 difference=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='baseline',tofile='Unity cache'))
 shutil.copy2(old,p)
 assert hashlib.sha256(p.read_bytes()).hexdigest()==sha
 ledger.append({'file':name,'before_cleanup_sha256':current,'restored_sha256':sha,'serialization_diff':difference})
(r/'native-cleanup-ledger.json').write_text(json.dumps(ledger,indent=2)+'\n');print('Restored proven cache serialization noise:',len(ledger))
