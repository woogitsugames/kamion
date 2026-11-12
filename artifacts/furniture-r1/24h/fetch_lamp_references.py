"""Bounded reference download; credentials and signed image URLs stay in memory."""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0,str(ROOT/'tools/refs'))
import mapillary_fetch as fetch

class MemoryClient(fetch.MapillaryClient):
    def __init__(self,credential):
        super().__init__(credential,cache_dir=None,retries=1)
        self.boxes = {}

    def images_in_bbox(self,bbox):
        key = tuple(round(value,6) for value in bbox)
        if key not in self.boxes:
            self.boxes[key] = super().images_in_bbox(bbox)
        return self.boxes[key]

parser = argparse.ArgumentParser()
parser.add_argument('--radius',type=int,choices=[35,75],default=35)
parser.add_argument('--pano',action='store_true')
options = parser.parse_args()
suffix = '' if options.radius == 35 and not options.pano else f'-r{options.radius}'+('-pano' if options.pano else '')
output = HERE/f'mapillary-pole-target{suffix}'
existing = set(output.glob('*.jpg'))
try:
    credential = fetch.resolve_token()
    if not credential:
        print('Reference credential unavailable; no credential values logged')
        raise SystemExit(2)
    args = fetch.build_parser().parse_args([
        '--region','bialystok-industrial-c','--points',str(HERE/'lamp-photo-search.json'),
        '--radius',str(options.radius),'--azimuth-tol','50','--per-camera','2','--max','8',
        '--out',str(output),'--fetch']+(['--pano'] if options.pano else []))
    client = MemoryClient(credential)
    selected = fetch.run(args,client=client)
    centre = fetch.load_points(HERE/'lamp-photo-search.json','bialystok-industrial-c')[0]
    records = {str(row['id']):row for rows in client.boxes.values() for row in rows}
    nearest = []
    for identity,record in records.items():
        position = fetch.record_lonlat(record)
        if position:
            nearest.append(dict(id=identity,distance_m=round(fetch.haversine_m(
                centre['lon'],centre['lat'],*position),1),is_pano=bool(record.get('is_pano')),
                compass_angle=record.get('compass_angle')))
    summary = dict(radius_m=options.radius,panoramas_allowed=options.pano,
                   returned_records=len(records),pano_records=sum(bool(row.get('is_pano')) for row in records.values()),
                   selected_images=len(selected),centre_lonlat=[centre['lon'],centre['lat']],
                   nearest=sorted(nearest,key=lambda row:row['distance_m'])[:8],
                   calibration='UNVERIFIED model diagnostic point; no real pole position established')
    (output/'query-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(f"Query summary: returned={len(records)}, selected={len(selected)}, radius={options.radius}m")
except Exception as error:
    # Do not expose an exception containing a signed CDN URL. Keep incomplete new images out of the packet.
    for image in set(output.glob('*.jpg'))-existing:
        image.unlink()
    print(f'Reference fetch failed ({type(error).__name__}); URLs and credentials omitted')
    raise SystemExit(1)
