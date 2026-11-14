"""Ekstrakcja drzew/szpalerów/żywopłotów OSM w granicach Białegostoku z ekstraktu PBF.
Zastępuje zapytanie Overpass (tools/q_trees.overpassql) — serwery Overpass były nieosiągalne
przez proxy 2026-11-14 17:05–17:10 UTC. Uruchom:
  uv run --with osmium --with shapely python -I tools/osm_extract_trees.py files/osm/podlaskie.osm.pbf data/
"""
import json, sys, os
import osmium
from shapely import wkb as swkb
from shapely.geometry import Point, LineString
from shapely.prepared import prep

pbf, out = sys.argv[1], sys.argv[2]
wkbf = osmium.geom.WKBFactory()

class Boundary(osmium.SimpleHandler):
    geom = None
    def area(self, a):
        if a.tags.get('boundary') == 'administrative' and a.tags.get('admin_level') == '8' \
           and a.tags.get('name') == 'Białystok' and not a.from_way():
            self.geom = swkb.loads(wkbf.create_multipolygon(a), hex=True)
            self.rel_id = a.orig_id()

b = Boundary()
b.apply_file(pbf, locations=True, filters=[osmium.filter.KeyFilter('boundary')])
assert b.geom is not None
P = prep(b.geom)
minx, miny, maxx, maxy = b.geom.bounds
print('boundary relation', b.rel_id, 'bounds', b.geom.bounds, file=sys.stderr)

class H(osmium.SimpleHandler):
    def __init__(s):
        super().__init__(); s.trees = []; s.rows = []; s.hedges = []; s.roads = []
    def node(s, n):
        if n.tags.get('natural') == 'tree':
            lon, lat = n.location.lon, n.location.lat
            if minx <= lon <= maxx and miny <= lat <= maxy and P.contains(Point(lon, lat)):
                s.trees.append({'id': n.id, 'lat': round(lat, 7), 'lon': round(lon, 7), 'tags': dict(n.tags)})
    def way(s, w):
        t = w.tags
        kind = None
        if t.get('natural') == 'tree_row': kind = 'rows'
        elif t.get('barrier') == 'hedge': kind = 'hedges'
        elif 'highway' in t and t['highway'] in ('motorway','trunk','primary','secondary','tertiary','unclassified',
              'residential','living_street','service','motorway_link','trunk_link','primary_link','secondary_link','tertiary_link'):
            kind = 'roads'
        if not kind: return
        try:
            pts = [(round(n.lon, 7), round(n.lat, 7)) for n in w.nodes]
        except osmium.InvalidLocationError:
            return
        if len(pts) < 2: return
        ls = LineString(pts)
        if not P.intersects(ls): return
        getattr(s, kind).append({'id': w.id, 'tags': dict(t), 'geom': pts})

h = H()
h.apply_file(pbf, locations=True)
os.makedirs(out, exist_ok=True)
meta = {'boundary_relation': b.rel_id, 'pbf': os.path.basename(pbf)}
for k in ('trees', 'rows', 'hedges', 'roads'):
    json.dump({'meta': meta, 'elements': getattr(h, k)}, open(os.path.join(out, f'osm_{k}.json'), 'w'),
              ensure_ascii=False, separators=(',', ':'))
    print(k, len(getattr(h, k)), file=sys.stderr)
