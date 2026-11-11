"""Audit immutable legacy tyre length values before reserving a negative sign."""
import json
import numpy as np
from bus_world_proof import OUT,read
def main():
    records=[]
    for file in sorted((OUT/'raw-before').glob('*.glb')):
        _,nodes=read(file)
        for node,primitives in nodes.items():
            for material,attrs in primitives:
                if material!='decal_tyre':continue
                lengths=attrs['TEXCOORD_1'][:,0]
                assert np.isfinite(lengths).all() and np.all(lengths>=0),(file,node,float(lengths.min()))
                records.append(dict(file=file.name,node=node,vertices=len(lengths),minimum=float(lengths.min()),maximum=float(lengths.max())))
    assert records
    report=dict(immutable_raw_files=192,primitives=len(records),vertices=sum(r['vertices']for r in records),all_legacy_lengths_nonnegative=True,records=records)
    (OUT/'tyre-length-contract.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Legacy tyre audit:',report['primitives'],'primitives,',report['vertices'],'vertices, all lengths >=0')
if __name__=='__main__':main()
