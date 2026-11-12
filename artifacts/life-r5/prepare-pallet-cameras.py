"""Inspection poses from fresh actual instances; never changes placements."""
import json
import math
from pathlib import Path

from shapely.affinity import translate
from shapely.geometry import LineString, Polygon, shape
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).parent
packet = json.loads((OUT / 'cameras.json').read_text(encoding='utf-8-sig'))
assert not any(c['id'].endswith('_prop_side3') for c in packet['cameras']), 'Camera evidence already exists'
manifest = json.loads((ROOT / 'Data/Regions/bialystok-industrial-c/generated/world_manifest.json').read_text())
instances = []
for chunk in manifest['chunks']:
    instances.extend(i for i in json.loads((ROOT / chunk['instances']['file']).read_text())['instances']
                     if i['p'].startswith(('pallet', 'container_', 'bin_', 'skip_', 'car_', 'van_', 'tractor_', 'trailer_')))
origin = manifest['origin_epsg2180']
obstacles = [translate(shape(f['geometry']).buffer(0), -origin['x'], -origin['y'])
             for f in json.loads((ROOT / 'Data/Regions/bialystok-industrial-c/buildings.geojson').read_text())['features']]
building_count = len(obstacles)


def xy(item, x, y):
    c, s = math.cos(item['yaw']), math.sin(item['yaw'])
    return item['e'] + c*x-s*y, item['n']+s*x+c*y


def bounds(proto):
    if proto.startswith('trailer_'): return (-1.3, 1.3, 0, 13.6)
    if proto.startswith('tractor_'): return (-1.25, 1.25, -1.7, 4.6)
    if proto.startswith(('car_', 'van_')): return (-1.1, 1.1, -2.6, 2.6)
    if proto.startswith('container_'): return (-1.23, 1.23, -6.1, 6.1) if '_40_' in proto else (-1.23, 1.23, -3.04, 3.04)
    if proto.startswith('bin_'): return (-.7, .7, -.6, .6)
    if proto.startswith('skip_'): return (-.95, .95, -2, 2)
    return (-.65, .65, -.45, .45)


for item in instances:
    x0, x1, y0, y1 = bounds(item['p'])
    obstacles.append(Polygon([xy(item, x0, y0), xy(item, x1, y0), xy(item, x1, y1), xy(item, x0, y1)]))
tree = STRtree(obstacles)


def views(item, index, height):
    result = []
    for label, offsets, distance in (
        ('side3', [(0, -3.5), (0, 3.5)], 3.5),
        ('end3', [(-3.5, 0), (3.5, 0)], 3.5),
        ('oblique4', [(sx*3.2, sy*2.5) for sx in (-1, 1) for sy in (-1, 1)], 4.06),
        ('far15', [(-15, 0), (15, 0), (0, -15), (0, 15)], 15)):
        options = []
        for x, y in offsets:
            pos = xy(item, x, y)
            hits = [int(i) for i in tree.query(LineString([pos, (item['e'], item['n'])]), predicate='intersects')
                    if int(i) != building_count + index]
            options.append((len(hits), x, y, pos, hits))
        blocked, x, y, pos, hits = min(options)
        camera = dict(id=f"yard_{item['p']}_prop_{label}", type='persp', kind='inspection', seat='file',
                      pos=[*pos, item['z']+max(1.1 if distance < 5 else 1.6, height/2+.35)],
                      look_at=[item['e'], item['n'], item['z']+height/2], fov_deg=50,
                      note=f"Actual {item['src']}; {blocked} 2D obstacles, render/terrain visibility UNVERIFIED",
                      target_instance=item, obstacle_count=blocked)
        result.append(camera)
    return result


selected, controls, missing = [], [], []
for proto in ('pallets_empty_4', 'pallets_empty_8', 'pallets_empty_12', 'pallets_empty_16'):
    candidates = []
    for index, item in enumerate(instances):
        if item['p'] != proto: continue
        cameras = views(item, index, .144*int(proto.rsplit('_', 1)[1]))
        # Near inspection has priority; the far pose still gets explicit obstacles.
        score = sum(c['obstacle_count']*(1 if c['id'].endswith('far15') else 4) for c in cameras)
        candidates.append((score, str(item['src']), item['e'], item['n'], item, cameras))
    if not candidates:
        missing.append(proto)
        continue
    _, _, _, _, item, cameras = min(candidates, key=lambda x: x[:4])
    selected.append(dict(instance=item, cameras=cameras))

for prefix, height in (('container_20_', 2.59), ('bin_1100_', 1.4)):
    candidates = []
    for index, item in enumerate(instances):
        if not item['p'].startswith(prefix): continue
        cameras = views(item, index, height)
        # One contextual oblique control; no promise to alter these prototypes.
        camera = next(c for c in cameras if c['id'].endswith('oblique4'))
        candidates.append((camera['obstacle_count'], str(item['src']), item['e'], item['n'], item, camera))
    if candidates:
        _, _, _, _, item, camera = min(candidates, key=lambda x: x[:4])
        camera['id'] += '_control'
        controls.append(dict(instance=item, cameras=[camera]))

assert selected, 'No actual empty pallet instances; inspect placement data rather than inventing targets'
new = [c for entry in selected+controls for c in entry['cameras']]
old_ids = {c['id'] for c in packet['cameras']}
assert not (old_ids & {c['id'] for c in new})
packet['cameras'].extend(new)
packet['life_r5_note'] = 'Actual empty pallet targets, four views per available stack class; contextual existing bin/container controls. Poses and occlusion remain subject to render inspection.'
(OUT / 'cameras.json').write_text(json.dumps(packet, indent=2), encoding='utf-8')
report = dict(selected=selected, controls=controls, missing_prototypes=missing, added_cameras=len(new),
              packet_cameras=len(packet['cameras']), candidate_instances=len(instances),
              note='Source data only. No placements changed, no field/GPS/photo correspondence claim.')
(OUT / 'pallet-targets.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(dict(selected=[e['instance'] for e in selected], added=len(new), missing=missing), indent=2))
