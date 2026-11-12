"""Metadata-only direction hints beyond station 300; no images, rays or pose approval."""
from pathlib import Path
import hashlib,json,sys
from pyproj import Geod,Transformer

ROOT=Path(__file__).resolve().parents[2];ART=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
source=ROOT/'artifacts/sbs-r2/first300-retry/metadata-full300.json'
region=ROOT/'Data/Regions/bialystok-industrial-c'
segment_path=region/'gate3_segment.json';world_path=ART/'evidence/inputs/world_manifest.json'
reference_path=ART/'evidence/inputs/sbs_references.json'
points=next(s['points_en'] for s in read(segment_path)['segments'] if s['id']=='G3-A')
origin=read(world_path)['origin_epsg2180']
lon,lat=Transformer.from_crs('EPSG:2180','EPSG:4326',always_xy=True).transform(points[0][0]+origin['x'],points[0][1]+origin['y'])
known={r['source_id'] for r in read(reference_path)['references']}
geod=Geod(ellps='WGS84');rows=[]
for row in read(source)['records']:
    coordinates=(row.get('computed_geometry') or {}).get('coordinates')
    heading=row.get('compass_angle')
    if coordinates is None or heading is None:continue
    toward,_,distance=geod.inv(coordinates[0],coordinates[1],lon,lat)
    delta=(heading-toward+180)%360-180
    rows.append({'id':row['id'],'page_url':row['page_url'],'creator':row.get('creator'),
        'station_m':row['station_m'],'route_distance_m':row['route_distance_m'],'computed_geometry':row['computed_geometry'],
        'captured_at':row.get('captured_at'),'compass_angle':heading,'bearing_toward_start_deg':toward%360,
        'heading_delta_to_start_deg':delta,'distance_to_start_m':distance,'already_in_reference_set':row['id'] in known,
        'is_pano':row.get('is_pano'),
        'direction_candidate_only':row['id'] not in known and not row.get('is_pano') and row['route_distance_m']<=35 and abs(delta)<=45})
rows.sort(key=lambda r:(not r['direction_candidate_only'],abs(r['heading_delta_to_start_deg'])))
result={'scope':'Historical metadata hints only: camera station is not image coverage; visibility, actual heading and two anchors still unverified. No production reference or pose added.',
        'inputs_sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (source,segment_path,world_path,reference_path)},
        'start_lonlat':[lon,lat],'rows':rows}
(ART/'near-start-direction-candidates.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for row in rows:
    if row['direction_candidate_only']:print(row['id'],'station',row['station_m'],'heading delta',round(row['heading_delta_to_start_deg'],1),'distance',round(row['distance_to_start_m'],1))
