from pathlib import Path
import json,hashlib,difflib
r=Path(__file__).resolve().parent;root=r.parents[1]
base=json.loads((r/'baseline-native-materials.json').read_text());folder=root/'game/Assets/_Generated/World/bialystok-industrial-c/Materials'
now={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.glob('*.mat')}
changed=[f for f in base if now.get(f)!=base[f]];added=sorted(set(now)-set(base));unexpected=[f for f in changed if f!='M_viaduct_concrete.mat']
p=folder/'M_viaduct_concrete.mat';old=(r/'private-native-baseline'/p.name).read_text();new=p.read_text()
clean='\n'.join(line for line in new.splitlines() if line.strip() not in ('- _SHADOW_NORMAL_BIAS_SCALE','- _ShadowNormalBiasScale: 0'))+'\n'
only_expected=clean==old.replace('\r\n','\n')
report={'baseline_materials':len(base),'unchanged_sha256':sum(now.get(f)==sha for f,sha in base.items()),'changed':changed,'added':added,'unexpected':unexpected,'viaduct_only_keyword_and_scale_changed':only_expected}
(r/'native-material-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
if not only_expected:(r/'native-viaduct-diff.txt').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='before',tofile='after')))
assert not added and not unexpected and only_expected, 'Unexpected native material changes; inspect before cleanup'
