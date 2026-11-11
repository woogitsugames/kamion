"""CPU checks for inactive R4 sources. Not a shader or Unity visual PASS."""
from pathlib import Path
import importlib.util
import json
import re
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
ART=ROOT/'artifacts/car-paint-r1'
sys.path.insert(0,str(ROOT/'tools/worldgen'))
sys.path.insert(0,str(ROOT/'art-source/world/materials/_src'))
from streetscape import life_cars as LC
from streetscape.export import crease_normals
import sets_facade as original

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

model=load('r4_model',ART/'r4-model.py')
draft=load('streetscape.r4_life_cars',ART/'r4-inactive-source/tools/worldgen/streetscape/life_cars.py')
facade=load('r4_facade',ART/'r4-inactive-source/art-source/world/materials/_src/sets_facade.py')
shader=(ART/'r4-inactive-source/game/Assets/_Project/Environment/Shaders/WorldPBR.shader').read_text()
compact=re.sub(r'\s+','',shader)
for expression in (
    'halfamount=0.08h+0.92h*i.carFilm.x;',
    'halffalloff=0.16h+0.06h*i.carFilm.x;',
    'halfvertical=exp2(-max(i.uv.z,0.0)/falloff*1.442695h);',
    'halffrontTrail=saturate(1.0h-abs(i.uv.w-0.87h)/0.28h);',
    'halfrearTrail=saturate(1.0h-abs(i.uv.w+0.13h)/0.28h);',
    'halfrearFace=saturate((-i.uv.w-0.20h)*8.0h);',
    'carFilmOpacity=0.5h*amount*vertical*(0.72h+0.28h*deposition)*(1.0h-keepUpper);',
    'uintlevel=h<429496730u?0u:(h<1932735283u?1u:(h<3435973837u?2u:3u));',
):
    assert expression in compact,expression
assert 'legacyFilm/expectedFilm' not in compact

old=original.car_grime(n=1024)
legacy=facade.car_grime(n=1024)
clean=facade.car_grime(n=1024,lower_film=False)
fields=('albedo','height','rough','elem_id','joint')
legacy_equal={k:bool(np.array_equal(getattr(old,k),getattr(legacy,k))) for k in fields}
assert all(legacy_equal.values())
_,yy=old.c.xy()
upper=2.5-yy>1.1
assert np.array_equal(clean.albedo[upper],old.albedo[upper]),'upper albedo changed'
assert np.array_equal(clean.rough[upper],old.rough[upper]),'upper roughness changed'
assert np.array_equal(clean.height,old.height),'peel height changed'
assert np.all(clean.rough<=old.rough),'removed film unexpectedly rougher'

rows=[]
max_quant_opacity_error=0.0
max_quant_height_error=0.0
for body,d in {**LC.CARS,'van':LC.VAN}.items():
    for colour in (LC.VAN_COLOURS if body=='van' else LC.CAR_COLOURS):
        source=LC.van(colour) if body=='van' else LC.car(body,colour)
        name=f'van_{colour}' if body=='van' else f'car_{body}_{colour}'
        for lod,mesh in enumerate((source[0],source[1],source[3])):
            before=crease_normals(mesh.out())
            after=draft.paint_deposition(before,name)
            assert len(before)==len(after)
            for p,q in zip(before,after):
                assert p['mat']==q['mat']
                for key in ('V','T','UV','N'):
                    assert np.array_equal(p[key],q[key]),(name,lod,key)
                if not p['mat'].startswith('car_paint_'):
                    assert 'UV1' not in q
                    continue
                uv=q['UV1'];v=q['V'];tri=q['T']
                assert np.allclose(uv[:,0],v[:,2]-d['sill'],atol=1e-12)
                assert np.allclose(uv[:,1],(v[:,1]-(d['L']/2-d['foh']-d['wb']))/d['wb'])
                # Exact affine height at interior points, including large triangles.
                bary=np.array([.2,.3,.5])
                point=np.einsum('tvk,v->tk',v[tri],bary)
                interp=np.einsum('tvk,v->tk',uv[tri],bary)
                assert np.allclose(interp[:,0],point[:,2]-d['sill'],atol=1e-12)
                quant=np.einsum('tvk,v->tk',uv.astype(np.float16).astype(np.float32)[tri],bary)
                max_quant_height_error=max(max_quant_height_error,float(np.max(np.abs(quant[:,0]-interp[:,0]))))
                for level in range(4):
                    exact=model.opacity(interp[:,0],model.longitudinal_weight(interp[:,1]),level)
                    actual=model.opacity(quant[:,0],model.longitudinal_weight(quant[:,1]),level)
                    max_quant_opacity_error=max(max_quant_opacity_error,float(np.max(np.abs(actual-exact))))
                # Check the affine longitudinal mask cannot overpower height falloff.
                a=np.concatenate([v[tri][:,:,[1,2]],np.ones((len(tri),3,1))],axis=2)
                good=np.abs(np.linalg.det(a))>1e-9
                if np.any(good):
                    slope=np.linalg.solve(a[good],uv[tri][good,:,1][...,None])[:,1,0]
                    assert np.allclose(slope,0,atol=1e-8),(name,lod,float(np.abs(slope).max()))
            rows.append(dict(prototype=name,lod=lod,vertices=sum(len(p['V']) for p in before),
                             native_stride_increase_bytes=4,
                             native_extra_bytes_estimate=4*sum(len(p['V']) for p in before)))

