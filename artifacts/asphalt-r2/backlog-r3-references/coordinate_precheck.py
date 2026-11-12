"""Lightweight coordinate conversion of three photo metadata points; no raster/world processing."""
import json
from pathlib import Path
from pyproj import Transformer

folder = Path('artifacts/asphalt-r2/backlog-r3-references')
data = json.loads((folder / 'pcrt-api-20200711.json').read_text(encoding='utf-8-sig'))
transform = Transformer.from_crs(4326, 2180, always_xy=True)
rows = []
for page in data['query']['pages']:
    info = page['imageinfo'][0]
    metadata = info['extmetadata']
    lat = metadata.get('GPSLatitude', {}).get('value')
    lon = metadata.get('GPSLongitude', {}).get('value')
    if not lat or not lon:
        rows.append(dict(title=page['title'], pose='UNVERIFIED: no coordinates in this file'))
        continue
    x, y = transform.transform(float(lon), float(lat))
    e, n = x - 777995.0, y - 596223.0
    rows.append(dict(title=page['title'], latitude=float(lat), longitude=float(lon),
                     epsg2180=[round(x, 3), round(y, 3)], local_en=[round(e, 3), round(n, 3)],
                     within_region=776971 <= x <= 779019 and 595199 <= y <= 597247,
                     inside_kwadrat_exclusion=400 <= e <= 850 and -700 <= n <= -250,
                     pose='Approximate photo metadata point; not a fitted camera pose'))
(folder / 'pcrt-coordinate-precheck.json').write_text(json.dumps(rows, indent=2)+'\n', encoding='utf-8')
print(json.dumps(rows, indent=2))
