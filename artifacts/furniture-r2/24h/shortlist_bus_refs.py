"""Small metadata-only reference shortlist; no generation, mesh or image processing."""
import json
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
    result.append(dict(osm_node=stop['osm_node'], tags=stop['tags'], source_en=[e,n],
        photos=[dict(id=p['id'], file=p['file'], distance_m=round(((p['_en'][0]-e)**2+(p['_en'][1]-n)**2)**.5,1),
                     compass_angle=p.get('compass_angle'), author=p['author'], license=p['license'],
                     page_url=p['page_url'], captured_at=p['captured_at'], sha256=p['sha256']) for p in ordered]))
out = Path(__file__).with_name('bus-reference-shortlist.json')
out.write_text(json.dumps(dict(caveat='Proximity only, not visibility or evidence of a shelter/bin. Inspect photos before a change.',
                               stops=result), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(f'{len(stops)} stops, {len(photos)} existing licensed photo records; shortlist saved')
