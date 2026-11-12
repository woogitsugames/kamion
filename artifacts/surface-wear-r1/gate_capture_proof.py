"""Pin completed gate frames, matched runtime poses and estimate-only counters."""
import hashlib
import json
from pathlib import Path

OUT=Path(__file__).resolve().parent
def main():
    records=[]
    for condition in ['Low-clear','Low-overcast','High-clear','High-overcast']:
        before=OUT/'gate-pair-before'/condition;after=OUT/'gate-pair-after'/condition
        a=json.loads((before/'runtime-pose.json').read_text())['cameras']
        b=json.loads((after/'runtime-pose.json').read_text())['cameras']
        assert len(a)==len(b)==2
        for old,new in zip(a,b):
            for key in ['id','scene','cameraPosition','cameraRotation','view','projection','fov','width','height','truck','trailer']:
                assert old[key]==new[key],(condition,old['id'],key)
            image=after/(new['id']+'.png')
            records.append(dict(condition=condition,id=new['id'],sha256=hashlib.sha256(image.read_bytes()).hexdigest(),
                                runtime_camera_and_vehicle_poses_exact=True))
        assert (before/'stats.txt').read_bytes()==(after/'stats.txt').read_bytes(),condition
    packet=dict(frames=records,count=len(records),rounded_preSRP_estimates_equal=True,
                note='Actual matched runtime poses for these8frames only. Counters are rounded preSRP estimates, not GPU measurements. Source adds64triangles per tier despite unchanged rounded trisK. No paired-visibility PASS.')
    (OUT/'gate-capture-proof.json').write_text(json.dumps(packet,indent=2)+'\n')
    print('Gate8 frames: SHA pinned, runtime camera+vehicle poses exact, rounded counters unchanged.')
if __name__=='__main__':main()
