"""Final actual uploaded meshes/materials, preserving deliberate bus/gate deltas."""
import json
from bus_world_proof import OUT
def main():
    old=json.loads((OUT/'native-before.json').read_text());final=json.loads((OUT/'native-final.json').read_text())
    a={(r['scene'],r['path']):r for r in old['meshes']};b={(r['scene'],r['path']):r for r in final['meshes']};assert a.keys()==b.keys()
    changed=[];uv=[];signed=[];vertex_delta=0;exact=0
    for key,first in a.items():
        last=b[key];fields=['positions','normals','indices','uv0','vertices','submeshes'];diff=[k for k in fields if first[k]!=last[k]]
        if diff:
            assert any(f'chunk_{c}.asset#{c}_markings'in key[1]for c in ['4_5','6_6']),key
            delta=last['vertices']-first['vertices'];assert delta==(10 if 'chunk_4_5' in key[1] else 72)
            vertex_delta+=delta;changed.append(dict(scene=key[0],path=key[1],changed_fields=diff,added_vertices=delta))
        else:exact+=1
        if first['uv1']!=last['uv1']:uv.append(dict(scene=key[0],path=key[1]))
        assert last['uv1y']==last['uv1ySource'],key
        for part in last['parts']:
            if part['material']=='M_decal_tyre'and part['shortApproachVertices']:
                assert part['shortApproachVertices']==72 and 'chunk_6_6'in key[1];signed.append(dict(scene=key[0],vertices=72,minimum_length=part['minimumTyreLength']))
    assert len(changed)==4 and exact==150 and vertex_delta==164 and len(signed)==2
    for material in final['materials']:
        assert not material['shader'].startswith('Hidden/'),material
        assert not any('SurfaceWearQA'in f for f in material['fields']),material
    road=next(r for r in final['materials']if r['path'].endswith('/M_road_asphalt.mat'))
    assert any(f.startswith('_MaskMap=')and f.endswith('/asphalt_worn/T_asphalt_worn_MaskMap.png')for f in road['fields'])
    assert '_MetallicScale=0'in road['fields']
    paint=json.loads((OUT/'paint-uniform-final.json').read_text());assert paint['materials'][0]['actual_uniform']==[.425,.25,.38,.12]
    report=dict(native_meshes=len(b),geometry_UV0_exact_meshes=exact,deliberate_marking_geometry_changes=changed,total_added_vertices_both_tiers=vertex_delta,
        changed_UV1_buffers=uv,all_native_UV1_age_matches_current_raw=True,signed_gate=signed,actual_old_road_material=road,actual_paint_uniform=paint,
        QA_shaders_and_packed_textures_unbound=True,note='Actual native buffer readback. All road geometry remains exact; four marking buffers add only10bus/72gate vertices per tier. Raw ordered-primitive proofs establish73additionaltriangles per tier and preservation of all old marking data. UV-only changes are separate from geometry deltas. No overall appearance or GPU budget PASS.')
    (OUT/'final-native-proof.json').write_text(json.dumps(report,indent=2)+'\n');print('Final native:',len(b),'meshes,',exact,'geometry-exact,4expectedmarking changes,+164vertices both tiers; no boundQA.')
if __name__=='__main__':main()
