#!/usr/bin/env python3
"""M65: inwentarz DDR / ciagow pieszo-rowerowych z overpass-result.json -> inventory.json
Uruchom: python3 -I tools/inventory.py   (z katalogu research/cloud/p22-red-bike-paths)"""
import json, math, os, sys, statistics
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geo import to2180, from2180, haversine

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TILES = {'C': (776971.0, 595199.0, 779019.0, 597247.0), 'Dojlidy': (779019.0, 589055.0, 781067.0, 591103.0)}
ROAD = {'motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'unclassified', 'residential', 'living_street',
        'motorway_link', 'trunk_link', 'primary_link', 'secondary_link', 'tertiary_link', 'service'}

def is_cycle(t):
    h = t.get('highway')
    if h == 'cycleway':
        return True
    if h in ('path', 'footway', 'pedestrian') and t.get('bicycle') == 'designated':
        return True
    return False

def clip_len(p, q, b):
    """dlugosc odcinka p-q wewnatrz prostokata b (Liang-Barsky), uklad 2180"""
    x0, y0 = p; x1, y1 = q; dx, dy = x1 - x0, y1 - y0
    t0, t1 = 0.0, 1.0
    for pp, qq in ((-dx, x0 - b[0]), (dx, b[2] - x0), (-dy, y0 - b[1]), (dy, b[3] - y0)):
        if pp == 0:
            if qq < 0: return 0.0
        else:
            r = qq / pp
            if pp < 0: t0 = max(t0, r)
            else: t1 = min(t1, r)
    return max(0.0, t1 - t0) * math.hypot(dx, dy) if t1 > t0 else 0.0

def seg_dist(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay
    l2 = dx * dx + dy * dy
    t = 0 if l2 == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / l2))
    cx, cy = ax + t * dx, ay + t * dy
    return math.hypot(px - cx, py - cy), math.atan2(dx, dy)

def main():
    d = json.load(open(os.path.join(HERE, 'overpass-result.json'), encoding='utf-8'))
    ways = [e for e in d['elements'] if e['type'] == 'way']
    for w in ways:
        w['xy'] = [to2180(g['lat'], g['lon']) for g in w['geometry']]
    roads = [w for w in ways if w['tags'].get('highway') in ROAD and w['tags'].get('area') != 'yes']
    # siatka przestrzenna odcinkow jezdni (komorka 50 m)
    grid = {}
    for w in roads:
        for i in range(len(w['xy']) - 1):
            a, b = w['xy'][i], w['xy'][i + 1]
            for gx in range(int(min(a[0], b[0]) // 50) - 1, int(max(a[0], b[0]) // 50) + 2):
                for gy in range(int(min(a[1], b[1]) // 50) - 1, int(max(a[1], b[1]) // 50) + 2):
                    grid.setdefault((gx, gy), []).append((w, a, b))
    out = []
    for w in ways:
        t = w['tags']
        if not is_cycle(t):
            continue
        xy = w['xy']; geo = w['geometry']
        length = sum(haversine(geo[i]['lat'], geo[i]['lon'], geo[i + 1]['lat'], geo[i + 1]['lon']) for i in range(len(geo) - 1))
        regs = {}
        for name, b in TILES.items():
            l = sum(clip_len(xy[i], xy[i + 1], b) for i in range(len(xy) - 1)) / 0.9993  # ~skala odwzorowania
            if l > 0.05:
                regs[name] = l
        if not regs:
            continue
        region = max(regs, key=regs.get)
        # skala lokalna 2180 vs haversine
        l2180 = sum(math.hypot(xy[i + 1][0] - xy[i][0], xy[i + 1][1] - xy[i][1]) for i in range(len(xy) - 1))
        k = length / l2180 if l2180 else 1
        len_in = regs[region] * 0.9993 * k
        # droga rownolegla: probki co 5 m
        samples = []
        for i in range(len(xy) - 1):
            a, b = xy[i], xy[i + 1]
            n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) // 5))
            for j in range(n):
                f = (j + 0.5) / n
                samples.append(((a[0] + f * (b[0] - a[0]), a[1] + f * (b[1] - a[1])), math.atan2(b[0] - a[0], b[1] - a[1])))
        votes = {}
        for p, brg in samples:
            best = {}
            for (w2, a, b) in grid.get((int(p[0] // 50), int(p[1] // 50)), []):
                dist, brg2 = seg_dist(p, a, b)
                dd = abs((brg - brg2 + math.pi / 2) % math.pi - math.pi / 2)
                if dist <= 40 and dd <= math.radians(30):
                    if w2['id'] not in best or dist < best[w2['id']][0]:
                        best[w2['id']] = (dist, w2)
            # glosuje najblizsza jezdnia; drogi 'service' tylko gdy nie ma innej
            cands = sorted(best.values(), key=lambda v: (v[1]['tags']['highway'] == 'service', v[0]))
            if cands:
                dist, w2 = cands[0]
                votes.setdefault(w2['id'], []).append(dist)
        par = None
        if votes:
            wid = max(votes, key=lambda i: len(votes[i]))
            share = len(votes[wid]) / len(samples)
            if share >= 0.3:
                w2 = next(r for r in roads if r['id'] == wid)
                par = {'way_id': wid, 'highway': w2['tags']['highway'], 'name': w2['tags'].get('name', ''),
                       'ref': w2['tags'].get('ref', ''), 'lanes': w2['tags'].get('lanes', ''), 'oneway': w2['tags'].get('oneway', ''),
                       'dist_median_m': round(statistics.median(votes[wid]) * k, 1),
                       'dist_min_m': round(min(votes[wid]) * k, 1), 'dist_max_m': round(max(votes[wid]) * k, 1),
                       'share': round(share, 2),
                       'others': sorted(((i, len(v)) for i, v in votes.items() if i != wid), key=lambda z: -z[1])[:3]}
        out.append({'way_id': w['id'], 'region': region, 'regions': {a: round(b, 1) for a, b in regs.items()},
                    'tags': t, 'length_m': round(length, 1), 'length_in_tile_m': round(len_in, 1),
                    'start': [round(geo[0]['lat'], 7), round(geo[0]['lon'], 7)],
                    'end': [round(geo[-1]['lat'], 7), round(geo[-1]['lon'], 7)],
                    'n_nodes': len(geo), 'node_ids': w['nodes'], 'parallel': par})
    out.sort(key=lambda r: (r['region'], r['way_id']))
    json.dump({'osm_base': d['osm3s']['timestamp_osm_base'], 'ways': out}, open(os.path.join(HERE, 'inventory.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for reg in TILES:
        rs = [r for r in out if r['region'] == reg]
        print(reg, 'odcinki:', len(rs), 'suma dl. calk. [m]:', round(sum(r['length_m'] for r in rs), 1), 'w kaflu [m]:', round(sum(r['length_in_tile_m'] for r in rs), 1))

if __name__ == '__main__':
    main()
