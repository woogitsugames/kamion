import json, sys, urllib.request, urllib.parse, time, math
UA = {'User-Agent': 'research-client/1.0 (generic)'}
R = {'skorupska17': (53.133953, 23.180958), 'dobra3': (53.138052, 23.180663), 'zwierzyniecka4': (53.119647, 23.149357),
     'hallera19': (53.153529, 23.125354), 'kopernika5a': (53.121630, 23.143090), 'wiezowiec_m57': (53.153231, 23.168022)}


def get(params):
    params.update(format='json')
    url = 'https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode(params)
    for i in range(6):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read())
        except Exception as e:
            sys.stderr.write(f'retry {i} {e}\n')
            time.sleep(60 if '429' in str(e) else 5)
    raise RuntimeError(url)


out = {}
for k, (lat, lon) in R.items():
    j = get(dict(action='query', list='geosearch', gscoord=f'{lat}|{lon}', gsradius=1000, gsnamespace=6, gslimit=500, gsprop='type|name'))
    rows = j['query']['geosearch']
    out[k] = rows
    print(k, len(rows))
    for r in rows[:60]:
        print('   ', round(r['dist']), r['title'])
    time.sleep(4)
json.dump(out, open(sys.argv[1], 'w'), indent=1)
