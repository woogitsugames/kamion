"""Metadata-only inspection of the separate Panoramax cache for next-round refs."""
import json
import math
from pathlib import Path
from pyproj import Transformer

root = Path(__file__).resolve().parents[2]
out = Path(__file__).parent
cache = root / 'Data/raw/refs/panoramax'
origin = json.loads((root / 'Data/Regions/bialystok-industrial-c/generated/world_manifest.json').read_text())['origin_epsg2180']
targets = json.loads((out / 'yard-targets.json').read_text())
tf = Transformer.from_crs(4326, 2180, always_xy=True)
rows = []
for line in (cache / 'manifest.jsonl').read_text(encoding='utf-8-sig').splitlines():
    row = json.loads(line)
    if row.get('license') != 'CC-BY-SA-4.0':
        continue
    image = (cache / row['file']).resolve()
    if not image.is_relative_to(cache.resolve()) or not image.is_file():
        continue
    e, n = tf.transform(row['lon'], row['lat'])
    distance = min(math.hypot(e - origin['x'] - t['e'], n - origin['y'] - t['n']) for t in targets)
    rows.append({k: row.get(k) for k in ('id', 'file', 'author', 'license', 'captured_at', 'lat', 'lon', 'heading', 'sha256', 'page_url')} | {'distance_to_yard_m': round(distance, 1)})
rows.sort(key=lambda r: r['distance_to_yard_m'])
(out / 'panoramax-preflight.json').write_text(json.dumps(rows[:12], indent=2), encoding='utf-8')
print(json.dumps({'available': len(rows), 'nearest_m': rows[0]['distance_to_yard_m'] if rows else None}))
