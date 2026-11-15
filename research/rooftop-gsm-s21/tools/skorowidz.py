"""M67-FIX: skorowidze GUGiK (ortofoto + LIDAR) dla dachów K67.

Uruchom: uv run --with pyproj python -I tools/skorowidz.py tools out/skorowidz.json
Zapytanie WFS 1.0.0 GetFeature, bbox 4 × 4 m w EPSG:2180 wokół punktu dachu.
"""
import sys, json, re, urllib.parse
sys.path.insert(0, sys.argv[1])
from httpc import get  # noqa
from pyproj import Transformer

ROOFS = {
    'skorupska17': (53.133953, 23.180958),
    'dobra3': (53.138052, 23.180663),
    'zwierzyniecka4': (53.119647, 23.149357),
    'hallera19': (53.153529, 23.125354),
    'kopernika5a': (53.121630, 23.143090),
}
T = Transformer.from_crs('EPSG:4326', 'EPSG:2180', always_xy=True)
SRV = {
    'ORTO': ('https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WFS/Skorowidze',
             ['gugik:SkorowidzOrtofomapy%d' % y for y in range(2018, 2027)]),
    'LIDAR': ('https://mapy.geoportal.gov.pl/wss/service/PZGIK/DanePomiaroweLidarEVRF2007/WFS/Skorowidze',
              ['gugik:SkorowidzDanychPomiarowychLIDAR%d' % y for y in range(2018, 2027)]),
}
FIELDS = ['godlo', 'akt_rok', 'akt_data', 'piksel', 'kolor', 'url_do_pobrania', 'wlk_pliku_mb', 'zrodlo_danych',
          'czy_ark_wypelniony', 'uklad_xy', 'char_przestrz', 'bladsrd', 'format', 'uklad_h', 'nazwa_pliku',
          'data_nalotu', 'dt_pzgik', 'modul_archiwizacji']
out = {}
for name, (lat, lon) in ROOFS.items():
    x, y = T.transform(lon, lat)
    out[name] = {'lat': lat, 'lon': lon, 'x2180': round(x, 2), 'y2180': round(y, 2)}
    for prod, (base, layers) in SRV.items():
        feats = []
        for lay in layers:
            q = {'service': 'WFS', 'version': '1.0.0', 'request': 'GetFeature', 'typename': lay,
                 'srsname': 'EPSG:2180', 'bbox': '%.2f,%.2f,%.2f,%.2f' % (x - 2, y - 2, x + 2, y + 2),
                 'maxfeatures': '25'}
            url = base + '?' + urllib.parse.urlencode(q)
            try:
                xml = get(url, timeout=120, tries=3).decode('utf-8', 'replace')
            except Exception as e:  # noqa
                feats.append({'layer': lay, 'error': str(e)[:200]})
                continue
            for m in re.finditer(r'<gml:featureMember>(.*?)</gml:featureMember>', xml, re.S):
                body = m.group(1)
                f = {'layer': lay}
                for k in FIELDS:
                    mm = re.search(r'<gugik:%s>([^<]*)</gugik:%s>' % (k, k), body)
                    if mm:
                        f[k] = mm.group(1)
                feats.append(f)
        out[name][prod] = feats
        print(name, prod, [(f.get('akt_data'), f.get('godlo'), f.get('piksel') or f.get('char_przestrz')) for f in feats if 'error' not in f])
json.dump(out, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1)
