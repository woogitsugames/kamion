import json, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from geo import near
for f in sys.argv[1:]:
    d = json.load(open(f))
    for x in d['features']:
        lo, la = x['geometry']['coordinates']
        p = x['properties']
        print(x['id'], x.get('collection', '')[:8], p['datetime'][:16], round(la, 6), round(lo, 6), 'az', p.get('view:azimuth'), near(la, lo))
