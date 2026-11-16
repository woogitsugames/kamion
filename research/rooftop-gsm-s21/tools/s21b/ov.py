import json, sys, urllib.request, urllib.parse, time
UA = {'User-Agent': 'research-client/1.0 (generic)'}
qs = sys.argv[2:]
out = {}
try:
    out = json.load(open(sys.argv[1]))
except Exception:
    pass
for q in qs:
    for page in (1, 2, 3):
        url = 'https://api.openverse.org/v1/images/?' + urllib.parse.urlencode(dict(q=q, license_type='commercial', page_size=20, page=page, source='wikimedia'))
        try:
            d = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read())
        except Exception as e:
            sys.stderr.write(f'{q} {page} {e}\n'); break
        for r in d.get('results', []):
            out[r['id']] = {k: r.get(k) for k in ('title', 'url', 'foreign_landing_url', 'license', 'license_version', 'creator', 'width', 'height')}
            out[r['id']]['q'] = q
        print(q, page, d.get('result_count'), len(d.get('results', [])))
        if page >= (d.get('page_count') or 1):
            break
        time.sleep(3)
    time.sleep(3)
json.dump(out, open(sys.argv[1], 'w'), indent=1)
print(len(out))
