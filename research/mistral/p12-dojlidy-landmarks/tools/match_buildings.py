#!/usr/bin/env python3
"""P12: łączy OSM budynki (data/osm-buildings.json) z LoD1 wysokościami i BDOT10k funkcjami
(dopasowanie centroidów, tolerancja 35 m / 30 m) -> data/matched-buildings.json."""
import json, math, sys
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from epsg2180 import tm_forward

def nearest(la, lo, arr, maxd):
    x, y = tm_forward(la, lo)
    best, bd = None, 1e9
    for b in arr:
        bx, by = (b['cx'], b['cy']) if 'cx' in b else tm_forward(b['lat'], b['lon'])
        d = (bx - x) ** 2 + (by - y) ** 2
        if d < bd: bd, best = d, b
    return best if bd <= maxd * maxd else None

def main():
    B = json.load(open('data/osm-buildings.json'))
    H = json.load(open('data/lod1-wysokosci.json'))
    D = json.load(open('data/bdot-budynki.json'))
    out = []
    for b in B:
        if not b['in_tile']: continue
        L = nearest(b['lat'], b['lon'], H, 35)
        Dd = nearest(b['lat'], b['lon'], D, 30)
        t = b['tags']
        out.append({'osm_id': b['id'], 'lat': b['lat'], 'lon': b['lon'], 'area_m2': b['area'],
                    'osm_building': t.get('building'), 'name': t.get('name', ''),
                    'addr': (t.get('addr:street', '') + ' ' + t.get('addr:housenumber', '')).strip(),
                    'lod_h': float(L['h']) if L else None, 'roofType': L['roofType'] if L else None,
                    'bdot_funkcja_og': Dd['funkcja_og'] if Dd else None,
                    'bdot_funkcja_sz': Dd['funkcja_sz'] if Dd else None,
                    'bdot_kond': Dd['kond'] if Dd else None})
    json.dump(out, open('data/matched-buildings.json', 'w'), ensure_ascii=False)
    print('matched:', len(out))

if __name__ == '__main__':
    main()
