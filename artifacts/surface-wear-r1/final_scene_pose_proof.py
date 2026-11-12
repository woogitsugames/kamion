"""Repeat the preserved-scene comparison without overwriting historical stage evidence."""
import json
from scene_pose_proof import ROOT,OUT,BASE,scene,prefab_transforms
def main():
    rows=[]
    for name in ['WorldC','WorldC_High']:
        file=f'game/Assets/_Generated/World/bialystok-industrial-c/{name}.unity';a=scene(BASE/file,BASE);b=scene(ROOT/file,ROOT)
        assert a['roots']==b['roots'],name
        diff={k:dict(before=v,after=b['controls'].get(k))for k,v in a['controls'].items()if v!=b['controls'].get(k)}
        assert not diff,(name,diff)
        rows.append(dict(scene=name,serialized_native_control_cameras=len(a['controls']),actor_roots_exact=True,effective_camera_matrices_FOV_clips_exact=True))
    prefabs=[]
    for file in ['game/Assets/_Generated/Truck/Tractor4x2_TRAKT.prefab','game/Assets/_Generated/Trailer/Trailer_Curtainsider_Art.prefab']:
        a=prefab_transforms(BASE/file);b=prefab_transforms(ROOT/file);assert a==b,file
        prefabs.append(dict(file=file,hierarchical_transforms=sum(map(len,a.values())),exact=True))
    proof=dict(scenes=rows,prefabs=prefabs,note='Actual original canonical scene/prefab files versus final chosen state. This proves serialized pose/intrinsics inputs, not retroactive runtime packets for all372originalimages. Current runtime packets and existing field comparisons are separate.')
    (OUT/'final-scene-pose-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
if __name__=='__main__':main()
