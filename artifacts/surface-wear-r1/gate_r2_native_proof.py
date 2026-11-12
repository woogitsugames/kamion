"""Verify imported signed length and geometry against actual first-gate native buffers."""
import json
from bus_world_proof import OUT
def main():
    before=json.loads((OUT/'native-gate-first.json').read_text());after=json.loads((OUT/'native-gate-r2.json').read_text())
    old={(r['scene'],r['path']):r for r in before['meshes']};new={(r['scene'],r['path']):r for r in after['meshes']}
    assert old.keys()==new.keys();changed=[];signed=[]
    for key,a in old.items():
        b=new[key]
        for field in ['positions','normals','indices','uv0','uv1y','vertices','submeshes','hasUv1']:
            assert a[field]==b[field],(key,field)
        if a['uv1']!=b['uv1']:changed.append(key)
        for part in b['parts']:
            if part['material']!='M_decal_tyre':continue
            count=part['shortApproachVertices']
            if count:
                assert count==72 and 'chunk_6_6.asset#6_6_markings' in key[1],(key,count)
                assert abs(part['minimumTyreLength']+4.2)<.002
                signed.append(dict(scene=key[0],path=key[1],negative_length_vertices=count,minimum_length=part['minimumTyreLength']))
            else:assert part['minimumTyreLength']>=0
    assert len(changed)==len(signed)==2
    assert set(changed)=={(r['scene'],r['path'])for r in signed}
    tyre=next(m for m in after['materials']if m['path'].endswith('/M_decal_tyre.mat'))
    assert '_DECAL_TYRE' in tyre['keywords'].split(',') and '_UV_MESH1' not in tyre['keywords'].split(',')
    report=dict(native_meshes=len(new),changed_UV1_buffers=changed,signed=signed,actual_tyre_keywords=tyre['keywords'],
                note='Actual uploaded mesh readback after canonical import. Geometry/UV0/age exact; only two gate marking UV1 buffers change. Shader GPU branch visibility remains a separate image test.')
    (OUT/'gate-r2-native-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
