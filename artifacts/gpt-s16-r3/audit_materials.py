from pathlib import Path
import json,hashlib,difflib
from material_audit_common import strip_shadow_fields
r=Path(__file__).resolve().parent;root=r.parents[1];folder=root/'game/Assets/_Generated/World/bialystok-industrial-c/Materials'
policy_path=root/'Data/Regions/bialystok-industrial-c/shadow_caster_bias.json';policy=json.loads(policy_path.read_text());expected={'M_'+name+'.mat' for name in policy['materials']}
base=json.loads((r/'baseline-native-materials.json').read_text());now={p.relative_to(folder).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*.mat')}
changed={f for f in base if now.get(f)!=base[f]};added=sorted(set(now)-set(base));only_expected={}
for name in expected:
 old=(r/'private-native-baseline'/name).read_text();new=(folder/name).read_text();only_expected[name]=strip_shadow_fields(new)==old and '- _ShadowNormalBiasScale: 0' in new and '- _SHADOW_NORMAL_BIAS_SCALE' in new
report={'baseline_materials':len(base),'unchanged_sha256':sum(now.get(f)==sha for f,sha in base.items()),'changed':sorted(changed),'expected':sorted(expected),'added':added,'unexpected':sorted(changed-expected),'only_keyword_and_scale_changed':only_expected,'policy_sha256':hashlib.sha256(policy_path.read_bytes()).hexdigest()}
(r/'native-material-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
assert not added and changed==expected and all(only_expected.values()), 'Unexpected native material state'
