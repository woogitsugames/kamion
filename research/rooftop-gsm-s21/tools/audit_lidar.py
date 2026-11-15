"""Audyt r2: niezależne przeliczenie wysokości dla wylosowanych pomiarów LIDAR inną metodą.
h_alt = max Z w walcu r = 1,5 m − MEDIANA Z punktów klas 6/12 w pierścieniu 2–8 m, w paśmie (top−12 m, top−0,5 m).
(r1 audytu: mediana klasy 6 z pasma wokół 25. percentyla — błędna dla Hallera 19: klasa 6 zawiera ściany; poprawione.)
Uruchom: uv run --no-project --with "laspy[lazrs]" --with numpy --with pyproj python -I tools/audit_lidar.py <laz_dir> skorupska17:c29 hallera19:osm ...
"""
import sys, os, glob, json
import numpy as np, laspy
from pyproj import Transformer
T = Transformer.from_crs('EPSG:4326', 'EPSG:2180', always_xy=True)
HERE = os.path.dirname(os.path.abspath(__file__))
ROOFS = {'skorupska17': ('N-34-107-C-b-1-4-4-2', 53.133953, 23.180958), 'dobra3': ('N-34-107-C-b-1-4-2-4', 53.138052, 23.180663),
         'zwierzyniecka4': ('N-34-107-C-b-3-1-2-4', 53.119647, 23.149357), 'hallera19': ('N-34-107-C-b-1-1-3-1', 53.153529, 23.125354),
         'kopernika5a': ('N-34-107-C-b-3-1-2-1', 53.121630, 23.143090), 'wiezowiec_m57': ('N-34-107-C-b-1-2-3-2', 53.153231, 23.168022)}
M = json.load(open(os.path.join(HERE, '..', 'masts_xy.json')))
LM = json.load(open(os.path.join(HERE, '..', 'out', 'lidar_masts.json')))
for arg in sys.argv[2:]:
    rk, cid = arg.split(':')
    g, lat, lon = ROOFS[rk]
    las = laspy.read(glob.glob(os.path.join(sys.argv[1], '*%s.laz' % g))[0])
    cx, cy = T.transform(lon, lat)
    it = [m for m in M[rk] if m['id'] == cid][0]
    mx, my = cx + it['dx'], cy + it['dy']
    x, y, z, c = np.asarray(las.x), np.asarray(las.y), np.asarray(las.z), np.asarray(las.classification)
    r = np.hypot(x - mx, y - my)
    top = z[r < 1.5].max()
    # klasy 6 (budynek) i 12 (pokrycie szeregów) — w arkuszach 2025 część dachu ma klasę 12, a klasa 6 obejmuje też ściany;
    # dlatego tylko punkty < 12 m pod szczytem urządzenia (odcina ściany i grunt)
    ann = (r > 2) & (r < 8) & np.isin(c, [6, 12]) & (z < top - 0.5) & (z > top - 12)
    base = np.median(z[ann])
    ref = [u for u in LM[rk]['urzadzenia'] if u['id'] == cid][0]['h']
    print(arg, 'h_alt=%.2f' % (top - base), 'h_manifest=%.2f' % ref, 'diff=%.2f' % (top - base - ref), 'PASS' if abs(top - base - ref) <= 0.3 else 'CHECK')
