"""Pin the fresh 56-frame broader-wear baseline or matched shader-only probe."""
import argparse,hashlib,json,subprocess
from bus_world_proof import ROOT,OUT

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main(stage):
    expected={c['id']for c in json.loads((OUT/'qa-wear-probe-cameras.json').read_text())['cameras']}
    assert len(expected)==14
    fixture_path=OUT/('gate-r2-fixture.json' if stage=='before' else 'wear-probe-before-final-fixture.json')
    fixture=json.loads(fixture_path.read_text())
    allowed={}
    if stage=='before':
        signal=json.loads((OUT/'wear-probe-signal-material-delta.json').read_text())
        assert signal['count']==2 and signal['other_cached_files_exact']==2439
        allowed={r['file']:r['post_before_sha256']for r in signal['changes']}
    actual_files=[];exceptions=[]
    for row in fixture['files']:
        actual=sha(ROOT/row['file'])
        if actual!=row['sha256']:
            assert row['file']in allowed and actual==allowed[row['file']],row['file']
            exceptions.append(row['file'])
        actual_files.append(dict(file=row['file'],bytes=(ROOT/row['file']).stat().st_size,sha256=actual))
    for row in fixture['raw']:assert sha(ROOT/row['file'])==row['sha256'],row['file']
    if stage=='before':
        assert set(exceptions)==set(allowed)
        (OUT/'wear-probe-before-final-fixture.json').write_text(json.dumps(dict(files=actual_files,raw=fixture['raw'],
            note='Actual final BEFORE cache; two exact _EMISSION keyword serialization changes are explicit in wear-probe-signal-material-delta.json. Original initial gate-r2 fixture remains unchanged.'),indent=2)+'\n')
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
                cached_Unity_files_verified=len(fixture['files']),raw_files_verified=len(fixture['raw']),explicit_baseline_material_serialization_exceptions=exceptions,
                actual_uniform=[.425,.25,.38,.12],uniform_native_proof_sha256=sha(OUT/'paint-uniform-gate-r2.json'),
                matched_runtime_poses_and_rounded_counters=stage=='after',
                note='Fresh actual14x4 images. Two explicit signal keyword serializations distinguish initial versus final BEFORE cache; AFTER must match the pinned final BEFORE cache. Native paint proof is tied to unchanged material-file hashes. Counter equality is preSRP estimation, not GPU time or visual acceptance.')
    (OUT/f'wear-probe-{stage}-proof.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Fresh',stage,len(images),'frames pinned;2441cached+192raw checked; explicit initial baseline exceptions',len(exceptions),'; pose/counter parity',stage=='after')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['before','after']);main(parser.parse_args().stage)
