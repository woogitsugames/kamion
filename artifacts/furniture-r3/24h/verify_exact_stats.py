"""Validate actual unrounded CPU counters against both current and frozen runner output."""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
p = argparse.ArgumentParser()
p.add_argument('phase', choices=['before', 'after', 'after2'])
p.add_argument('tier', choices=['Low', 'High'])
p.add_argument('lighting', choices=['clear', 'overcast', 'dusk'])
args = p.parse_args()
key = f'{args.tier}-{args.lighting}'
probe = ROOT / f'exact-{args.phase}' / key


def stats(path):
    rows = {}
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        m = re.search(r'([^ :]+): objects=(\d+) drawsEst=(\d+) shadowDrawsEst=(\d+) trisK=(\d+)', line)
        if m:
            camera, objects, draws, shadows, tris = m.groups()
            rows[camera] = dict(mesh_objects=int(objects), mesh_draws=int(draws), mesh_triangles=int(tris))
        m = re.search(r'([^ :]+) instanced .*: draws (\d+), instances (\d+), triangles (\d+)k', line)
        if m:
            camera, draws, count, tris = m.groups()
            rows[camera].update(instance_draws=int(draws), instances=int(count), instance_triangles=int(tris))
    assert rows, 'No parsed camera rows'
    return rows


frozen = stats(ROOT / args.phase / key / 'stats.txt')
current = stats(probe / 'stats.txt')
assert frozen == current, 'Frozen runner output changed: do not claim exact baseline/candidate identity'
packet = json.loads((probe / 'exact-stats.json').read_text(encoding='utf-8-sig'))
assert (packet['phase'], packet['tier'], packet['lighting']) == (args.phase, args.tier, args.lighting)
rows = {r['camera']: r for r in packet['cameras']}
assert len(rows) == packet['rendered'] and rows.keys() == frozen.keys()
for camera, row in rows.items():
    old = frozen[camera]
    for field in ('mesh_objects', 'mesh_draws', 'instance_draws', 'instances'):
        assert row[field] == old.get(field, 0), (camera, field)
    for field in ('mesh_triangles', 'instance_triangles'):
        assert row[field] // 1000 == old.get(field, 0), (camera, field)
proof = dict(phase=args.phase, tier=args.tier, lighting=args.lighting, cameras=len(rows),
             runner_and_frozen_match=True, unrounded_values_match_every_reported_floor=True,
             frozen_stats_sha256=hashlib.sha256((ROOT / args.phase / key / 'stats.txt').read_bytes()).hexdigest(),
             packet_sha256=hashlib.sha256((probe / 'exact-stats.json').read_bytes()).hexdigest(),
             scope='CPU estimates before SRP batching, not GPU measurements')
(probe / 'validation.json').write_text(json.dumps(proof, indent=2) + '\n')
print(json.dumps(proof))

