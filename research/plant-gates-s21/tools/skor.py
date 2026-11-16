"""Ortho sheet index lookup: skor.py lat lon -> sheets 2024/2025/2026 (godło, aktualność, piksel)."""
import sys, re, urllib.request
from pyproj import Transformer
lat, lon = float(sys.argv[1]), float(sys.argv[2])
x, y = Transformer.from_crs(4326, 2180, always_xy=True).transform(lon, lat)
for L in ('SkorowidzeOrtofotomapy2026', 'SkorowidzeOrtofotomapy2025', 'SkorowidzeOrtofotomapy2024'):
    url = ('https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/SkorowidzeWgAktualnosci?SERVICE=WMS&VERSION=1.3.0'
           f'&REQUEST=GetFeatureInfo&LAYERS={L}&QUERY_LAYERS={L}&STYLES=&CRS=EPSG:2180&BBOX={y-50},{x-50},{y+50},{x+50}'
           '&WIDTH=101&HEIGHT=101&I=50&J=50&INFO_FORMAT=text/html&FEATURE_COUNT=10')
    t = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'research-client/1.0 (generic)'}), timeout=120).read().decode('utf-8', 'replace')
    for m in re.finditer(r'godlo:"([^"]+)", aktualnosc:"([^"]+)", wielkoscPiksela:"([^"]+)".*?numerZgloszeniaPracy:"([^"]*)"', t):
        print(L[-4:], m.group(1), m.group(2), m.group(3), m.group(4))
