"""GUGiK ortho GetMap: ortho.py lat lon width_m height_m gsd out.jpg  (EPSG:2180, BBOX N,E order for WMS 1.3.0)."""
import sys, os, urllib.request
from pyproj import Transformer
lat, lon, wm, hm, gsd = map(float, sys.argv[1:6])
out = sys.argv[6]
T = Transformer.from_crs(4326, 2180, always_xy=True)
x, y = T.transform(lon, lat)  # x=E, y=N
w = int(round(wm / gsd)); h = int(round(hm / gsd))
e0, e1 = x - wm / 2, x + wm / 2
n0, n1 = y - hm / 2, y + hm / 2
url = ('https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/HighResolution?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap'
       f'&LAYERS=Raster&STYLES=&CRS=EPSG:2180&BBOX={n0:.2f},{e0:.2f},{n1:.2f},{e1:.2f}&WIDTH={w}&HEIGHT={h}&FORMAT=image/jpeg')
req = urllib.request.Request(url, headers={'User-Agent': 'research-client/1.0 (generic)'})
d = urllib.request.urlopen(req, timeout=300).read()
open(out, 'wb').write(d)
print(url)
print('E', round(e0, 2), round(e1, 2), 'N', round(n0, 2), round(n1, 2), w, h, len(d))
