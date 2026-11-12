"""Keep only the regenerated fire-station entry in the shared tracked material spec."""
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
path=ROOT/'art-source/world/materials/materials_spec.json'
current=json.loads(path.read_text(encoding='utf-8'))
baseline=json.loads((Path(__file__).parent/'baseline-source.json').read_text(encoding='utf-8-sig'))['base']
original=json.loads(subprocess.run(['git','show',f'{baseline}:art-source/world/materials/materials_spec.json'],
    cwd=ROOT,capture_output=True,check=True).stdout)
hero=current['sets']['fire_station']
if set(hero['files'])!={'High','Medium','Low'}:
    raise RuntimeError('Generate every fire_station tier under the heavy slot before scoping the shared spec')
other={key:value for key,value in original['sets'].items() if key!='fire_station'}
def original_order(template,value):
    if isinstance(template,dict) and isinstance(value,dict):
        keys=[key for key in template if key in value]+[key for key in value if key not in template]
        return {key:original_order(template.get(key),value[key]) for key in keys}
    return value
original['sets']['fire_station']=original_order(original['sets']['fire_station'],hero)
assert other=={key:value for key,value in original['sets'].items() if key!='fire_station'}
path.write_text(json.dumps(original,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
proof={'changed_set_only':'fire_station','all_other_set_entries_preserved_from_baseline':True,
    'baseline_commit':baseline,'original_key_order_preserved':True,
    'fire_station_tiers':sorted(hero['files'])}
(Path(__file__).parent/'scoped-material-spec.json').write_text(json.dumps(proof,indent=2),encoding='utf-8')
print(proof)
