import json, sys, urllib.request, time
UA = {'User-Agent': 'research-client/1.0 (generic)'}
R = {'skorupska17': (53.133953, 23.180958), 'dobra3': (53.138052, 23.180663), 'zwierzyniecka4': (53.119647, 23.149357),
     'hallera19': (53.153529, 23.125354), 'kopernika5a': (53.121630, 23.143090), 'wiezowiec_m57': (53.153231, 23.168022)}
out = {}
for k, (la, lo) in R.items():
    for dy in (-0.008, 0, 0.008):
        for dx in (-0.013, 0, 0.013):
            url = f'https://api.kartaview.org/2.0/photo/?lat={la+dy:.6f}&lng={lo+dx:.6f}&radius=500&itemsPerPage=100'
            try:
                d = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90).read())
                for p in d['result']['data']:
                    out[p['id']] = {x: p.get(x) for x in ('id', 'lat', 'lng', 'heading', 'shotDate', 'sequenceId', 'fileurlProc', 'imageProcUrl', 'width', 'height', 'fieldOfView', 'projection')}
                print(k, dx, dy, len(d['result']['data']), flush=True)
            except Exception as e:
                print(k, dx, dy, 'ERR', e, flush=True)
            time.sleep(1)
json.dump(list(out.values()), open(sys.argv[1], 'w'))
print(len(out))
