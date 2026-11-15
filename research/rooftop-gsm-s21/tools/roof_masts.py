"""Maszty/anteny OSM leżące w obrysie budynku (= dachowe) + wysokość budynku z tagów (height / building:levels)."""
import sys, glob, json
import xml.etree.ElementTree as ET
tiles = sys.argv[1]
nodes, bld, masts = {}, {}, {}
for fn in glob.glob(tiles + '/*.osm'):
    r = ET.parse(fn).getroot()
    for n in r.iter('node'):
        nodes[n.get('id')] = (float(n.get('lat')), float(n.get('lon')))
        t = {x.get('k'): x.get('v') for x in n.findall('tag')}
        if t.get('man_made') in ('mast', 'antenna', 'tower') and t.get('tower:type') in (None, 'communication') or 'communication:mobile_phone' in t:
            if t.get('man_made') in ('mast', 'antenna', 'tower'):
                masts[n.get('id')] = t
    for w in r.iter('way'):
        t = {x.get('k'): x.get('v') for x in w.findall('tag')}
        if 'building' in t:
            bld[w.get('id')] = ([nd.get('ref') for nd in w.findall('nd')], t)


def inside(p, poly):
    c = False
    for (a, b), (c2, d) in zip(poly, poly[1:] + poly[:1]):
        if (b > p[1]) != (d > p[1]) and p[0] < (c2 - a) * (p[1] - b) / (d - b + 1e-15) + a:
            c = not c
    return c


out = []
for mid, t in masts.items():
    p = nodes[mid]
    pp = (p[1], p[0])
    hit = None
    for wid, (refs, bt) in bld.items():
        poly = [(nodes[x][1], nodes[x][0]) for x in refs if x in nodes]
        if len(poly) < 3:
            continue
        if min(q[0] for q in poly) <= pp[0] <= max(q[0] for q in poly) and min(q[1] for q in poly) <= pp[1] <= max(q[1] for q in poly) and inside(pp, poly):
            hit = (wid, bt)
            break
    out.append({'node': mid, 'lat': p[0], 'lon': p[1], 'tags': t, 'building_way': hit[0] if hit else None,
                'building_tags': {k: v for k, v in hit[1].items() if k in ('building', 'building:levels', 'height', 'roof:levels', 'name', 'addr:street', 'addr:housenumber')} if hit else None})
json.dump(out, open(sys.argv[2], 'w'), ensure_ascii=False, indent=0)
for o in out:
    if o['building_way']:
        print(o['node'], '%.6f,%.6f' % (o['lat'], o['lon']), o['tags'].get('man_made'), o['tags'].get('height', ''), 'way', o['building_way'], o['building_tags'])
print(len(out), 'masts;', sum(1 for o in out if o['building_way']), 'on buildings')
