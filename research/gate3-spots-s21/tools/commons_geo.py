import json, sys, os, subprocess, urllib.parse
sys.path.insert(0, os.path.dirname(__file__))
from geo import P, near
UA = 'research-client/1.0 (generic)'
out = {}
for k, (la, lo) in P.items():
    url = ('https://commons.wikimedia.org/w/api.php?action=query&format=json&list=geosearch&gsnamespace=6&gslimit=500'
           f'&gsradius=400&gscoord={la}%7C{lo}')
    import time
    for i in range(6):
        r = subprocess.run(['curl', '-sS', '-m', '60', '-A', UA, url], capture_output=True, text=True)
        try:
            d = json.loads(r.stdout); d['query']; break
        except Exception:
            print('retry', r.stdout[:80], file=sys.stderr); time.sleep(15 * (i + 1))
    time.sleep(5)
    out[k] = d['query']['geosearch']
    print(k, len(out[k]))
json.dump(out, open(sys.argv[1], 'w'), ensure_ascii=False, indent=1)
seen = set()
for k, v in out.items():
    for g in v:
        if g['title'] in seen:
            continue
        seen.add(g['title'])
        print(g['title'], round(g['lat'], 6), round(g['lon'], 6), near(g['lat'], g['lon']))
