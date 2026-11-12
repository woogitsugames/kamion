"""One bounded read-only retry of the original start-of-route metadata query; no shared raw writes."""
from pathlib import Path
from datetime import datetime,timezone
import json,socket,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/refs'))
OUT=Path(__file__).with_name('first300-retry');OUT.mkdir(exist_ok=True)
result={'checked_at_utc':datetime.now(timezone.utc).isoformat(),'scope':'Original r1 bbox near G3-A start; not proof of all first 300m coverage.',
        'bbox_lonlat':[23.169747,53.154215,23.171095,53.155023],'thumbnail_downloaded':False,'records':[]}
try:
    socket.getaddrinfo('graph.mapillary.com',443,type=socket.SOCK_STREAM)
    from mapillary_fetch import MapillaryClient,resolve_token,API,FIELDS
    token=resolve_token()
    if not token:result['status']='NO_CONFIGURED_CREDENTIAL'
    else:
        client=MapillaryClient(token,retries=0,cache_dir=None)
        body=client._get(API,params={'bbox':','.join(str(v) for v in result['bbox_lonlat']),'fields':FIELDS,'limit':100}).json()
        for row in body.get('data',[]):
            safe={k:row.get(k) for k in ('id','captured_at','compass_angle','computed_geometry','is_pano','sequence')}
            creator=row.get('creator') or {}
            safe['creator']={k:creator.get(k) for k in ('id','username')} if isinstance(creator,dict) else str(creator)
            safe['page_url']='https://www.mapillary.com/app/?pKey='+str(row.get('id',''))
            result['records'].append(safe)
        result['status']='METADATA_RECEIVED';result['more_pages_available']=bool(body.get('paging',{}).get('next'))
except Exception as exc:
    # Never log exception text, request headers, token values or signed thumbnail URLs.
    result['status']='UNAVAILABLE';result['error_class']=type(exc).__name__
(OUT/'metadata.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':result['status'],'records':len(result['records']),'error_class':result.get('error_class')}))
