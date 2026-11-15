"""Budynki z building:levels >= N (z kafli OSM), środek i obrys bbox."""
import sys, glob, json
import xml.etree.ElementTree as ET
tiles, N = sys.argv[1], int(sys.argv[2])
nodes, res = {}, {}
for fn in glob.glob(tiles + '/*.osm'):
    r = ET.parse(fn).getroot()
    for n in r.iter('node'):
        nodes[n.get('id')] = (float(n.get('lat')), float(n.get('lon')))
    for w in r.iter('way'):
        t = {x.get('k'): x.get('v') for x in w.findall('tag')}
        try:
            lv = float(t.get('building:levels', '0').split(';')[0])
        except ValueError:
            lv = 0
        if 'building' in t and lv >= N:
            res[w.get('id')] = ([nd.get('ref') for nd in w.findall('nd')], t, lv)
out = []
for wid, (refs, t, lv) in res.items():
    pts = [nodes[x] for x in refs if x in nodes]
    if not pts:
        continue
    la = [p[0] for p in pts]; lo = [p[1] for p in pts]
    out.append({'way': wid, 'levels': lv, 'height': t.get('height'), 'name': t.get('name'), 'addr': '%s %s' % (t.get('addr:street', ''), t.get('addr:housenumber', '')),
                'lat': sum(la) / len(la), 'lon': sum(lo) / len(lo), 'bbox': [min(la), min(lo), max(la), max(lo)]})
out.sort(key=lambda o: -o['levels'])
json.dump(out, open(sys.argv[3], 'w'), ensure_ascii=False, indent=0)
for o in out[:40]:
    print(o['way'], o['levels'], o['height'], o['name'], o['addr'], '%.6f,%.6f' % (o['lat'], o['lon']))
print(len(out))
