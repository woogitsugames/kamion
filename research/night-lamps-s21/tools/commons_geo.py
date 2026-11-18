"""Commons: geosearch po siatce punktów Białegostoku (r=1500 m) + tytuły z commons_titles.json,
potem imageinfo (extmetadata, url, sha1, thumb 1600) w paczkach po 50; wysokość Słońca z DateTimeOriginal (czas lokalny PL) i GPS.
Zapis: commons_meta.json (wszystkie), wypis kandydatów nocnych (sun_el < -4)."""
import sys, json, time, urllib.parse, datetime, os, re
sys.path.insert(0, sys.argv[1])
from httpc import getjson  # noqa
import sun  # noqa
titles_in, out = sys.argv[2], sys.argv[3]
API = 'https://commons.wikimedia.org/w/api.php?'


def q(params):
    time.sleep(2.0)
    return getjson(API + urllib.parse.urlencode(dict(params, format='json')), tries=6)


titles = set(json.load(open(titles_in))) if os.path.exists(titles_in) else set()
geo = {}
if '--geo' in sys.argv:
    pts = []
    la = 53.095
    while la <= 53.17:
        lo = 23.09
        while lo <= 23.24:
            pts.append((la, lo)); lo += 0.025
        la += 0.015
    for la, lo in pts:
        r = q(dict(action='query', list='geosearch', gscoord='%.4f|%.4f' % (la, lo), gsradius=1500, gslimit=500, gsnamespace=6))
        for g in r.get('query', {}).get('geosearch', []):
            titles.add(g['title']); geo[g['title']] = (g['lat'], g['lon'])
        print('geo', la, lo, len(titles), file=sys.stderr)
meta = {}
if os.path.exists(out):
    meta = {m['title']: m for m in json.load(open(out))}
todo = [t for t in sorted(titles) if t not in meta]
for i in range(0, len(todo), 50):
    chunk = todo[i:i + 50]
    r = q(dict(action='query', titles='|'.join(chunk), prop='imageinfo|coordinates', iiprop='extmetadata|url|sha1|size|mime',
               iiurlwidth=1600, iiextmetadatafilter='DateTimeOriginal|DateTime|LicenseShortName|Artist|GPSLatitude|GPSLongitude|ImageDescription|Categories'))
    for p in r.get('query', {}).get('pages', {}).values():
        ii = (p.get('imageinfo') or [{}])[0]
        em = ii.get('extmetadata', {})
        g = lambda k: re.sub('<[^>]+>', '', str(em.get(k, {}).get('value', ''))).strip()
        co = (p.get('coordinates') or [{}])[0]
        lat = co.get('lat') or (geo.get(p['title']) or (None, None))[0]
        lon = co.get('lon') or (geo.get(p['title']) or (None, None))[1]
        dto = g('DateTimeOriginal')
        el = None
        m = re.match(r'(\d{4})[:-](\d\d)[:-](\d\d)[ T](\d\d):(\d\d)', dto)
        if m:
            try:
                loc = datetime.datetime(*map(int, m.groups()))
                el = sun.elevation_local(loc, lat or 53.1325, lon or 23.1688)[0]
            except Exception:  # noqa
                el = None
        meta[p['title']] = {'title': p['title'], 'pageid': p.get('pageid'), 'lat': lat, 'lon': lon, 'dto': dto, 'sun_el': el,
                            'license': g('LicenseShortName'), 'artist': g('Artist')[:120], 'desc': g('ImageDescription')[:300],
                            'cats': g('Categories')[:400], 'url': ii.get('url'), 'thumb': ii.get('thumburl'), 'sha1': ii.get('sha1'),
                            'w': ii.get('width'), 'h': ii.get('height'), 'mime': ii.get('mime'), 'page': ii.get('descriptionurl')}
    json.dump(list(meta.values()), open(out, 'w'), ensure_ascii=False)
    print('meta', i + len(chunk), '/', len(todo), file=sys.stderr)
night = [m for m in meta.values() if m['sun_el'] is not None and m['sun_el'] < -4]
print(len(meta), 'files;', len(night), 'night (sun<-4)')
for m in sorted(night, key=lambda m: m['dto']):
    print('%6.1f %s %s | %s' % (m['sun_el'], m['dto'][:16], m['license'], m['title'][5:90]))
