"""Geometric evidence for actual static yard prototypes, without scene generation."""
import json,sys
from pathlib import Path
import numpy as np
root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/'tools/worldgen'))
stage=sys.argv[1] if len(sys.argv)>1 else 'baseline'
if stage=='baseline':
    import importlib.util
    spec=importlib.util.spec_from_file_location('streetscape._life_props_baseline',Path(__file__).with_name('baseline-life_props.py'))
    LP=importlib.util.module_from_spec(spec); spec.loader.exec_module(LP)
else:
    from streetscape import life_props as LP
result={}
for name,meshes in LP.build_all().items():
    if not name.startswith(('trailer_','tractor_')): continue
    lods=[]
    for mesh in meshes[:2]:
        prims=mesh.out()
        tyre=next(p for p in prims if p['mat']=='tyre')
        V,T=tyre['V'],tyre['T']
        sides={}
        for sign in (-1,1):
            tris=[V[t] for t in T if np.all(sign*V[t,0]>0)]
            intervals=sorted((float(v[:,1].min()),float(v[:,1].max())) for v in tris)
            merged=[]
            for lo,hi in intervals:
                if merged and lo<=merged[-1][1]+1e-6: merged[-1][1]=max(merged[-1][1],hi)
                else: merged.append([lo,hi])
            sides[str(sign)]=merged
        curtain=next((p for p in prims if p['mat'].startswith('trailer_curtain_')),None)
        uv_bounds=None if curtain is None else dict(min=curtain['UV'].min(axis=0).tolist(),max=curtain['UV'].max(axis=0).tolist())
        lods.append(dict(triangles=sum(len(p['T']) for p in prims),materials=[p['mat'] for p in prims],tyre_ground=float(V[:,2].min()),axle_intervals=sides,curtain_uv_bounds=uv_bounds))
    result[name]=lods
out=Path(__file__).with_name(f'prototype-{stage}.json')
out.write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k in ('trailer_curtain_0','tractor_white')},indent=2))
if stage!='baseline':
    base=json.loads(Path(__file__).with_name('prototype-baseline.json').read_text())
    for name,lods in result.items():
        for lod,(b,a) in enumerate(zip(base[name],lods)):
            assert a['materials']==b['materials'],(name,lod,'material groups changed')
        if name.startswith('trailer_'):
            assert all(len(v)==3 for v in lods[1]['axle_intervals'].values()),name
            # Ten-sided LOD0 has up to 2.7 cm faceting clearance. LOD1 must
            # touch nominal ground, with no return of the former 12 cm gap.
            assert -1e-6 <= lods[1]['tyre_ground'] < 0.01,name
            assert abs(lods[1]['tyre_ground']-lods[0]['tyre_ground'])<0.03,name
        if name.startswith('trailer_curtain_'):
            assert all(0 <= a['curtain_uv_bounds']['min'][1] < a['curtain_uv_bounds']['max'][1] < 2.7 for a in lods),name
