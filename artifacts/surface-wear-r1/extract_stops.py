from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools/worldgen'))
from streetscape import sources as S
path=ROOT/'Data/Regions/bialystok-industrial-c/generated/streetscape_sources.json';old=json.loads(path.read_text());new=S.extract_osm(old['bbox'],ROOT/'Data/raw/osm/podlaskie-261108.osm.pbf')
a={x['osm_node']:x for x in old['osm']['nodes']};b={x['osm_node']:x for x in new['nodes']};assert a.keys()<=b.keys();updates=[]
for k,x in a.items():
 y=b[k];yy=dict(y);yy['tags']=dict(y['tags']);yy['tags'].pop('bus',None);assert yy==x,(k,x,yy)
 if x!=y:updates.append(k)
assert new['areas']==old['osm']['areas'] and new['ways']==old['osm']['ways']
added=[b[k]for k in b.keys()-a.keys()];assert len(added)==20 and all(x['tags'].get('public_transport')=='stop_position'and x['tags'].get('bus')=='yes'for x in added)
result=dict(old);result['osm']=new
(OUT/'streetscape-sources-with-stops.json').write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n',encoding='utf-8')
proof=dict(original_source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),added_stop_positions=20,added_osm_nodes=sorted(x['osm_node']for x in added),existing_node_bus_tag_only_updates=updates,existing_ways_areas_geometry_unchanged=True,note='Canonicalextract_osm from samepinnedrawPBF; NOT yet installed/worldgenerated.')
(OUT/'stop-selector-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
