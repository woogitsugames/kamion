"""Openverse: wyszukiwanie obrazów (page_size 20, bez klucza), zapis wyników do JSON."""
import sys, json, time, urllib.parse
sys.path.insert(0, sys.argv[1])
from httpc import getjson  # noqa
out = sys.argv[2]
qs = sys.argv[3:]
res = {}
for q in qs:
    for page in range(1, 6):
        url = 'https://api.openverse.org/v1/images/?' + urllib.parse.urlencode({'q': q, 'page_size': 20, 'page': page})
        try:
            d = getjson(url, tries=2)
        except Exception as e:  # noqa
            print('fail', q, page, e, file=sys.stderr)
            break
        for r in d.get('results', []):
            r['_q'] = q
            res.setdefault(r['id'], r)
        if page >= d.get('page_count', 0):
            break
        time.sleep(1)
    print(q, len(res), file=sys.stderr)
json.dump(list(res.values()), open(out, 'w'), ensure_ascii=False)
for r in res.values():
    print(r['source'], r['license'], r.get('license_version'), (r.get('title') or '')[:70], r['foreign_landing_url'])
