"""Check all372 original/final frames, exact scope and honest counter/pose limits."""
import json,hashlib,re,csv
from bus_world_proof import ROOT,OUT
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stats(path):
    result={};current=None
    for line in path.read_text().splitlines():
        m=re.match(r'^(\S+): objects=(\d+) drawsEst=(\d+) shadowDrawsEst=(\d+) trisK=(\d+)',line)
        if m:current=m[1];result[current]=dict(zip(['objects','drawsEst','shadowDrawsEst','trisK'],map(int,m.groups()[1:])))
        m=re.match(r'^\s+(\S+) instanced .*: draws (\d+), instances (\d+), triangles (\d+)k, cells (\d+), forest HLOD cells (\d+)',line)
        if m:
            assert m[1]in result
            result[m[1]].update(zip(['instanced_draws','instances','instanced_trisK','cells','HLOD_cells'],map(int,m.groups()[1:])))
    return result
def main():
    baseline=json.loads((OUT/'baseline-capture-proof.json').read_text());frames=[];budgets=[];runtime=[];field_checks=[]
    for row in baseline['rows']:
        stage=row['stage'];condition=row['condition'];after_stage='after'if stage=='before'else'after-legacy'
        before_dir=OUT/stage/condition;after_dir=OUT/after_stage/condition
        ids=set(row['ids']);assert {p.stem for p in after_dir.glob('*.png')}==ids
        for file,digest in row['pngSHA256'].items():assert sha(before_dir/file)==digest,(stage,condition,file)
        packet=json.loads((after_dir/'runtime-pose.json').read_text())['cameras'];assert {c['id']for c in packet}==ids
        expected_scene='WorldC_High'if condition.startswith('High')else'WorldC';assert all(c['scene']==expected_scene for c in packet)
        old,new=stats(before_dir/'stats.txt'),stats(after_dir/'stats.txt');assert old.keys()==new.keys()==ids
        field_path=OUT/'wear-probe-before'/condition/'runtime-pose.json';field={c['id']:c for c in json.loads(field_path.read_text())['cameras']}
        for camera in packet:
            if camera['id']in field:
                prior=field[camera['id']];differences=[k for k in ['cameraPosition','cameraRotation','view','projection','fov','width','height','truck','trailer']if camera[k]!=prior[k]]
                field_checks.append(dict(condition=condition,camera=camera['id'],differences=differences))
        runtime.append(dict(stage=after_stage,condition=condition,cameras=len(packet),packet_sha256=sha(after_dir/'runtime-pose.json')))
        for name in sorted(ids):
            frames.append(dict(stage=after_stage,condition=condition,camera=name,sha256=sha(after_dir/(name+'.png'))))
            a,b=old[name],new[name];assert a.keys()==b.keys()
            budgets.append(dict(condition=condition,camera=name,stage=after_stage,**{k+'_before':v for k,v in a.items()},**{k+'_after':v for k,v in b.items()},**{k+'_delta':b[k]-a[k]for k in a}))
    assert len(frames)==len(budgets)==372
    fixture=json.loads((OUT/'wear-probe-before-final-fixture.json').read_text())
    for r in fixture['files']+fixture['raw']:assert sha(ROOT/r['file'])==r['sha256'],r['file']
    shader=ROOT/'game/Assets/_Project/Environment/Shaders/WorldPBR.shader';assert sha(shader)=='1dc7db4ea4ec839f4dc8fbd301ba5aedd38a12c3fff892e66818841d125edce4'
    keys=[k for k in budgets[0]if k.endswith('_delta')];ranges={k:dict(min=min(r[k]for r in budgets),max=max(r[k]for r in budgets),nonzero=sum(r[k]!=0 for r in budgets))for k in keys}
    with (OUT/'final-counter-comparison.csv').open('w',newline='')as f:
        writer=csv.DictWriter(f,fieldnames=list(budgets[0]));writer.writeheader();writer.writerows(budgets)
    proof=dict(frames=frames,count=len(frames),original_baseline372_hashes_exact=True,runtime_packets=runtime,current_field_runtime_comparisons=field_checks,
        counter_delta_ranges=ranges,shipping_cached_files_exact=len(fixture['files']),raw_files_exact=len(fixture['raw']),selected_shader_sha256=sha(shader),
        intended_source_triangle_delta_per_tier=73,intended_source_vertex_delta_per_tier=82,new_source_material_groups=0,
        note='Original93x4baseline images are intact and final scope matches exactly. Final runtime packets are actual; original372predates this recorder, so no retroactive before/runtime or pixel stability claim. Separate serialized camera/vehicle and raw geometry proofs support registration; exact current field matches are listed, with any differences flagged. Counters include instanced estimates but are not actual SRP/Android GPU measurements. Added73triangles/tier are real even if roundedK stays unchanged.')
    (OUT/'final-capture-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print('Final372scope/raw/cache verified. Counter delta ranges:',json.dumps(ranges));print('Field pose flags:',[r for r in field_checks if r['differences']])
if __name__=='__main__':main()
