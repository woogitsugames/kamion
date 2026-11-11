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
    result=dict(manifest_sha=sha(manifest),products=products,raw_count=len(products),mismatches=sum(not p['valid'] for p in products),fab_ready=len(ready),fixtures=fixtures)
    assert len(products)==192 and result['mismatches']==0
    assert len(ready)==15,'Fab/Megascans ready library missing entries'
    tag=sys.argv[1] if len(sys.argv)>1 else 'candidate'
    out=Path(__file__).with_name(f'{tag}-source-proof.json')
    out.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('raw_count','mismatches','fab_ready')}))
if __name__=='__main__':main()
