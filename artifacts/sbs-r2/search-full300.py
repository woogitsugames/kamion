"""Bounded metadata-only search near first 300m; signed URLs remain in memory only."""
from pathlib import Path
from datetime import datetime,timezone
import json,math,sys
from pyproj import Transformer
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/refs'))
from mapillary_fetch import MapillaryClient,resolve_token,API,FIELDS
REGION=ROOT/'Data/Regions/bialystok-industrial-c';OUT=Path(__file__).with_name('first300-retry');OUT.mkdir(exist_ok=True)
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
points=next(s['points_en'] for s in read(REGION/'gate3_segment.json')['segments'] if s['id']=='G3-A')
origin=read(REGION/'generated/world_manifest.json')['origin_epsg2180'];partial=[points[0]];distance=0
for a,b in zip(points,points[1:]):
    length=math.dist(a,b)
    if distance+length>=300:
        t=(300-distance)/length;partial.append([a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])]);break
    partial.append(b);distance+=length
left=min(p[0] for p in partial)+origin['x']-35;right=max(p[0] for p in partial)+origin['x']+35
bottom=min(p[1] for p in partial)+origin['y']-35;top=max(p[1] for p in partial)+origin['y']+35
ll=Transformer.from_crs('EPSG:2180','EPSG:4326',always_xy=True)
corners=[ll.transform(x,y) for x,y in ((left,bottom),(left,top),(right,bottom),(right,top))]
bbox=[min(p[0] for p in corners),min(p[1] for p in corners),max(p[0] for p in corners),max(p[1] for p in corners)]
to_local=Transformer.from_crs('EPSG:4326','EPSG:2180',always_xy=True)
def project(lon,lat):
    x,y=to_local.transform(lon,lat);x-=origin['x'];y-=origin['y'];along=0;best=None
    for a,b in zip(points,points[1:]):
        dx=b[0]-a[0];dy=b[1]-a[1];length=math.hypot(dx,dy)
        t=max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/(length*length))) if length else 0
        d=math.hypot(x-a[0]-t*dx,y-a[1]-t*dy)
        if best is None or d<best[0]:best=(d,along+t*length)
        along+=length
    return best
result={'checked_at_utc':datetime.now(timezone.utc).isoformat(),'bbox_lonlat':bbox,'limit':2000,'padding_m':35,
        'scope':'First 300m of stored G3-A; one page only; metadata search does not establish pose or coverage.', 'records':[],'candidates':[]}
try:
    token=resolve_token()
    if not token:result['status']='NO_CONFIGURED_CREDENTIAL'
    else:
        client=MapillaryClient(token,retries=0,cache_dir=None)
        body=client._get(API,params={'bbox':','.join(f'{v:.6f}' for v in bbox),'fields':FIELDS,'limit':2000}).json()
        result['more_pages_available']=bool(body.get('paging',{}).get('next'))
        for row in body.get('data',[]):
            safe={k:row.get(k) for k in ('id','captured_at','compass_angle','computed_geometry','is_pano','sequence')}
            creator=row.get('creator') or {};safe['creator']={k:creator.get(k) for k in ('id','username')} if isinstance(creator,dict) else str(creator)
            safe['page_url']='https://www.mapillary.com/app/?pKey='+str(row.get('id',''))
            coordinates=(row.get('computed_geometry') or {}).get('coordinates')
            if coordinates:
                d,station=project(*coordinates[:2]);safe.update(route_distance_m=round(d,3),station_m=round(station,3))
                if station<=300 and d<=35 and not row.get('is_pano'):result['candidates'].append(safe)
            result['records'].append(safe)
        result['status']='METADATA_RECEIVED'
except Exception as exc:result.update(status='UNAVAILABLE',error_class=type(exc).__name__)
(OUT/'metadata-full300.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':result['status'],'records':len(result['records']),'candidates':len(result['candidates']),'more_pages_available':result.get('more_pages_available'),'error_class':result.get('error_class')}))
