import hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/worldgen'))
from streetscape import fab_details as FD

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    manifest=ROOT/'Data/Regions/bialystok-industrial-c/generated/world_manifest.json'
    data=json.loads(manifest.read_text(encoding='utf-8-sig'))
    products=[]
    for chunk in data['chunks']:
        for item in (chunk,chunk['low'],chunk['instances']):
            path=ROOT/item['file']
            got=sha(path)
            products.append(dict(file=item['file'],expected=item['sha256'],actual=got,valid=got==item['sha256']))
    ready=FD.load_ready()
    fixtures={}
    for folder in ('game/Assets/_Generated/Truck','game/Assets/_Generated/Trailer'):
        for p in sorted((ROOT/folder).rglob('*')):
            if p.is_file() and p.suffix.lower() in ('.prefab','.mat','.fbx'):
                fixtures[p.relative_to(ROOT).as_posix()]=sha(p)
    material_root=ROOT/'art-source/world/materials'
    spec_path=material_root/'materials_spec.json'
    spec=json.loads(spec_path.read_text(encoding='utf-8-sig'))
    texture_sha={}
    for entry in spec['sets'].values():
        tier=entry.get('files',{}).get('Medium')
        if not tier:continue
        for filename in tier.get('files',[]):
            image=material_root/tier['dir']/filename
            assert image.is_file(),f'Missing prepared PBR map: {image}'
            texture_sha[image.relative_to(ROOT).as_posix()]=sha(image)
    sources={name:sha(ROOT/name) for name in (
        'art-source/world/materials/_src/sets_facade.py',
        'art-source/world/materials/materials_spec.json',
        'art-source/world/props/street_props.glb',
        'art-source/world/props/props_meta.json',
        'tools/worldgen/streetscape/life_cars.py',
        'tools/worldgen/streetscape/materials.py',
        'game/Assets/_Project/Environment/Shaders/WorldPBR.shader')}
    mode_path=Path(__file__).with_name('SOURCE-MODE.json')
    mode=json.loads(mode_path.read_text(encoding='utf-8-sig')) if mode_path.exists() else None
    result=dict(manifest_sha=sha(manifest),products=products,raw_count=len(products),mismatches=sum(not p['valid'] for p in products),fab_ready=len(ready),fixtures=fixtures,prepared_medium_textures=texture_sha,source_sha=sources,source_mode=mode)
    base_path=Path(__file__).with_name('canonical-main-manifest.json')
    if base_path.exists():
        base=json.loads(base_path.read_text(encoding='utf-8-sig'))
        expected={item['file']:item['sha256'] for c in base['chunks'] for item in (c,c['low'],c['instances'])}
        actual={p['file']:p['actual'] for p in products}
        changed=[name for name in sorted(expected.keys()|actual.keys()) if expected.get(name)!=actual.get(name)]
        result['raw_vs_committed_base']=dict(base='5f2aa277',changed=len(changed),files=changed)
    assert len(products)==192 and result['mismatches']==0
    assert len(ready)==15,'Fab/Megascans ready library missing entries'
    tag=sys.argv[1] if len(sys.argv)>1 else 'candidate'
    out=Path(__file__).with_name(f'{tag}-source-proof.json')
    out.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('raw_count','mismatches','fab_ready')}|{'prepared_maps':len(texture_sha),'raw_changed_vs_base':result.get('raw_vs_committed_base',{}).get('changed')}))
if __name__=='__main__':main()
