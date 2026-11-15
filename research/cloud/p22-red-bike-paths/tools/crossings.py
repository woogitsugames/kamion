#!/usr/bin/env python3
"""M65: przeciecia DDR/CPR z jezdniami (wspolne wezly OSM) -> crossings.json
Uruchom: python3 -I tools/crossings.py"""
import json, os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geo import to2180, bearing
from inventory import TILES, ROAD, is_cycle
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main():
    d = json.load(open(os.path.join(HERE, 'overpass-result.json'), encoding='utf-8'))
    inv = {r['way_id']: r for r in json.load(open(os.path.join(HERE, 'inventory.json'), encoding='utf-8'))['ways']}
    ways = [e for e in d['elements'] if e['type'] == 'way']
    nodes = {e['id']: e for e in d['elements'] if e['type'] == 'node'}
    pos = {}
    use = {}
    for w in ways:
        for nid, g in zip(w['nodes'], w['geometry']):
            pos[nid] = (g['lat'], g['lon'])
            use.setdefault(nid, []).append(w)
    out = []
    for nid, ws in use.items():
        cyc = [w for w in ws if w['id'] in inv]
        rds = [w for w in ws if w['tags'].get('highway') in ROAD]
        if not cyc or not rds:
            continue
        lat, lon = pos[nid]
        x, y = to2180(lat, lon)
        reg = [n for n, b in TILES.items() if b[0] <= x <= b[2] and b[1] <= y <= b[3]]
        if not reg:
            continue
        # czy DDR przechodzi przez wezel (wezel wewnetrzny albo >= 2 odcinki pieszo-rowerowe)
        through = any(0 < w['nodes'].index(nid) < len(w['nodes']) - 1 for w in cyc) or \
            len([w for w in ws if w['tags'].get('highway') in ('cycleway', 'path', 'footway')]) >= 2
        r = rds[0]
        i = r['nodes'].index(nid)
        j = i + 1 if i + 1 < len(r['nodes']) else i - 1
        g = r['geometry']
        rb = bearing(g[min(i, j)]['lat'], g[min(i, j)]['lon'], g[max(i, j)]['lat'], g[max(i, j)]['lon'])
        ntags = nodes.get(nid, {}).get('tags', {})
        out.append({'node_id': nid, 'region': reg[0], 'lat': round(lat, 7), 'lon': round(lon, 7),
                    'node_tags': ntags, 'through': through,
                    'cycle_ways': [{'way_id': w['id'], 'tags': w['tags']} for w in cyc],
                    'roads': [{'way_id': w['id'], 'highway': w['tags']['highway'], 'name': w['tags'].get('name', ''),
                               'ref': w['tags'].get('ref', ''), 'lanes': w['tags'].get('lanes', ''),
                               'oneway': w['tags'].get('oneway', ''), 'service': w['tags'].get('service', ''),
                               'junction': w['tags'].get('junction', '')} for w in rds],
                    'road_bearing_deg': round(rb, 0),
                    'kind': 'wjazd' if all(w['tags']['highway'] == 'service' for w in rds) else 'jezdnia'})
    out.sort(key=lambda r: (r['region'], r['kind'], r['node_id']))
    json.dump(out, open(os.path.join(HERE, 'crossings.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    from collections import Counter
    print(Counter((r['region'], r['kind'], r['through']) for r in out))

if __name__ == '__main__':
    main()
