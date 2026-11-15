"""Wyciąga z kafli OSM API 0.6 obiekty man_made=mast/antenna/tower(communication) oraz location=roof; zapis JSON."""
import sys, glob, json
import xml.etree.ElementTree as ET
tiles, out = sys.argv[1], sys.argv[2]
res = {}
for fn in glob.glob(tiles + '/*.osm'):
    r = ET.parse(fn).getroot()
    nodes = {n.get('id'): (float(n.get('lat')), float(n.get('lon'))) for n in r.iter('node')}
    for el in list(r.iter('node')) + list(r.iter('way')):
        t = {x.get('k'): x.get('v') for x in el.findall('tag')}
        if t.get('man_made') in ('mast', 'antenna', 'tower', 'communications_tower') or 'communication:mobile_phone' in t:
            if el.tag == 'node':
                ll = (float(el.get('lat')), float(el.get('lon')))
            else:
                pts = [nodes[nd.get('ref')] for nd in el.findall('nd') if nd.get('ref') in nodes]
                if not pts:
                    continue
                ll = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
            res[el.tag + '/' + el.get('id')] = {'id': el.tag + '/' + el.get('id'), 'lat': ll[0], 'lon': ll[1], 'tags': t,
                                                 'version': el.get('version'), 'timestamp': el.get('timestamp')}
json.dump(list(res.values()), open(out, 'w'), ensure_ascii=False, indent=0)
for v in res.values():
    t = v['tags']
    print(v['id'], '%.6f,%.6f' % (v['lat'], v['lon']), {k: t[k] for k in t if k in ('man_made', 'tower:type', 'height', 'location', 'tower:construction', 'communication:mobile_phone', 'name', 'building', 'operator')})
print(len(res))
