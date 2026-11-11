import json, subprocess, sys, types
from pathlib import Path
sys.path.insert(0, 'tools/worldgen')
from streetscape import props, furniture_textures
base = types.ModuleType('streetscape._baseline_props')
base.__package__ = 'streetscape'
exec(subprocess.check_output(['git','show','9e6e9fde:tools/worldgen/streetscape/props.py'], text=True, encoding='utf-8'), base.__dict__)
result = {}
for name, fn in [('lamp_12m', lambda p: p.lamp(12, 2)), ('lamp_old_concrete_9m', lambda p: p.lamp_old(9, 'concrete')), ('lamp_old_steel_8m', lambda p: p.lamp_old(8,'steel')), ('lamp_arc_9m', lambda p: p.lamp_arc()), ('bollard', lambda p: p.bollard())]:
    row = {}
    for label, mod in [('before',base), ('after',props)]:
        row[label] = [{'tris':sum(len(x['T']) for x in m.out()),'slots':len(m.out())} for m in fn(mod)[:2]]
    result[name] = row
out = Path('artifacts/furniture-r1')
(out/'prototype-budget.json').write_text(json.dumps(result, indent=2)+'\n')
for k,im in furniture_textures.textures().items():
    im.save(out/f'{k}.png')
# Authored close-up poses derived from actual baseline instance coordinates, unchanged between A/B.
instances = []
for f in Path('Data/raw/derived/bialystok-industrial-c/world').glob('instances_*.json'):
    d=json.loads(f.read_text()); instances.extend(d.get('instances', d.get('items',[])) if isinstance(d,dict) else d)
print('instance count',len(instances))
cams=[]
for name,e,n,proto in [('footing-slope',-727.2,75.6,'lamp_'),('old-steel',24.4,-467.9,'lamp_old_steel'),('old-concrete',356.9,-552.3,'lamp_old_concrete'),('sign-back',-250,-250,'sign_post')]:
    candidates=[x for x in instances if x['p'].startswith(proto)]
    if not candidates: continue
    it=min(candidates,key=lambda x:(x['e']-e)**2+(x['n']-n)**2)
    e,n,z=it['e'],it['n'],it['z']
    high=3 if proto=='sign_post' else 1.6
    cams.append(dict(id='furniture-'+name,type='persp',fov_deg=50,pos=[e+4,n-5,z+high],look_at=[e,n,z+high-0.1],note='ADR0102 authored close-up from baseline instance; fixed for before/after.'))
Path('Data/Regions/bialystok-industrial-c/furniture_cameras.json').write_text(json.dumps({'cameras':cams},indent=1)+'\n')
print(json.dumps(result,indent=1))
