"""Read only original PBF stop positions; selector gap is not source absence."""
from pathlib import Path
import osmium,json,hashlib
from pyproj import Transformer
ROOT=Path(__file__).resolve().parents[2]
p=ROOT/'Data/raw/osm/podlaskie-261108.osm.pbf'
t=Transformer.from_crs(4326,2180,always_xy=True)
rows=[];regional=0
for o in osmium.FileProcessor(str(p)).with_filter(osmium.filter.TagFilter(('public_transport','stop_position'))):
 if not o.is_node() or not o.location.valid():continue
 regional+=1;x,y=t.transform(o.location.lon,o.location.lat)
 if 776971<=x<=779019 and 595199<=y<=597247:rows.append(dict(osm_node=o.id,tags=dict(o.tags),epsg2180=[x,y],local_en=[x-777995,y-596223]))
out=dict(source=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),regional_stop_positions=regional,region_stop_positions=rows,note='ExistingPBFread-only node selector. Roadside/direction/photographic stoppingzone still needs validation; no decal placement inferred.')
(ROOT/'artifacts/surface-wear-r1/busstop-raw-proof.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out))
