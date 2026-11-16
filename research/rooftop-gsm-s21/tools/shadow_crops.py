"""M67-FIX: wycinki ortofoto WMS (0,05 m/px) wokół masztów z LIDAR, przesunięte w stronę cienia (NNW).
Uruchom: uv run --no-project --with pyproj --with pillow python -I tools/shadow_crops.py tools files/
Każdy wycinek: bok 50 m, środek = maszt + 6 m w azymucie 330° (kierunek cienia o ~09:00 UTC).
"""
import sys, os, json, math, subprocess
from pyproj import Transformer
TOOLS, OUTD = sys.argv[1], sys.argv[2]
fwd = Transformer.from_crs('EPSG:4326', 'EPSG:2180', always_xy=True)
inv = Transformer.from_crs('EPSG:2180', 'EPSG:4326', always_xy=True)
ROOFS = {'skorupska17': (53.133953, 23.180958), 'dobra3': (53.138052, 23.180663),
         'zwierzyniecka4': (53.119647, 23.149357), 'kopernika5a': (53.121630, 23.143090)}
PICK = {'skorupska17': 'c12', 'dobra3': 'c11', 'zwierzyniecka4': 'c3', 'kopernika5a': 'c49'}
M = json.load(open(os.path.join(TOOLS, '..', 'masts_xy.json')))
res = {}
for name, cid in PICK.items():
    lat, lon = ROOFS[name]
    x, y = fwd.transform(lon, lat)
    it = [m for m in M[name] if m['id'] == cid][0]
    mx, my = x + it['dx'], y + it['dy']
    a = math.radians(330)
    cx, cy = mx + 6 * math.sin(a), my + 6 * math.cos(a)
    clon, clat = inv.transform(cx, cy)
    mlon, mlat = inv.transform(mx, my)
    out = os.path.join(OUTD, 'shadow_%s.jpg' % name)
    r = subprocess.run([sys.executable, '-I', os.path.join(TOOLS, 'ortho_crop.py'), TOOLS, name, '%.7f' % clat, '%.7f' % clon,
                        '50', out, '0.05'], capture_output=True, text=True)
    print(r.stdout.strip()[:200], r.stderr.strip()[-200:])
    # położenie masztu (LIDAR) w px wycinka: środek 500,500; maszt przesunięty o −6 m w az 330
    res[name] = {'mast_lat': round(mlat, 7), 'mast_lon': round(mlon, 7), 'crop_center': [round(clat, 7), round(clon, 7)],
                 'mast_px_LIDAR': [round(500 - 6 * math.sin(a) / 0.05), round(500 + 6 * math.cos(a) / 0.05)]}
json.dump(res, open(os.path.join(OUTD, '..', 'out', 'shadow_crops.json'), 'w'), indent=1)
print(res)
