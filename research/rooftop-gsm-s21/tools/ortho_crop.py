"""Wycinek ortofoto GUGiK WMS HighResolution (EPSG:4326) wokół punktu, bok S m, 0,1 m/px (max 1000 px), z linijką 10 m. Północ u góry."""
import sys, math, io, urllib.parse, hashlib
sys.path.insert(0, sys.argv[1])
from httpc import get  # noqa
from PIL import Image, ImageDraw
name, lat, lon, S = sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])
out = sys.argv[6]
kx = 111320.0 * math.cos(math.radians(lat)); kz = 110574.0
px = min(1000, int(S / float(sys.argv[7]) if len(sys.argv) > 7 else S / 0.1))
bbox = (lat - S / 2 / kz, lon - S / 2 / kx, lat + S / 2 / kz, lon + S / 2 / kx)
p = {'SERVICE': 'WMS', 'VERSION': '1.3.0', 'REQUEST': 'GetMap', 'LAYERS': 'Raster', 'STYLES': '', 'CRS': 'EPSG:4326',
     'BBOX': '%.7f,%.7f,%.7f,%.7f' % bbox, 'WIDTH': px, 'HEIGHT': px, 'FORMAT': 'image/jpeg'}
u = 'https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/HighResolution?' + urllib.parse.urlencode(p)
b = get(u, timeout=180)
im = Image.open(io.BytesIO(b)).convert('RGB')
d = ImageDraw.Draw(im)
mpp = S / px
L = int(10 / mpp)
d.rectangle((10, px - 22, 10 + L, px - 16), fill=(255, 255, 0), outline=(0, 0, 0))
d.text((12, px - 14), '10 m  (%.2f m/px)  N^' % mpp, fill=(255, 255, 0))
for g in range(0, px, int(10 / mpp)):
    d.line((g, 0, g, 6), fill=(255, 0, 0)); d.line((0, g, 6, g), fill=(255, 0, 0))
im.save(out, quality=88)
print(name, out, 'mpp', round(mpp, 3), 'sha256', hashlib.sha256(open(out, 'rb').read()).hexdigest(), u)
