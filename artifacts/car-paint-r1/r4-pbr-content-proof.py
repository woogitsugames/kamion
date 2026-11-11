"""Narrow private-trial proof for targeted R4 PBR generation; never touches mtimes."""
from pathlib import Path
import ast
import hashlib
import json
import sys
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
ART=ROOT/'artifacts/car-paint-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

if len(sys.argv)>1 and sys.argv[1]=='--check':
    record=json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
    assert record['private_R4_exception'] is True
    assert all(sha(ROOT/r['file'])==r['sha256'] for r in record['content'])
    print('R4 content proof unchanged; private targeted-PBR exception remains valid')
    raise SystemExit(0)

before=json.loads((ART/'r4-pbr-before-pins.json').read_text())
assert all(sha(ROOT/r['file'])==r['sha256'] for r in before['maps'])
assert all(sha(ROOT/r['file'])==r['sha256'] for r in before['sources'] if not r['file'].endswith('/sets_facade.py'))

facade=ROOT/'art-source/world/materials/_src/sets_facade.py'
original=ART/'r4-baseline-inputs/art-source/world/materials/_src/sets_facade.py'
def unrelated_ast(path):
    tree=ast.parse(path.read_text(encoding='utf-8'))
    tree.body=[n for n in tree.body if not isinstance(n,ast.FunctionDef) or n.name!='car_grime']
    for n in tree.body:
        if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='FACADE_SETS' for t in n.targets):
            keep=[j for j,key in enumerate(n.value.keys) if not isinstance(key,ast.Constant) or key.value!='car_grime_clean']
            n.value.keys=[n.value.keys[j] for j in keep]
            n.value.values=[n.value.values[j] for j in keep]
    return ast.dump(tree,include_attributes=False)
assert unrelated_ast(facade)==unrelated_ast(original),'Unrelated facade function/registry changed'

matroot=ROOT/'art-source/world/materials'
specpath=matroot/'materials_spec.json'
spec=json.loads(specpath.read_text())
assert spec['sets']['car_grime_clean']['kind']=='modulation_set'
assert spec['sets']['car_grime']['kind']=='modulation_set'
allmaps=[]
for name,s in spec['sets'].items():
    for tier,files in s['files'].items():
        for filename in files['files']:
            p=matroot/files['dir']/filename
            assert p.is_file(),p
            allmaps.append(p)
legacy=[p for p in allmaps if '/car_grime/' in p.as_posix()]
assert len(legacy)==12
new=[p for p in allmaps if '/car_grime_clean/' in p.as_posix()]
assert len(new)==12
comparisons=[]
for p in new:
    old=matroot/'car_grime'/p.parent.name/p.name.replace('car_grime_clean','car_grime')
    a=np.asarray(Image.open(old));b=np.asarray(Image.open(p))
    assert a.shape==b.shape
    if p.name.endswith(('_Normal.png','_Var.png')):
        assert np.array_equal(a,b),p
    # PNG row0 is top of the 2.5m tile. Exclude any lower film/filter footprint.
    heights=2.5*(1-(np.arange(a.shape[0])+.5)/a.shape[0])
    upper=heights>1.1
    upper_changed=int(np.count_nonzero(a[upper]!=b[upper]))
    assert upper_changed==0,(p,upper_changed)
    comparisons.append(dict(file=p.relative_to(ROOT).as_posix(),upper_changed_components=upper_changed,
                            changed_components=int(np.count_nonzero(a!=b))))

fir=ROOT/'art-source/world/landmarks/fire_station_jrg2/conifer_foliage_meta.json'
assert json.loads(fir.read_text())['applied'] is True
files=set(allmaps+[ROOT/r['file'] for r in before['sources']]+[specpath,fir])
files.update(ROOT/p for p in (
    'game/Assets/_Project/Environment/Shaders/WorldPBR.shader',
    'game/Assets/_Project/World/Import/WorldPbrMaterials.cs',
    'tools/worldgen/streetscape/life_cars.py','tools/worldgen/streetscape/export.py',
    'tools/worldgen/streetscape/materials.py'))
manifestpath=ROOT/'Data/Regions/bialystok-industrial-c/generated/world_manifest.json'
manifest=json.loads(manifestpath.read_text())
files.add(manifestpath)
files.update(ROOT/ref['file'] for c in manifest['chunks'] for ref in (c,c['low'],c['instances']))
files.update(ROOT/p for p in (
    'art-source/world/props/street_props.glb','art-source/world/props/props_meta.json',
    'art-source/world/textures/fire_station_alpha.png',
    'art-source/world/landmarks/fire_station_jrg2/fire_station_jrg2.glb',
    'art-source/world/landmarks/fire_station_jrg2/atlas_layout.json',
    'art-source/world/cc0/_raw/fir_tree_01/twig_diff.png',
    'art-source/world/cc0/_raw/fir_tree_01/twig_alpha.png'))
baseline=json.loads((ART/'r4-before-imported-source-proof.json').read_text())
for p,digest in baseline['fixture_sha256'].items():
    assert sha(ROOT/p)==digest,'Canonical vehicle fixture drift after BEFORE'
    files.add(ROOT/p)
content=[dict(file=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in sorted(files)]
out=dict(private_R4_exception=True,baseline_pngs_exact=len(before['maps']),legacy_car_grime_exact=12,
    unrelated_facade_ast_exact=True,other_src_hashes_exact=True,missing=0,
    clean_kind='modulation_set',fir_applied=True,new_map_comparisons=comparisons,content=content,
    note='Private targeted generation after canonical full baseline PBR451s. No mtime changes. Final full canonical regeneration must reproduce these products; not a claim of full PBR regeneration after R4.')
(ART/'r4-targeted-pbr-content-proof.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k not in ('content','new_map_comparisons')}))
