"""CPU float32 proposal check only. Actual RenderMeshInstanced GPU proof remains required."""
import collections
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
man=json.loads((ROOT/'Data/Regions/bialystok-industrial-c/generated/world_manifest.json').read_text())
instances=[]
for chunk in man['chunks']:
    data=json.loads((ROOT/chunk['instances']['file']).read_text())
    instances += [i for i in data['instances'] if i['p'].startswith(('car_','van_'))]
poses=np.asarray([[i['e'],i['n']] for i in instances],dtype=np.float32)
corner=np.array([-1024,-1024],dtype=np.float32)

def cells(shift):
    sh=np.asarray(shift,dtype=np.float32)
    return np.floor(((poses+sh)-(corner+sh))*4+.37).astype(np.int64)

base=cells((0,0))
mismatches={str(s):int(np.count_nonzero(np.any(base!=cells(s),axis=1)))
            for s in [(1024,0),(-1024,1024),(4096,-4096),(-4096,4096),(512.25,-2048.75)]}
h=base[:,0].astype(np.uint32)*np.uint32(1664525)+base[:,1].astype(np.uint32)*np.uint32(1013904223)
h ^= h>>np.uint32(16)
h *= np.uint32(2246822519)
h ^= h>>np.uint32(13)
levels=(h>>np.uint32(30)).astype(int)
counts=collections.Counter(map(int,levels))
result=dict(note='CPU float32 proposal only; actual instanced GPU proof still required. Quarter-metre stable origin grid plus arbitrary hash salt. No runtime/source changes.',
            count=len(instances),levels=dict(sorted(counts.items())),shift_cell_mismatches=mismatches,
            examples=[dict(level=k,instance=instances[next(j for j,v in enumerate(levels) if v==k)]) for k in range(4)])
assert len(counts)==4 and all(n==0 for n in mismatches.values())
out=ROOT/'artifacts/car-paint-r1/proposed-dirt-seed-proof.json'
out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(counts=dict(counts),shift_cell_mismatches=mismatches)))
