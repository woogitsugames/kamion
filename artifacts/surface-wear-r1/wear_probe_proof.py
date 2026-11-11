"""Pin the fresh 56-frame broader-wear baseline or matched shader-only probe."""
import argparse,hashlib,json,subprocess
from bus_world_proof import ROOT,OUT

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main(stage):
    expected={c['id']for c in json.loads((OUT/'qa-wear-probe-cameras.json').read_text())['cameras']}
    assert len(expected)==14
    fixture_path=OUT/'gate-r2-fixture.json';fixture=json.loads(fixture_path.read_text())
    for row in fixture['files']+fixture['raw']:assert sha(ROOT/row['file'])==row['sha256'],row['file']
    uniform=json.loads((OUT/'paint-uniform-gate-r2.json').read_text())
    assert uniform['repeated_import_matches_first'] and uniform['materials'][0]['actual_uniform']==[.425,.25,.38,.12]
    images=[];runtime=[]
    for condition in ['Low-clear','Low-overcast','High-clear','High-overcast']:
        directory=OUT/f'wear-probe-{stage}'/condition
        found={f.stem for f in directory.glob('*.png')};assert found==expected,(stage,condition,found^expected)
        packet=json.loads((directory/'runtime-pose.json').read_text())['cameras'];assert {c['id']for c in packet}==expected
        if stage=='after':
            before=json.loads((OUT/'wear-probe-before'/condition/'runtime-pose.json').read_text())['cameras']
            for camera in packet:
                old=next(c for c in before if c['id']==camera['id'])
                for field in ['scene','cameraPosition','cameraRotation','view','projection','fov','width','height','truck','trailer']:
                    assert camera[field]==old[field],(condition,camera['id'],field)
            assert (directory/'stats.txt').read_bytes()==(OUT/'wear-probe-before'/condition/'stats.txt').read_bytes(),condition
        images.extend(dict(condition=condition,id=c,sha256=sha(directory/(c+'.png')))for c in sorted(expected))
        runtime.append(dict(condition=condition,sha256=sha(directory/'runtime-pose.json'),cameras=len(packet)))
    shader=ROOT/'game/Assets/_Project/Environment/Shaders/WorldPBR.shader'
    report=dict(stage=stage,source_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                frames=len(images),images=images,runtime_packets=runtime,shader_sha256=sha(shader),
                patch_sha256=sha(OUT/'candidate-broadwear-r2.patch'),fixture_sha256=sha(fixture_path),
                cached_Unity_files_verified=len(fixture['files']),raw_files_verified=len(fixture['raw']),
                actual_uniform=[.425,.25,.38,.12],uniform_native_proof_sha256=sha(OUT/'paint-uniform-gate-r2.json'),
                matched_runtime_poses_and_rounded_counters=stage=='after',
                note='Fresh actual14x4 images; current gate-r2 fixtures exact. Native paint proof is tied to unchanged material-file hashes. Counter equality is preSRP estimation, not GPU time or visual acceptance.')
    (OUT/f'wear-probe-{stage}-proof.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Fresh',stage,len(images),'frames pinned;2441cached+192raw verified; pose/counter parity',stage=='after')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['before','after']);main(parser.parse_args().stage)