for weight in (0,.25,.5,1):
    h=np.linspace(0,1.5,300)
    for level in range(4):
        value=model.opacity(h,weight,level)
        assert np.all(np.diff(value)<=0)
        assert value.max()<=.5
        assert value[0]>0

rng=np.random.default_rng(2026)
origins=(rng.integers(-9600,9600,(100000,2))/8).astype(np.float32)
rect=np.array([-1024,-1024],np.float32)
levels,phase=model.film_hash(origins,rect)
counts=np.bincount(levels,minlength=4)
assert np.all(np.abs(counts/len(levels)-np.array([.1,.35,.35,.2]))<.01)
for shift in ([256,512],[-1024,1024]):
    ll,pp=model.film_hash(origins+np.array(shift,np.float32),rect+np.array(shift,np.float32))
    # Random floats may lie on quantization boundaries; report rather than conceal.
    assert np.array_equal(ll,levels),'float32 rebasing changed level'
    assert np.array_equal(pp,phase),'float32 rebasing changed phase'

assert max_quant_height_error < .001
assert max_quant_opacity_error < .001
manifest=json.loads((ROOT/'Data/Regions/bialystok-industrial-c/generated/world_manifest.json').read_text())
instances=[]
for chunk in manifest['chunks']:
    instances.extend(i for i in json.loads((ROOT/chunk['instances']['file']).read_text())['instances']
                     if i['p'].startswith(('car_','van_')))
poses=np.asarray([[i['e'],i['n']] for i in instances],dtype=np.float32)
actual_levels,actual_phase=model.film_hash(poses,rect)
shift_cases=[]
for shift in ([1024,0],[-1024,1024],[4096,-4096],[-4096,4096],[512.25,-2048.75]):
    sh=np.asarray(shift,np.float32)
    ll,pp=model.film_hash(poses+sh,rect+sh)
    mismatches=int(np.count_nonzero((ll!=actual_levels)|(pp!=actual_phase)))
    shift_cases.append(dict(shift=shift,mismatches=mismatches))
assert not any(c['mismatches'] for c in shift_cases)

out=dict(status='CPU-only inactive model PASS; compile/GPU/appearance UNVERIFIED',
         candidate_source_expression_contract=True,
         gpu_binding_uv_v_conversion_and_keep_upper='UNVERIFIED: actual opacity/UV readback required after import',
         legacy_fields_exact=legacy_equal,upper_albedo_roughness_exact=True,peel_height_exact=True,
         source_lod_rows=len(rows),geometry_uv0_indices_normals_materials_exact=True,
         barycentric_height_and_monotonic_bound=True,
         total_native_extra_bytes_estimate=sum(r['native_extra_bytes_estimate'] for r in rows),
         note='Native estimate includes every group in each affected prototype LOD; actual descriptor/import pending',
         hash_exact_eighth_metre_float32_count=len(levels),distribution_counts=counts.tolist(),
         maximum_float16_barycentric_height_error_m=max_quant_height_error,
         maximum_float16_barycentric_opacity_error=max_quant_opacity_error,
         actual_cpu_instance_count=len(instances),
         actual_cpu_distribution_counts=np.bincount(actual_levels,minlength=4).tolist(),
         actual_cpu_rebase_cases=shift_cases,rows=rows)
(ART/'r4-inactive-tests.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k!='rows'}))
