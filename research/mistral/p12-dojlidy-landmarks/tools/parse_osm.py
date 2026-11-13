#!/usr/bin/env python3
"""P12: wyciąg OSM (/api/0.6/map) -> compact JSON (data/osm-*.json).
Pobranie: curl -o osm-map.osm "https://api.openstreetmap.org/api/0.6/map?bbox=23.1600,53.0955,23.1980,53.1180"
Uruchomienie: python3 parse_osm.py osm-map.osm
Filtruje budynki/linie/POI/obszary, liczy centroidy, powierzchnie EPSG:2180 i przynależność do kafla
(bbox [778660,589590,780660,591590]). Wymaga epsg2180.py w tym samym katalogu."""
import sys, json
import xml.etree.ElementTree as ET
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from epsg2180 import tm_forward

X0, Y0, X1, Y1 = 778660, 589590, 780660, 591590

def centroid(pts):
    if len(pts) >= 4 and pts[0] == pts[-1]:
        A = cx = cy = 0.0
        for i in range(len(pts) - 1):
            x1, y1 = pts[i]; x2, y2 = pts[i + 1]
            cr = x1 * y2 - x2 * y1
            A += cr; cx += (x1 + x2) * cr; cy += (y1 + y2) * cr
        if abs(A) > 1e-12:
            return cx / (3 * A), cy / (3 * A)
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))

def area_m2(pts):
    if len(pts) >= 4 and pts[0] == pts[-1]:
        xy = [tm_forward(*p) for p in pts]
        s = sum(xy[i][0] * xy[i + 1][1] - xy[i + 1][0] * xy[i][1] for i in range(len(xy) - 1))
        return abs(s) / 2
    return 0

def inside(pt):
    x, y = tm_forward(*pt)
    return X0 <= x <= X1 and Y0 <= y <= Y1

def main(path):
    root = ET.parse(path).getroot()
    nodes = {int(n.get('id')): (float(n.get('lat')), float(n.get('lon'))) for n in root.findall('node')}
    ways = []
    for w in root.findall('way'):
        ways.append((int(w.get('id')),
                     {t.get('k'): t.get('v') for t in w.findall('tag')},
                     [int(nd.get('ref')) for nd in w.findall('nd')]))
    def poly(nds): return [nodes[r] for r in nds if r in nodes]
    buildings, lines, areas = [], [], []
    for wid, t, nds in ways:
        pts = poly(nds)
        if not pts: continue
        c = centroid(pts)
        if 'building' in t:
            buildings.append({'id': wid, 'lat': round(c[0], 6), 'lon': round(c[1], 6),
                              'area': round(area_m2(pts)), 'in_tile': inside(c), 'tags': t})
        elif any(k in t for k in ('highway', 'railway', 'waterway')):
            lines.append({'id': wid, 'kind': 'highway' if 'highway' in t else ('railway' if 'railway' in t else 'waterway'),
                          'lat': round(c[0], 6), 'lon': round(c[1], 6), 'in_tile': inside(c), 'tags': t})
        elif len(pts) >= 4 and pts[0] == pts[-1] and any(k in t for k in ('landuse', 'leisure', 'aeroway', 'amenity', 'natural', 'man_made', 'military', 'power', 'railway', 'barrier')):
            areas.append({'id': wid, 'lat': round(c[0], 6), 'lon': round(c[1], 6), 'area': round(area_m2(pts)),
                          'in_tile': inside(c), 'tags': t})
    pois = []
    for n in root.findall('node'):
        t = {tk.get('k'): tk.get('v') for tk in n.findall('tag')}
        if t and any(k in t for k in ('amenity', 'man_made', 'aeroway', 'highway', 'barrier', 'natural', 'leisure', 'landuse', 'tourism', 'shop', 'railway', 'waterway', 'power', 'emergency', 'public_transport', 'crossing', 'traffic_calming', 'advertising', 'historic', 'military')):
            la, lo = float(n.get('lat')), float(n.get('lon'))
            pois.append({'id': int(n.get('id')), 'lat': round(la, 6), 'lon': round(lo, 6), 'in_tile': inside((la, lo)), 'tags': t})
    for name, obj in (('osm-buildings', buildings), ('osm-lines', lines), ('osm-pois', pois), ('osm-areas', areas)):
        json.dump(obj, open(f'data/{name}.json', 'w'), ensure_ascii=False)
        print(name, len(obj))

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'osm-map.osm')
