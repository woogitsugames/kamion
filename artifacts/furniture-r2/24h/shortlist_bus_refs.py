"""Small metadata-only reference shortlist; no generation, mesh or image processing."""
import json
import math
from pathlib import Path
from pyproj import Transformer

root = Path(__file__).resolve().parents[3]
source = root / 'Data/Regions/bialystok-industrial-c/generated/streetscape_sources.json'
manifest = root / 'Data/raw/mapillary/bialystok-industrial-c/manifest.jsonl'
photos = [json.loads(line) for line in manifest.read_text(encoding='utf-8-sig').splitlines() if line.strip()]
project = Transformer.from_crs(4326, 2180, always_xy=True)
for photo in photos:
    photo['_en'] = project.transform(photo['lon'], photo['lat'])
stops = [node for node in json.loads(source.read_text(encoding='utf-8-sig'))['osm']['nodes']
         if node['tags'].get('highway') == 'bus_stop']
result = []
for stop in stops:
    e, n = stop['geometry']['coordinates']
    ordered = sorted(photos, key=lambda p: (p['_en'][0]-e)**2+(p['_en'][1]-n)**2)[:3]
    approach = []
    for photo in photos:
        de, dn = e-photo['_en'][0], n-photo['_en'][1]
        distance = math.hypot(de, dn)
        bearing = math.degrees(math.atan2(de, dn)) % 360
        angle = abs((bearing-photo.get('compass_angle', 0)+180) % 360-180)
        if 15 <= distance <= 120 and angle <= 55:
            approach.append(dict(id=photo['id'], file=photo['file'], distance_m=round(distance,1),
                                 target_angle_deg=round(angle,1), page_url=photo['page_url']))
    approach.sort(key=lambda p: p['distance_m']+p['target_angle_deg']*.4)
    result.append(dict(osm_node=stop['osm_node'], tags=stop['tags'], source_en=[e,n],
        approach_photos=approach[:3],
        photos=[dict(id=p['id'], file=p['file'], distance_m=round(((p['_en'][0]-e)**2+(p['_en'][1]-n)**2)**.5,1),
                     compass_angle=p.get('compass_angle'), author=p['author'], license=p['license'],
                     page_url=p['page_url'], captured_at=p['captured_at'], sha256=p['sha256']) for p in ordered]))
out = Path(__file__).with_name('bus-reference-shortlist.json')
out.write_text(json.dumps(dict(caveat='Proximity only, not visibility or evidence of a shelter/bin. Inspect photos before a change.',
                               stops=result), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(f'{len(stops)} stops, {len(photos)} existing licensed photo records; shortlist saved')
