"""Pobiera OSM API 0.6 /map w kaflach 0,01 x 0,01 deg (Overpass niedostępny przez proxy 2026-11-15).
Wyciąga: węzły highway=street_lamp (z tagami) i drogi highway=* z geometrią. Zapis do JSON (format zbliżony do Overpass out geom)."""
import sys, json, os, time, math
import xml.etree.ElementTree as ET
sys.path.insert(0, sys.argv[1])
from httpc import get  # noqa

lat0, lat1, lon0, lon1 = map(float, sys.argv[2:6])
out = sys.argv[6]
tdir = out + '.tiles'
os.makedirs(tdir, exist_ok=True)
step = 0.01
lamps = {}
ways = {}
nodes = {}
la = lat0
while la < lat1 - 1e-9:
    lo = lon0
    while lo < lon1 - 1e-9:
        fn = os.path.join(tdir, '%.3f_%.3f.osm' % (la, lo))
        if not os.path.exists(fn) or os.path.getsize(fn) < 100:
            url = 'https://api.openstreetmap.org/api/0.6/map?bbox=%.4f,%.4f,%.4f,%.4f' % (lo, la, lo + step, la + step)
            b = get(url, timeout=120)
            open(fn, 'wb').write(b)
            time.sleep(1.0)
        root = ET.parse(fn).getroot()
        for n in root.iter('node'):
            nid = int(n.get('id'))
            nodes[nid] = (float(n.get('lat')), float(n.get('lon')))
            tags = {t.get('k'): t.get('v') for t in n.findall('tag')}
            if tags.get('highway') == 'street_lamp':
                lamps[nid] = {'type': 'node', 'id': nid, 'lat': nodes[nid][0], 'lon': nodes[nid][1], 'tags': tags,
                              'version': int(n.get('version')), 'timestamp': n.get('timestamp')}
        for w in root.iter('way'):
            tags = {t.get('k'): t.get('v') for t in w.findall('tag')}
            if 'highway' in tags:
                wid = int(w.get('id'))
                ways[wid] = {'type': 'way', 'id': wid, 'tags': tags, 'nodes': [int(nd.get('ref')) for nd in w.findall('nd')]}
        lo += step
    la += step
    print('row', la, len(lamps), len(ways), file=sys.stderr)
for w in ways.values():
    w['geometry'] = [{'lat': nodes[r][0], 'lon': nodes[r][1]} if r in nodes else None for r in w['nodes']]
json.dump({'generator': 'OSM API 0.6 /map tiles', 'bbox': [lat0, lon0, lat1, lon1],
           'fetched_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
           'elements': list(lamps.values()) + list(ways.values())}, open(out, 'w'))
print(len(lamps), 'lamps', len(ways), 'ways')
