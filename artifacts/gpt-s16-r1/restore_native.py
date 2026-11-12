"""Restore only audited Unity serialization side effects after all r1 Unity runs."""
import difflib,json,shutil
from pathlib import Path
r=Path(__file__).resolve().parent
world=r.parents[1]/'game/Assets/_Generated/World/bialystok-industrial-c/Materials'
audit=json.loads((r/'native-material-audit.json').read_text())
allowed={'M_car_dirt_1.mat','M_car_dirt_2.mat','M_sign_G390e84fe0.mat','M_sign_G3d34c990e.mat','M_sign_G3ee8d02e9.mat','M_sign_OB_7c1f064e.mat','M_sign_OB_a8034096.mat'}
assert set(audit['changed'])<=allowed, audit['changed']
shutil.copyfile(r/'native-material-audit.json',r/'native-material-before-cleanup.json')
changes={}
for name in audit['changed']:
 old=r/'private-native-materials'/name;current=world/name
 changes[name]=list(difflib.unified_diff(old.read_text().splitlines(),current.read_text().splitlines(),fromfile='baseline',tofile='unity-side-effect',lineterm=''))
 shutil.copyfile(old,current)
(r/'native-cleanup-ledger.json').write_text(json.dumps(changes,indent=2)+'\n')
print('Restored audited native cache files:',len(changes))
