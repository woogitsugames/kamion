"""Exact native-material guard; only the new opt-in atlas material may be added."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[2]
out = Path(__file__).parent
base = json.loads((out/'baseline-native-materials.json').read_text())
folder = root/'game/Assets/_Generated/World/bialystok-industrial-c/Materials'
now = {str(p.relative_to(folder)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*.mat')}
changed = {p:dict(before=base[p],after=now.get(p)) for p in base if base[p] != now.get(p)}
added = sorted(now.keys()-base.keys())
unexpected = [p for p in added if Path(p).name != 'M_vehicle_lod_details.mat']
result = dict(baseline_materials=len(base), current_materials=len(now), changed=changed, added=added, unexpected_added=unexpected)
(out/'native-material-audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
if changed or unexpected:
    raise SystemExit(1)
