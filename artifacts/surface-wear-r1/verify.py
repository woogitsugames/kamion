"""Read-only D baseline provenance. No Unity or production mutation."""
from pathlib import Path
import hashlib
import json
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/worldgen'))
from streetscape import fab_details as FD

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    tag=sys.argv[1] if len(sys.argv)>1 else 'baseline'
    path=ROOT/'Data/Regions/bialystok-industrial-c/generated/world_manifest.json'
    manifest=json.loads(path.read_text(encoding='utf-8'))
    raw=[]
    for c in manifest['chunks']:
        for item in (c,c['low'],c['instances']):
            got=sha(ROOT/item['file'])
            raw.append(dict(file=item['file'],sha256=got,expected=item['sha256'],valid=got==item['sha256']))
    ready=FD.load_ready()
    assert len(raw)==192 and all(i['valid'] for i in raw)
    assert len(ready)==15
    sources={}
    for name in ('game/Assets/_Project/Environment/Shaders/WorldPBR.shader',
                 'game/Assets/_Project/Rendering/Shaders/WorldSurface.shader',
                 'game/Assets/_Project/World/Import/WorldPbrMaterials.cs',
                 'game/Assets/_Project/World/Import/WorldMeshBake.cs',
                 'game/Assets/_Project/World/Import/RegionImporter.cs',
                 'tools/worldgen/streetscape/materials.py',
                 'art-source/world/materials/materials_spec.json'):
        sources[name]=sha(ROOT/name)
    for p in sorted((ROOT/'art-source/world/materials').glob('asphalt*/*/*.png')):
        sources[p.relative_to(ROOT).as_posix()]=sha(p)
    out=dict(base_main='901c427f2bc5cebf9571adc14df3253bbd3bd772',required_0095_merge='471438fb',
             cache_only_from_C='5db77e9d',manifest_sha256=sha(path),
             raw_count=192,mismatches=0,fab_ready=15,fab_fallback=False,raw=raw,source_sha256=sources)
    (ROOT/f'artifacts/surface-wear-r1/{tag}-source-proof.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(raw=192,mismatches=0,fab_ready=15,fab_fallback=False,sources=len(sources))))

if __name__=='__main__':main()
