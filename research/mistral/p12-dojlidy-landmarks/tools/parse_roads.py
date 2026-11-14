#!/usr/bin/env python3
"""P12: drogi jezne OSM (highway=*) z pełną geometrią -> data/road-geom.json.

road-geom.json usunięto z gałęzi (pochodna OSM, M48-FIX pkt 5 / M48-FIX-2).
Odtworzenie (README, sekcja „Pliki badania” — pkt 4):
  curl -o osm-roads.osm "https://api.openstreetmap.org/api/0.6/map?bbox=23.1570,53.0920,23.2020,53.1210"
  python3 tools/parse_roads.py osm-roads.osm
(bbox = kafel referencyjny bialystok-dojlidy + bufor; ODbL. Wyciąg API zwraca
każdy way z co najmniej jednym węzłem w bboxie wraz z pełną geometrią.)

Skrypt filtruje drogi jezdne (bez footway/cycleway/path/steps/track/pedestrian/
raceway), deduplikuje way-e po id (dla wyciągów sklejanych z pod-kafli) i zapisuje
{ts, roads: [{id, hw, name, ref, maxspeed, geom[lat,lon], xy[EPSG:2180]}]}.
Wymaga epsg2180.py w tym samym katalogu.
"""
import json, sys, time
import xml.etree.ElementTree as ET
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from epsg2180 import tm_forward

HW = ('motorway', 'motorway_link', 'trunk', 'trunk_link', 'primary', 'primary_link',
      'secondary', 'secondary_link', 'tertiary', 'tertiary_link', 'unclassified',
      'residential', 'living_street', 'service', 'road')


def main(paths):
    nodes, seen, roads = {}, set(), []
    for path in paths:
        root = ET.parse(path).getroot()
        for n in root.findall('node'):
            nodes[int(n.get('id'))] = (float(n.get('lat')), float(n.get('lon')))
        for w in root.findall('way'):
            wid = int(w.get('id'))
            if wid in seen:
                continue
            t = {tk.get('k'): tk.get('v') for tk in w.findall('tag')}
            if t.get('highway') not in HW:
                continue
            pts = [nodes[int(nd.get('ref'))] for nd in w.findall('nd')
                   if int(nd.get('ref')) in nodes]
            if len(pts) < 2:
                continue
            seen.add(wid)
            geom = [[round(p[0], 6), round(p[1], 6)] for p in pts]
            roads.append({'id': wid, 'hw': t['highway'],
                          'name': t.get('name', ''), 'ref': t.get('ref', ''),
                          'maxspeed': t.get('maxspeed', ''),
                          'geom': geom,
                          'xy': [[round(x, 1), round(y, 1)] for x, y in
                                 (tm_forward(*p) for p in geom)]})
    roads.sort(key=lambda r: r['id'])
    out = {'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'roads': roads}
    json.dump(out, open('data/road-geom.json', 'w'), ensure_ascii=False, indent=1)
    print('road-geom:', len(roads), 'dróg -> data/road-geom.json')


if __name__ == '__main__':
    main(sys.argv[1:])
