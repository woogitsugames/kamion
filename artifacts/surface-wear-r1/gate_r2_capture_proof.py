"""Pin the 16-frame gate packet and distinguish runtime proof from old controls."""
import hashlib,json,re
from bus_world_proof import OUT

def counters(path):
    result={};current=None
    for line in path.read_text().splitlines():
        match=re.match(r'^(d_gate_\w+):',line)
        if match:current=match.group(1);result[current]=[line.strip()]
        elif current and line.strip().startswith(current+' instanced'):result[current].append(line.strip())
    return result

def main():
    files=[];rows=[]
    for condition in ['Low-clear','Low-overcast','High-clear','High-overcast']:
        after=OUT/'gate-r2-after'/condition
        packet=json.loads((after/'runtime-pose.json').read_text())['cameras']
        before=json.loads((OUT/'gate-pair-before'/condition/'runtime-pose.json').read_text())['cameras']
        assert len(packet)==4 and len(before)==2
        for old in before:
            new=next(c for c in packet if c['id']==old['id'])
            for field in ['scene','cameraPosition','cameraRotation','view','projection','fov','width','height','truck','trailer']:
                assert old[field]==new[field],(condition,old['id'],field)
            rows.append(dict(condition=condition,camera=old['id'],actual_runtime_camera_and_vehicle_pose_exact=True))
        expected={**counters(OUT/'gate-pair-before'/condition/'stats.txt'),**counters(OUT/'gate-kerb-before'/condition/'stats.txt')}
        assert len(expected)==4 and counters(after/'stats.txt')==expected,condition
        for c in packet:
            image=after/(c['id']+'.png');files.append(dict(condition=condition,camera=c['id'],sha256=hashlib.sha256(image.read_bytes()).hexdigest()))
    report=dict(count=len(files),files=files,gate_runtime_comparisons=rows,all16_rounded_counter_rows_equal=True,
                note='Gate8 have actual matched runtime camera/vehicle packets. Older kerb8 have matching authored cameras and rounded counters but no historical runtime packet. Counters are preSRP estimates, not GPU timing. No overall visual acceptance implied.')
    assert len(files)==16
    (OUT/'gate-r2-capture-proof.json').write_text(json.dumps(report,indent=2)+'\n');print('Pinned16 PNGs; gate8 runtime poses exact, all16 rounded counter rows exact; old kerb runtime caveat retained.')
if __name__=='__main__':main()
