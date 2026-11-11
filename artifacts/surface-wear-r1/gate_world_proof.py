"""Strict second-stage delta: bus-only world -> gate pairs, with cached Unity fixtures frozen."""
from pathlib import Path
import json,hashlib
import numpy as np
from bus_world_proof import ROOT,OUT,read

def main():
    fixture=json.loads((OUT/'bus-only-fixture.json').read_text());changed=[];files=[]
    for row in fixture['files']:
        sha=hashlib.sha256((ROOT/row['file']).read_bytes()).hexdigest();files.append(dict(file=row['file'],sha256=sha))
        if sha!=row['sha256']:changed.append(row['file'])
    expected=[f'Data/raw/derived/bialystok-industrial-c/world/chunk_6_6{s}.glb'for s in ('','.low')]
    assert sorted(changed)==sorted(expected),changed
    proof=[]
    for file in changed:
        da,a=read(OUT/'raw-before'/Path(file).name);db,b=read(ROOT/file)
        assert a.keys()==b.keys() and da['materials']==db['materials'] and da['nodes']==db['nodes']
        same=0;insertion=None
        for node,primitives in a.items():
            assert len(primitives)==len(b[node])
            for (mat,attrs),(newmat,new) in zip(primitives,b[node]):
                assert mat==newmat and attrs.keys()==new.keys()
                if node=='markings'and mat=='decal_tyre':
                    oldp=attrs['POSITION'];newp=new['POSITION'];assert len(newp)-len(oldp)==72
                    different=np.flatnonzero(np.any(oldp!=newp[:len(oldp)],axis=1));assert len(different)
                    start=int(different[0]);insertion=start
                    for name,old in attrs.items():
                        other=new[name];assert old.dtype==other.dtype,(name,old.dtype,other.dtype)
                        if name=='indices':continue
                        assert len(other)-len(old)==72 and np.array_equal(other[:start],old[:start]) and np.array_equal(other[start+72:],old[start:]),(file,node,mat,name)
                    oldidx=attrs['indices'].reshape(-1,3);newidx=new['indices'].reshape(-1,3)
                    inserted=np.all((newidx>=start)&(newidx<start+72),axis=1);assert int(inserted.sum())==64
                    expectedidx=np.where(oldidx>=start,oldidx+72,oldidx)
                    assert np.array_equal(newidx[~inserted],expectedidx)
                    uv=new['TEXCOORD_1'][start:start+72]
                    assert np.allclose(uv[:,0],4.2,atol=1e-4)and np.allclose(uv[:,1],.1,atol=1e-4)
                else:
                    for name,old in attrs.items():assert old.dtype==new[name].dtype and np.array_equal(old,new[name]),(file,node,mat,name)
                    same+=1
        assert insertion is not None
        proof.append(dict(file=file,unchanged_ordered_primitives=same,tyre_insertion_vertex=insertion,old_tyre_attributes_exact_after_removing_insertion=True,
                          old_tyre_indices_exact_after_rebasing=True,added_vertices=72,added_triangles=64,new_material_groups=0))
    cached=json.loads((OUT/'bus-only-canonical-fixture.json').read_text());mismatches=[]
    for row in cached['files']:
        if hashlib.sha256((ROOT/row['file']).read_bytes()).hexdigest()!=row['sha256']:mismatches.append(row['file'])
    assert not mismatches,mismatches
    qa=json.loads((ROOT/'Data/Regions/bialystok-industrial-c/generated/streetscape_qa.json').read_text());tracks=qa['furniture']['gates']['tyre_tracks'];fab=qa['furniture']['megascans']
    assert len(tracks['applied'])==2 and not tracks['rejected']
    assert sum(x['triangles']for x in tracks['applied'])==64 and len(fab['available'])==15 and fab['added_props']==320 and not fab.get('fallback',False)
    bus=qa['furniture']['life']['bus_stop_oil'];assert len(bus['applied'])==1 and len(bus['rejected'])==19
    manifest=json.loads((ROOT/'Data/Regions/bialystok-industrial-c/generated/world_manifest.json').read_text())
    for c in manifest['chunks']:
        for item in(c,c['low'],c['instances']):assert hashlib.sha256((ROOT/item['file']).read_bytes()).hexdigest()==item['sha256']
    packet=dict(raw_count=192,unchanged_from_bus_only=190,changed=proof,bus_4_5_exact=True,all64instances_exact=True,
                cached_bus_only_Generated_files_unchanged=len(cached['files']),cached_Generated_mismatches=mismatches,
                gate=tracks,fab_ready=15,fab_props=320,fab_fallback=False,files=files,
                note='Canonical CPU build only. Cached Unity scenes still bus-only for pending HighOV/narrow/gate BEFORE. New gate64tris per tier source groups0; no actual PNG/GPU PASS yet.')
    (OUT/'gate-world-proof.json').write_text(json.dumps(packet,indent=2)+'\n');print(json.dumps({k:v for k,v in packet.items()if k not in('files','gate')}))
if __name__=='__main__':main()
