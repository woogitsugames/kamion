"""Fetch GUGiK ortho (WMS StandardResolution / HighResolution) around a WGS84 point.
Usage: ortho.py out.jpg lat lon half_m px [service]"""
import sys, subprocess
from pyproj import Transformer
out, la, lo, half, px = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5])
svc = sys.argv[6] if len(sys.argv) > 6 else 'HighResolution'
t = Transformer.from_crs(4326, 2180, always_xy=True)
x, y = t.transform(lo, la)
# EPSG:2180 WMS 1.3.0 axis order is northing,easting
bbox = f'{y-half},{x-half},{y+half},{x+half}'
url = (f'https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/{svc}?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap'
       f'&LAYERS=Raster&STYLES=&CRS=EPSG:2180&BBOX={bbox}&WIDTH={px}&HEIGHT={px}&FORMAT=image/jpeg')
r = subprocess.run(['curl', '-sS', '-m', '120', '-o', out, '-w', '%{http_code} %{content_type}', url], capture_output=True, text=True)
print(r.stdout, f'x={x:.1f} y={y:.1f} m/px={2*half/px:.3f}')
print(url)
