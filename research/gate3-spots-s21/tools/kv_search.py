"""KartaView nearby photos for each point; course from neighbouring frames of the same sequence.
Usage: kv_search.py out.json radius"""
import json, sys, os, subprocess, time
sys.path.insert(0, os.path.dirname(__file__))
from geo import P, dist, near
R = sys.argv[2] if len(sys.argv) > 2 else '80'


def get(url):
    for k in range(5):
        r = subprocess.run(['curl', '-sS', '-m', '60', url], capture_output=True, text=True)
        try:
            return json.loads(r.stdout)
        except Exception:
            time.sleep(5 * (k + 1))
    return None


allp = {}
for key, (la, lo) in P.items():
    page = 1
    while True:
        d = get(f'https://api.kartaview.org/2.0/photo/?lat={la}&lng={lo}&radius={R}&itemsPerPage=100&page={page}')
        data = d['result']['data']
        for x in data:
            x['_pt'] = x.get('_pt', '') + key
            allp.setdefault(x['id'], x)
        if not d['result'].get('hasMoreData') or page > 10:
            break
        page += 1
# course from neighbours
bySeq = {}
for x in allp.values():
    bySeq.setdefault(x['sequenceId'], {})[int(x['sequenceIndex'])] = x
for sid, idx in bySeq.items():
    for i, x in idx.items():
        nb = idx.get(i + 1) or idx.get(i + 2)
        pv = idx.get(i - 1) or idx.get(i - 2)
        a = (float(x['lat']), float(x['lng']))
        c = None
        if nb:
            d_, c = dist(a, (float(nb['lat']), float(nb['lng'])))
            if d_ < 1: c = None
        if c is None and pv:
            d_, c = dist((float(pv['lat']), float(pv['lng'])), a)
            if d_ < 1: c = None
        x['_course'] = None if c is None else round(c, 1)
json.dump(allp, open(sys.argv[1], 'w'), indent=1)
for x in sorted(allp.values(), key=lambda x: (x['sequenceId'], int(x['sequenceIndex']))):
    print(x['id'], x['sequenceId'], x['sequenceIndex'], x['shotDate'][:16], x['lat'], x['lng'], 'hdg', x['heading'], 'course', x['_course'], x['width'], x['height'], near(float(x['lat']), float(x['lng'])))
