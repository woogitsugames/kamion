"""Skanuje Panoramax /api/search w kaflach, zbiera wszystkie kadry i liczy wysokość Słońca z datetime (UTC).
Wynik: JSON listy kadrów z sun_el; kadry z sun_el < -4 to kandydaci nocni."""
import sys, json, os, time, datetime
sys.path.insert(0, sys.argv[1])
from httpc import getjson  # noqa
import sun  # noqa

lat0, lat1, lon0, lon1, step = map(float, sys.argv[2:7])
out = sys.argv[7]
items = {}
sat = []


def scan(la, lo, st, depth=0):
    url = 'https://api.panoramax.xyz/api/search?bbox=%.5f,%.5f,%.5f,%.5f&limit=1000' % (lo, la, lo + st, la + st)
    try:
        d = getjson(url, timeout=120, tries=4)
    except Exception as e:  # noqa
        print('FAIL', url, e, file=sys.stderr)
        return
    fs = d.get('features', [])
    for f in fs:
        p = f['properties']
        dt = p.get('datetime')
        try:
            utc = datetime.datetime.fromisoformat(dt.replace('Z', '+00:00')).astimezone(datetime.timezone.utc).replace(tzinfo=None)
            el, az = sun.elevation_azimuth(utc, f['geometry']['coordinates'][1], f['geometry']['coordinates'][0])
        except Exception:  # noqa
            el = az = None
        items[f['id']] = {'id': f['id'], 'collection': f.get('collection'), 'datetime': dt, 'datetimetz': p.get('datetimetz'),
                          'lon': f['geometry']['coordinates'][0], 'lat': f['geometry']['coordinates'][1],
                          'azimuth': p.get('view:azimuth'), 'license': p.get('license'),
                          'producer': p.get('geovisio:producer'), 'thumb': p.get('geovisio:thumbnail'),
                          'hd': (f.get('assets', {}).get('hd') or {}).get('href'), 'sun_el': el,
                          'model': p.get('exif', {}).get('Exif.Image.Model'),
                          'type': (p.get('pers:interior_orientation') or {}).get('field_of_view')}
    if len(fs) >= 990 and depth < 4:
        h = st / 2
        for a in (0, h):
            for b in (0, h):
                scan(la + a, lo + b, h, depth + 1)
    time.sleep(0.3)


la = lat0
while la < lat1 - 1e-9:
    lo = lon0
    while lo < lon1 - 1e-9:
        scan(la, lo, step)
        lo += step
    la += step
    print('row', la, len(items), file=sys.stderr)
json.dump(list(items.values()), open(out, 'w'))
night = [i for i in items.values() if i['sun_el'] is not None and i['sun_el'] < -4]
print(len(items), 'items;', len(night), 'with sun < -4')
