"""Light metadata projection only: 16 coordinates, no image or geometry loading."""
from pathlib import Path
import hashlib,json,math
from pyproj import Transformer

ROOT=Path(__file__).resolve().parents[2];ART=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
source=ART/'commons-first300-metadata.json';body=read(source)
assert body['status']=='METADATA_RECEIVED'
region=ROOT/'Data/Regions/bialystok-industrial-c'
segment_path=region/'gate3_segment.json';world_path=region/'generated/world_manifest.json'
points=next(s['points_en'] for s in read(segment_path)['segments'] if s['id']=='G3-A')
origin=read(world_path)['origin_epsg2180']
project=Transformer.from_crs('EPSG:4326','EPSG:2180',always_xy=True)
manifest_path=ROOT/'Data/raw/refs/objects/kwadrat-park/commons-geo/manifest.jsonl'
existing={json.loads(line)['id'] for line in manifest_path.read_text(encoding='utf-8-sig').splitlines() if line}
rows=[]
for page in body['response']['query']['pages'].values():
    coord=page.get('coordinates',[])
    if not coord:continue
    c=coord[0];x,y=project.transform(c['lon'],c['lat']);x-=origin['x'];y-=origin['y']
    station=0;best=None
    for a,b in zip(points,points[1:]):
        dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
        t=max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/(length*length))) if length else 0
        distance=math.hypot(x-a[0]-t*dx,y-a[1]-t*dy)
        if best is None or distance<best[0]:best=(distance,station+t*length)
        station+=length
    meta=page.get('imageinfo',[{}])[0].get('extmetadata',{})
    value=lambda key:meta.get(key,{}).get('value')
    sid='cm'+str(page['pageid'])
    rows.append({'id':sid,'title':page['title'],'page_url':'https://commons.wikimedia.org/?curid='+str(page['pageid']),
                 'coordinates':c,'local_en':[x,y],'route_distance_m':round(best[0],3),'station_m':round(best[1],3),
                 'within_first300_corridor':best[1]<=300 and best[0]<=35,'already_in_local_manifest':sid in existing,
                 'license':value('LicenseShortName'),'license_url':value('LicenseUrl'),'artist_html':value('Artist'),
                 'date_time_original':value('DateTimeOriginal'),'description_html':value('ImageDescription')})
result={'scope':'Coordinates are source metadata, not proven camera pose or image coverage. No image inspected or downloaded.',
        'inputs_sha256':{str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in (source,segment_path,world_path,manifest_path)},
        'origin_epsg2180':origin,'corridor_width_m':35,'rows':sorted(rows,key=lambda r:r['station_m'])}
(ART/'commons-first300-classified.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for r in result['rows']:
    print(r['id'],r['station_m'],r['route_distance_m'],'FIRST300' if r['within_first300_corridor'] else '-', 'EXISTING' if r['already_in_local_manifest'] else 'NEW',r['license'])
