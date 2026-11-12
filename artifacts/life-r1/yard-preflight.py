import json, sys
from pathlib import Path
root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/'tools/worldgen'))
from streetscape import life_props as LP
out={}
for name, value in LP.build_all().items():
    if not name.startswith(('tractor_','trailer_')): continue
    lods=[]
    for mesh in value[:2]:
        p=mesh.out()
        lods.append({'triangles':sum(len(x['T']) for x in p),'material_groups':len(p),'materials':{x['mat']:len(x['T']) for x in p}})
    out[name]=lods
Path(__file__).with_name('yard-prototype-baseline.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k in ('tractor_white','trailer_curtain_0','trailer_box_0','trailer_reefer_0')},indent=2))
