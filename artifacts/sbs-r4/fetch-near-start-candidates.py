"""Bounded reference I/O only. No decoding, composition, credentials or signed URLs in output."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys

ROOT=Path(__file__).resolve().parents[2];ART=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools/refs'))
from mapillary_fetch import MapillaryClient,resolve_token,FIELDS,LICENSE,LICENSE_URL
source=ART/'near-start-direction-candidates.json'
data=json.loads(source.read_text(encoding='utf-8-sig'))
chosen=[r for r in data['rows'] if r['direction_candidate_only']][:3]
assert len(chosen)==3 and all(r['id'].isdigit() for r in chosen)
OUT=ART/'near-start-photos';OUT.mkdir(exist_ok=True)
manifest=OUT/'manifest.json'
if manifest.exists():raise SystemExit('Manifest already exists; inspect existing receipt instead of repeating downloads')
result={'created_at_utc':datetime.now(timezone.utc).isoformat(),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'scope':'At most three public reference thumbnails; metadata hints, not accepted coverage or poses. No original images or heavy processing.',
        'license':LICENSE,'license_url':LICENSE_URL,'rows':[]}
token=resolve_token()
client=MapillaryClient(token,retries=0,cache_dir=None) if token else None
for candidate in chosen:
    sid=candidate['id'];dest=OUT/(sid+'.jpg')
    safe={'id':sid,'page_url':candidate['page_url'],'station_m':candidate['station_m'],
          'heading_delta_to_start_deg':candidate['heading_delta_to_start_deg'],'license':LICENSE,'license_url':LICENSE_URL}
    try:
        if client is None:raise RuntimeError('No configured credential')
        if dest.exists():raise RuntimeError('Candidate image already exists')
        record=client._get('https://graph.mapillary.com/'+sid,params={'fields':FIELDS}).json()
        if str(record.get('id'))!=sid or record.get('is_pano') or not record.get('thumb_2048_url'):
            raise RuntimeError('Unexpected source record')
        creator=record.get('creator') or {}
        safe.update(creator={key:creator.get(key) for key in ('id','username')} if isinstance(creator,dict) else str(creator),
                    captured_at=record.get('captured_at'),compass_angle=record.get('compass_angle'),
                    computed_geometry=record.get('computed_geometry'),is_pano=record.get('is_pano'))
        # The signed URL stays in memory; MapillaryClient sends no OAuth header to the image host.
        digest=client.download(record['thumb_2048_url'],dest)
        safe.update(status='DOWNLOADED_UNREVIEWED',file=dest.relative_to(ROOT).as_posix(),sha256=digest,bytes=dest.stat().st_size)
    except Exception as exc:
        safe.update(status='UNAVAILABLE',error_class=type(exc).__name__)
    result['rows'].append(safe)
    manifest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(sid,safe['status'])
print('Completed bounded reference I/O; no pose or coverage acceptance')
