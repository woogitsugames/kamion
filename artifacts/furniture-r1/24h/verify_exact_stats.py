"""Validate an unrounded capture against both runner stats and the frozen after4 stats."""
import argparse
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('tier',choices=['Low','High'])
parser.add_argument('lighting',choices=['clear','overcast'])
args = parser.parse_args()
key = f'{args.tier}-{args.lighting}'
probe = HERE/'exact-after4'/key

def stats(path):
    result = {}
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        match = re.search(r'([^ :]+): objects=(\d+) drawsEst=(\d+) shadowDrawsEst=(\d+) trisK=(\d+)',line)
        if match:
            camera,objects,draws,shadows,triangles = match.groups()
            result[camera] = dict(objects=int(objects),draws=int(draws),shadows=int(shadows),triangles=int(triangles))
        match = re.search(r'([^ :]+) instanced .*: draws (\d+), instances (\d+), triangles (\d+)k',line)
        if match:
            camera,draws,instances,triangles = match.groups()
            result[camera].update(instance_draws=int(draws),instances=int(instances),instance_triangles=int(triangles))
    return result

original = stats(HERE/'after'/key/'stats.txt')
captured = stats(probe/'stats.txt')
assert original == captured,'Probe runner counters differ from the frozen after4 capture'
before = stats(HERE/'before'/key/'stats.txt')
packet = json.loads((probe/'exact-stats.json').read_text())
assert packet['tier'] == args.tier and packet['lighting'] == args.lighting
rows = {row['camera']:row for row in packet['cameras']}
assert rows.keys() == original.keys() == before.keys()
assert len(rows) == packet['rendered'] == 55
out = []
for camera,row in sorted(rows.items()):
    reference = original[camera]
    assert row['mesh_objects'] == reference['objects'],camera
    assert row['mesh_draws'] == reference['draws'],camera
    assert row['mesh_triangles']//1000 == reference['triangles'],camera
    assert row['instance_draws'] == reference.get('instance_draws',0),camera
    assert row['instances'] == reference.get('instances',0),camera
    assert row['instance_triangles']//1000 == reference.get('instance_triangles',0),camera
    baseline_floor = 1000*(before[camera]['triangles']+before[camera].get('instance_triangles',0))
    total = row['mesh_triangles']+row['instance_triangles']
    out.append(dict(camera=camera,tier=args.tier,lighting=args.lighting,after_exact_triangles=total,
                    before_floor_triangles=baseline_floor,
                    tris_delta_upper_percent=100*(total/baseline_floor-1) if baseline_floor else None,
                    mesh_draw_delta=row['mesh_draws']-before[camera]['draws'],
                    instance_draw_delta=row['instance_draws']-before[camera].get('instance_draws',0)))
(probe/'verified-budget.json').write_text(json.dumps(out,indent=2)+'\n')
print(f'Validated {len(out)} unrounded camera counts against runner and frozen after4 stats; CPU estimates only')
for row in out:
    if row['tris_delta_upper_percent'] is not None and row['tris_delta_upper_percent']>2:
        print(f"{row['camera']}: upper delta {row['tris_delta_upper_percent']:.6f}%")
