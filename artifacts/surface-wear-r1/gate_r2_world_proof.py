"""Strict gate-r1 -> signed short-approach delta; no cached Unity mutation."""
import hashlib,json
import numpy as np
from bus_world_proof import ROOT,OUT,read
def main():
    fixture=json.loads((OUT/'gate-first-fixture.json').read_text())
    changed=[r['file']for r in fixture['raw'] if hashlib.sha256((ROOT/r['file']).read_bytes()).hexdigest()!=r['sha256']]
    assert sorted(changed)==sorted(f'Data/raw/derived/bialystok-industrial-c/world/chunk_6_6{s}.glb'for s in ('','.low')),changed
    proofs=[]
    for file in changed:
        da,a=read(OUT/'gate-r1-raw'/file.split('/')[-1]);db,b=read(ROOT/file)
        assert da==db,'GLB structure/materials/nodes/accessor counts must remain exact'
        differences=0;primitives=0
        for node,old in a.items():
            for (mat,attrs),(newmat,new) in zip(old,b[node]):
                assert mat==newmat
                for key,value in attrs.items():
                    if node=='markings'and mat=='decal_tyre'and key=='TEXCOORD_1':
                        expected=value.copy();expected[176:248,0]*=-1
                        assert np.array_equal(new[key],expected)
                        assert np.all(value[176:248,0]>0) and np.all(new[key][176:248,0]<0)
                        differences=int(np.count_nonzero(value!=new[key]));assert differences==72
                    else:assert np.array_equal(value,new[key]),(file,node,mat,key)
                primitives+=1
        proofs.append(dict(file=file,ordered_primitives=primitives,changed_scalar_values=differences,geometry_uv0_strength_legacy_uv1_exact=True))
    for row in fixture['files']:
        assert hashlib.sha256((ROOT/row['file']).read_bytes()).hexdigest()==row['sha256'],row['file']
    manifest=json.loads((ROOT/'Data/Regions/bialystok-industrial-c/generated/world_manifest.json').read_text())
    for c in manifest['chunks']:
        for item in (c,c['low'],c['instances']):assert hashlib.sha256((ROOT/item['file']).read_bytes()).hexdigest()==item['sha256']
    report=dict(changed=proofs,unchanged_raw_files=190,cached_Unity_unchanged=len(fixture['files']),added_triangles=0,added_vertices=0,
                note='Gate-r1 to r2 changes ONLY72 UV1.x signs per tier; legacy tyre data literal exact. Shader adds signed mode .65/.90m fades, strength.9 and macro unchanged. GPU/visibility unverified; Unity remains held.')
    (OUT/'gate-r2-world-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
