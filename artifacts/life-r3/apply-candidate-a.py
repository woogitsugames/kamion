"""Apply a bounded candidate only after the author inspects the fresh baseline."""
import ast, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).parent
review=json.loads((OUT/'BASELINE-INSPECTED.json').read_text(encoding='utf-8-sig'))
assert review['inspected'] is True
assert (OUT/'post-baseline-result.json').is_file()
assert json.loads((OUT/'post-baseline-result.json').read_text())['exit_code']==0
inputs=json.loads((OUT/'before-inputs.json').read_text(encoding='utf-8-sig'))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
for name,digest in inputs['source_sha'].items():
    assert sha(ROOT/name).lower()==digest.lower(),f'Baseline source drift: {name}'
assert sha(ROOT/'art-source/world/props/street_props.glb').lower()==inputs['library_sha'].lower()

wheel=ROOT/'tools/worldgen/streetscape/life_cars.py'
shader=ROOT/'game/Assets/_Project/Environment/Shaders/WorldPBR.shader'
before={str(p.relative_to(ROOT)):sha(p) for p in (wheel,shader)}
source=wheel.read_text(encoding='utf-8-sig')
old='''                    if ns * (2 if twin else 1) > 7:               # thin spokes: one face
                        _quad(m, face, ia, oa, ob, ib_, X)
                    else:
                        im, om = c0 + u * 0.05 + X * 0.012, c0 + u1 * r1 + X * 0.022
                        _quad(m, face, ia, oa, om, im, X - v * 0.6)
                        _quad(m, face, im, om, ob, ib_, X + v * 0.6)'''
new='''                    # ADR0089 life r3, WORKING_VALUE: two faces also on thin
                    # spokes. The wide section survives the existing 38-degree
                    # exporter crease; no global normal-policy change.
                    thin = ns * (2 if twin else 1) > 7
                    rise_inner, rise_outer = ((0.010, 0.020) if thin else
                        (max(0.020, min(0.026, wi * 0.40)), 0.012 + max(0.014, min(0.018, wo * 0.40))))
                    im = c0 + u * 0.05 + X * rise_inner
                    om = c0 + u1 * r1 + X * rise_outer
                    _quad(m, face, ia, oa, om, im, X - v * 0.6)
                    _quad(m, face, im, om, ob, ib_, X + v * 0.6)'''
assert source.count(old)==1,'Wheel patch context drift'
source=source.replace(old,new)

hlsl=shader.read_text(encoding='utf-8-sig')
weights='''                    half frontTrail = saturate(1.0h - abs(i.uv.w - 0.87h) / 0.28h);
                    half rearTrail = saturate(1.0h - abs(i.uv.w + 0.13h) / 0.28h);
                    half rearFace = saturate((-i.uv.w - 0.20h) * 8.0h);
                    half deposition = max(max(frontTrail, rearTrail), rearFace);
'''
old_vertical='''                    half vertical = exp2(-max(i.uv.z, 0.0) / falloff * 1.442695h);
'''+weights
assert hlsl.count(old_vertical)==1,'Deposition patch context drift'
hlsl=hlsl.replace(old_vertical,'''                    half vertical = exp2(-max(i.uv.z, 0.0) / falloff * 1.442695h);
''')
assert hlsl.count('                    half amount, falloff;')==1
hlsl=hlsl.replace('                    half amount, falloff;',weights+'                    half amount, falloff;')
old_falloff='                        falloff = 0.16h + 0.06h * i.carFilm.x;'
assert hlsl.count(old_falloff)==1
hlsl=hlsl.replace(old_falloff,old_falloff+'''
                        // ADR0089 life r3 A, WORKING_VALUE: broader only behind
                        // axles and on the rear. Still monotone above the sill,
                        // bounded by the existing 0.5 opacity, no new sampling.
                        falloff += deposition * (0.12h + 0.12h * i.carFilm.x)
                                 + rearFace * 0.10h * (0.25h + 0.75h * i.carFilm.x);''')
assert 'falloff = 0.32h + 0.16h * i.carFilm.x;' in hlsl
test=ROOT/'tests/gis/test_car_rim_facets.py'
assert not test.exists(),'Refuse replacing a test'
ast.parse(source)
wheel.write_text(source,encoding='utf-8',newline='\n')
shader.write_text(hlsl,encoding='utf-8',newline='\n')

test.write_text('''"""Close alloy spokes must retain two readable faces through the real exporter."""
import numpy as np
import pytest
from streetscape import life_cars as cars
from streetscape.export import crease_normals
from streetscape.props import Mesh

@pytest.mark.parametrize("style", range(5))
@pytest.mark.parametrize("side", [-1, 1])
def test_alloy_spoke_faces_survive_export_on_both_sides(style, side):
    mesh=Mesh()
    cars._wheel2(mesh, side, 0, .32, side, 22, False, 0, wst=style, rimm="rim", tyre="car_tyre")
    primitives=crease_normals(mesh.out())
    material="rim_dark" if style==3 else "rim"
    p=next(p for p in primitives if p["mat"]==material)
    triangles=p["V"][p["T"]]
    normals=p["N"][p["T"]].mean(axis=1)
    center=triangles.mean(axis=1)-np.array([side,0,.32])
    radius=np.linalg.norm(center[:,1:],axis=1)
    mask=(radius>.095)&(radius<.18)&(normals[:,0]*side>.65)
    assert mask.any()
    tangent=np.column_stack([np.zeros(mask.sum()),-center[mask,2],center[mask,1]])
    tangent/=np.linalg.norm(tangent,axis=1)[:,None]
    shading=np.einsum("ij,ij->i",normals[mask],tangent)
    assert shading.min()<-.15 and shading.max()>.15,(style,side,shading)
    for primitive in primitives:
        v=primitive["V"][primitive["T"]]
        area=np.linalg.norm(np.cross(v[:,1]-v[:,0],v[:,2]-v[:,0]),axis=1)
        assert area.min()>1e-10
''',encoding='utf-8',newline='\n')
(OUT/'candidate-a-source-changes.json').write_text(json.dumps(dict(before=before,
    after={str(p.relative_to(ROOT)):sha(p) for p in (wheel,shader)},requires_regeneration=True,
    status='candidate A applied, not generated or visually accepted'),indent=2),encoding='utf-8')
print('Candidate A applied; regeneration, targeted tests and visual review required.')
