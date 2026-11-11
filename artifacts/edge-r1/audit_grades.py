"""Compare the old straight-stub grade with the apron underneath its actual XY path."""
import json
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/worldgen'))
from streetscape import far_field as FF

region = 'bialystok-industrial-c'
reg = FF.pipeline.load_region(region)
origin = np.array([reg['origin']['x'], reg['origin']['y']])
graph = json.loads((ROOT / 'Data/Regions' / region / 'roads.graph.json').read_text())
boundary = {n['id'] for n in graph['nodes'] if n.get('boundary')}
elev = FF.BorderElevation.from_region(region)
rows = []
for edge in graph['edges']:
    for at_start, node in [(True, edge['from']), (False, edge['to'])]:
        if node not in boundary:
            continue
        pts = np.array(edge['geometry']) - origin
        if at_start:
            pts = pts[::-1]
        direction = pts[-1] - pts[-2]
        direction /= np.linalg.norm(direction)
        start = pts[-1]
        z0, zsm = elev.border_z_and_smooth(*start)
        gaps = []
        for distance in np.linspace(0, 420, 13):
            t1 = np.clip(distance / 220, 0, 1)
            t2 = np.clip((distance - 220) / 1400, 0, 1)
            old_apron = z0 + (zsm - .15 - z0) * t1*t1*(3-2*t1)
            old_apron += (zsm - .25 + .08*(elev.mean-zsm) - old_apron)*t2*t2*(3-2*t2)
            t = np.clip(distance/120, 0, 1)
            crown = z0+.03+(old_apron+.14-z0-.03)*t*t*(3-2*t)
            actual_xy = start + direction * distance
            gaps.append(round(float(crown - elev.z_at_eff(*actual_xy)), 3))
        rows.append(dict(road=edge.get('attrs', {}).get('name', {}).get('v'),
                         edge=edge.get('id'), start=start.tolist(), direction=direction.tolist(),
                         min_clearance_m=min(gaps), clearances_m=gaps))
rows.sort(key=lambda row: row['min_clearance_m'])
(Path(__file__).parent / 'grade-audit.json').write_text(json.dumps(rows, indent=2))
for row in rows:
    if row['min_clearance_m'] < -.1:
        print(row['road'], np.round(row['start'], 1), row['min_clearance_m'])
