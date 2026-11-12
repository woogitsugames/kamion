"""Verify a non-shipping candidate against every actual source shrub, without Blender."""
import ast
import json
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
source = ROOT/'tools/blender/world/landmarks/make_fire_station.py'
spec = ROOT/'Data/Regions/bialystok-industrial-c/generated/landmarks/fire_station_jrg2.spec.json'
tree = ast.parse(source.read_text(encoding='utf-8'))
tree.body = [n for n in tree.body if not (
    isinstance(n,ast.Import) and any(a.name in ('bpy','bmesh') for a in n.names)
    or isinstance(n,ast.Expr) and isinstance(n.value,ast.Call)
    and isinstance(n.value.func,ast.Name) and n.value.func.id == 'main')]
sys.argv = [str(source),'--','--spec',str(spec)]
ns = {'__file__':str(source)}
exec(compile(tree,str(source),'exec'),ns)
original = ns['build_thuja']
exec(compile((Path(__file__).parent/'thuja_candidate.py').read_text(),'<candidate>','exec'),ns)
candidate = ns['build_thuja']
rows=[]
for lod in (0,1):
    before,after = ns['MB'](),ns['MB']()
    for e,n,z,h,r,key in ns['SPEC']['ground']['thuja']:
        centre = ns['en_to_uvz']([e,n,z])-[0,0,.05]
        original(before,centre,h,r,key,lod)
        candidate(after,centre,h,r,key,lod)
    np.testing.assert_array_equal(before.V,after.V)
    assert before.F == after.F and before.M == after.M and before.UV == after.UV
    if lod:
        assert len(after.core_normals) == len(after.V)
        shared={}
        for index,normal in after.core_normals.items():
            assert np.isfinite(normal).all() and np.linalg.norm(normal)>0
            position=tuple(after.V[index])
            if position in shared:
                np.testing.assert_array_equal(shared[position],normal)
            shared[position]=normal
    else:
        assert before.core_normals == after.core_normals
    rows.append({'lod':lod,'shrubs':len(ns['SPEC']['ground']['thuja']),
        'triangles':sum(len(f)-2 for f in after.F),
        'geometry_uv_materials_exact':True,'custom_normal_corners':len(after.core_normals),
        'shared_position_normals_exact':True})
out=Path(__file__).parent/'thuja-candidate-proof.json'
out.write_text(json.dumps({'non_shipping_CPU_candidate':True,'rows':rows},indent=2),encoding='utf-8')
print(json.dumps(rows))
