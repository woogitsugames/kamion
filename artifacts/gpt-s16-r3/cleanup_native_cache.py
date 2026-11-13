"""Restore only proven serialization noise, retaining the three configured bias overrides."""
from pathlib import Path
import json,hashlib,shutil,difflib
from material_audit_common import normalize_invalid,strip_shadow_fields
r=Path(__file__).resolve().parent;root=r.parents[1];folder=root/'game/Assets/_Generated/World/bialystok-industrial-c/Materials';backup=r/'private-native-baseline'
policy=json.loads((root/'Data/Regions/bialystok-industrial-c/shadow_caster_bias.json').read_text());targets={'M_'+name+'.mat' for name in policy['materials']}
base=json.loads((r/'baseline-native-materials.json').read_text());ledger=[]
for name,sha in base.items():
 p=folder/name;current=hashlib.sha256(p.read_bytes()).hexdigest()
 if current==sha:continue
 old=backup/name;assert hashlib.sha256(old.read_bytes()).hexdigest()==sha,name
 before=old.read_text();after=p.read_text();normalized=normalize_invalid(after,before,name);clean=strip_shadow_fields(normalized)
 if name in ('M_car_dirt_1.mat','M_car_dirt_2.mat'):clean=clean.replace('- _SrcBlend: 1\n','- _SrcBlend: 5\n')
 if clean!=before:
  (r/'unexpected-material-diff.txt').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='baseline',tofile=name)))
  raise AssertionError('Unexpected material modification; refusing restore: '+name)
 if name in targets:
  assert '- _ShadowNormalBiasScale: 0' in normalized and '- _SHADOW_NORMAL_BIAS_SCALE' in normalized,name
  if normalized==after:continue
  p.write_text(normalized,encoding='utf-8',newline='\n')
 else:shutil.copy2(old,p)
 ledger.append({'file':name,'before_cleanup_sha256':current,'after_cleanup_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'retained_policy_override':name in targets})
(r/'native-cleanup-ledger.json').write_text(json.dumps(ledger,indent=2)+'\n');print('Cleaned proven serialization noise:',len(ledger),'files; retained configured overrides')
