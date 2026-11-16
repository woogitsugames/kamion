import json, math, sys, urllib.request, time
UA = {'User-Agent': 'research-client/1.0 (generic)'}
R = {'skorupska17': (53.133953, 23.180958), 'dobra3': (53.138052, 23.180663), 'zwierzyniecka4': (53.119647, 23.149357),
     'hallera19': (53.153529, 23.125354), 'kopernika5a': (53.121630, 23.143090), 'wiezowiec_m57': (53.153231, 23.168022)}


def dist(a, b):
    la = math.radians((a[0] + b[0]) / 2)
    dx = (b[1] - a[1]) * 111320 * math.cos(la)
    dy = (b[0] - a[0]) * 110574
    return math.hypot(dx, dy), (math.degrees(math.atan2(dx, dy)) + 360) % 360


out = {}
for k, (lat, lon) in R.items():
    d = 0.006
    bb = f'{lon-d*1.7},{lat-d},{lon+d*1.7},{lat+d}'
    url = f'https://api.panoramax.xyz/api/search?bbox={bb}&limit=1000'
    j = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read())
    rows = []
    for f in j['features']:
        lo, la = f['geometry']['coordinates']
        p = f['properties']
        dd, brg = dist((la, lo), (lat, lon))
        az = p.get('view:azimuth')
        fov = (p.get('pers:interior_orientation') or {}).get('field_of_view')
        diff = None if az is None else ((brg - az + 540) % 360) - 180
        rows.append(dict(id=f['id'], coll=f.get('collection'), dt=p.get('datetime'), lat=la, lon=lo, dist=round(dd), brg=round(brg),
                         az=az, fov=fov, diff=None if diff is None else round(diff),
                         sd=f['assets'].get('sd', {}).get('href'), hd=f['assets'].get('hd', {}).get('href'),
                         lic=p.get('license'), prov=[x.get('name') for x in f.get('providers', [])]))
    rows.sort(key=lambda r: r['dist'])
    out[k] = rows
    print(k, len(rows), [(r['dist'], r['diff'], r['fov'], (r['dt'] or '')[:10]) for r in rows[:12]])
    time.sleep(2)
json.dump(out, open(sys.argv[1], 'w'), indent=1)
