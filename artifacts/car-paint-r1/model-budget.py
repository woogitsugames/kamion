"""Actual authored mesh counts plus real parked-car positions; no runtime/GPU claim."""
import collections
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/worldgen'))
from streetscape import life_cars as LC
PROPOSAL_SEGMENTS = None

def mesh(m):
    p = m.out()
    if PROPOSAL_SEGMENTS is not None:
        p = [x for x in p if not x['mat'].startswith('car_dirt_')]
    return dict(triangles=sum(len(x['T']) for x in p), primitives=len(p),
                materials={x['mat']: len(x['T']) for x in p})

def main():
    global PROPOSAL_SEGMENTS
    tag = sys.argv[1] if len(sys.argv)>1 else 'baseline'
    if len(sys.argv)>2:
        PROPOSAL_SEGMENTS = int(sys.argv[2])
        original_wheel = LC._wheel2
        def proposal_wheel(m,x,y,r,sx,segments,steel,lod,*args,**kwargs):
            return original_wheel(m,x,y,r,sx,PROPOSAL_SEGMENTS if lod==0 else segments,steel,lod,*args,**kwargs)
        LC._wheel2 = proposal_wheel
    names = [(f'car_{b}_{c}', lambda b=b,c=c: LC.car(b,c)) for b in LC.CARS for c in LC.CAR_COLOURS]
    names += [(f'van_{c}', lambda c=c: LC.van(c)) for c in LC.VAN_COLOURS]
    models = {}
    for name, fn in names:
        parts = fn()
        models[name] = [mesh(parts[i]) for i in (0,1,3)]
    instances=[]
    man=json.loads((ROOT/'Data/Regions/bialystok-industrial-c/generated/world_manifest.json').read_text())
    for c in man['chunks']:
        data=json.loads((ROOT/c['instances']['file']).read_text())
        instances += [i for i in data['instances'] if i['p'] in models]
    count=collections.Counter(i['p'] for i in instances)
    output=dict(note='Authored per-prototype counts, not visible draw/GPU costs. Instance transforms source matches InstanceImporter e,z,n TRS.',
                synthetic_proposal_only=PROPOSAL_SEGMENTS is not None, proposal_lod0_segments=PROPOSAL_SEGMENTS,
                source_sha256=hashlib.sha256((ROOT/'tools/worldgen/streetscape/life_cars.py').read_bytes()).hexdigest(),
                models=models, instance_count=len(instances), instance_counts=dict(sorted(count.items())),
                all_instanced_lod0_triangles=sum(count[p]*models[p][0]['triangles'] for p in count))
    out=ROOT/f'artifacts/car-paint-r1/{tag}-model-budget.json'
    out.write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'models':len(models),'instances':len(instances),'all_lod0_triangles':output['all_instanced_lod0_triangles']}))

if __name__=='__main__': main()
