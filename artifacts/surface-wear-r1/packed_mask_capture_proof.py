"""Verify the isolated 16-frame mask trial against the actual fresh selected-source baseline."""
import json,hashlib,re
from bus_world_proof import ROOT,OUT
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stats(path):
    result={};current=None
    for line in path.read_text().splitlines():
        match=re.match(r'^(d_\w+):',line)
        if match:current=match.group(1);result[current]=[line.strip()]
        elif current and line.strip().startswith(current+' instanced'):result[current].append(line.strip())
    return result
def main():
    ids={c['id']for c in json.loads((OUT/'qa-packed-mask-cameras.json').read_text())['cameras']};assert len(ids)==4
    fixture=json.loads((OUT/'wear-probe-before-final-fixture.json').read_text())
    for row in fixture['files']+fixture['raw']:assert sha(ROOT/row['file'])==row['sha256'],row['file']
    shader=ROOT/'game/Assets/_Project/Environment/Shaders/WorldPBR.shader';assert sha(shader)=='1dc7db4ea4ec839f4dc8fbd301ba5aedd38a12c3fff892e66818841d125edce4'
    rows=[];runs=[];signals=[]
    for cond in ['Low-clear','Low-overcast','High-clear','High-overcast']:
        directory=OUT/'packed-mask-qa'/cond;assert {p.stem for p in directory.glob('*.png')}==ids
        packet=json.loads((directory/'runtime-pose.json').read_text())['cameras'];before=json.loads((OUT/'wear-probe-before'/cond/'runtime-pose.json').read_text())['cameras'];assert {c['id']for c in packet}==ids
        expected=stats(OUT/'wear-probe-before'/cond/'stats.txt');actual=stats(directory/'stats.txt');assert actual=={k:expected[k]for k in ids}
        run=json.loads((OUT/f'packed-mask-{cond}-run.json').read_text(encoding='utf-8-sig'));assert run['complete']and run['fresh_frames']==4 and run['finally_restored'];runs.append(run)
        for camera in packet:
            old=next(c for c in before if c['id']==camera['id'])
            for key in ['scene','cameraPosition','cameraRotation','view','projection','fov','width','height','truck','trailer']:assert camera[key]==old[key],(cond,camera['id'],key)
            rows.append(dict(condition=cond,camera=camera['id'],sha256=sha(directory/(camera['id']+'.png')),runtime_camera_and_vehicle_pose_exact=True))
        signals.append(dict(condition=cond,actual_instanced_signal_materials=packet[0]['signals']))
    production=shader.read_text();qa=(OUT/'PackedRoadMask.shader').read_text();assert production.count('SAMPLE_TEXTURE2D')==qa.count('SAMPLE_TEXTURE2D')==20
    proof=dict(frames=len(rows),images=rows,runs=runs,actual_signal_bindings=signals,shipping_cached_files_exact=len(fixture['files']),raw_files_exact=len(fixture['raw']),
        production_shader_sha256=sha(shader),QA_shader_sha256=sha(OUT/'PackedRoadMask.shader'),all16_runtime_poses_and_rounded_counter_rows_equal=True,
        additional_QA_asset_scope='Only ignored SurfaceWearQA shaders/controller/new packed texture; original shipping World/Truck/Trailer files unchanged. Original world materials restored; only M_road_asphalt temporarily cloned.',
        note='QA-only trial, no production binding. GBA compression drift and image quality assessed separately. Actual instanced signal shader/keywords recorded; no historical signal runtime or nonexistent lamp ROI is claimed. Counter equality is not GPU time.')
    (OUT/'packed-mask16-capture-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print('16QA frames: runtime poses/counters exact;2441shipping+192raw exact; production shader and materials restored.')
if __name__=='__main__':main()
