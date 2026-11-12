"""Bounded reference download; credentials and signed image URLs stay in memory."""
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

output = HERE/'mapillary-pole-target'
existing = set(output.glob('*.jpg'))
try:
    credential = fetch.resolve_token()
    if not credential:
        print('Reference credential unavailable; no credential values logged')
        raise SystemExit(2)
    args = fetch.build_parser().parse_args([
        '--region','bialystok-industrial-c','--points',str(HERE/'lamp-photo-search.json'),
        '--radius','35','--azimuth-tol','50','--per-camera','2','--max','8',
        '--out',str(output),'--fetch'])
    fetch.run(args,client=MemoryClient(credential))
except Exception as error:
    # Do not expose an exception containing a signed CDN URL. Keep incomplete new images out of the packet.
    for image in set(output.glob('*.jpg'))-existing:
        image.unlink()
    print(f'Reference fetch failed ({type(error).__name__}); URLs and credentials omitted')
    raise SystemExit(1)
