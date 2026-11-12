"""Lightweight metadata-only candidate selection; no download or image processing."""
import json,math
from pathlib import Path
from pyproj import Transformer
root=Path(__file__).resolve().parents[2]; out=Path(__file__).parent
origin=json.loads((root/'Data/Regions/bialystok-industrial-c/generated/world_manifest.json').read_text())['origin_epsg2180']
targets=json.loads((out/'yard-targets.json').read_text())
tf=Transformer.from_crs(4326,2180,always_xy=True)
cache=root/'Data/raw/mapillary/bialystok-industrial-c'
rows=[]
for line in (cache/'manifest.jsonl').read_text(encoding='utf-8-sig').splitlines():
    r=json.loads(line); ident=str(r['id'])
    if not ident.isdigit() or r.get('is_pano') or r.get('license')!='CC BY-SA 4.0':continue
    image=cache/f'{ident}.jpg'
    if not image.is_file():continue
    e,n=tf.transform(r['lon'],r['lat']);e-=origin['x'];n-=origin['y']
    distance=min(math.hypot(e-t['e'],n-t['n']) for t in targets)
    rows.append(dict(id=ident,author=r.get('author'),license=r['license'],captured_at=r.get('captured_at'),distance_to_yard_m=round(distance,1),file=str(image),sha256=r.get('sha256'),page_url=f'https://www.mapillary.com/app/?pKey={ident}'))
rows=sorted(rows,key=lambda r:r['distance_to_yard_m'])[:12]
(out/'yard-photo-candidates.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print(json.dumps(dict(candidates=len(rows),nearest_m=rows[0]['distance_to_yard_m'] if rows else None)))
