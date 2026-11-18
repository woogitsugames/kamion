"""Recompute GetMap URLs for ortho crops (same math as ortho.py) -> url_map.json."""
import sys, json
from pyproj import Transformer
T = Transformer.from_crs(4326, 2180, always_xy=True)
P = {
    'overview_2m.jpg': (53.1020, 23.1725, 2400, 1000, 2.0),
    'rwy_mid_005.jpg': (53.100906, 23.173246, 48, 27, 0.05),
    'rwy_W_01.jpg': (53.1011, 23.1640, 120, 68, 0.1),
    'rwy_E_01.jpg': (53.10075, 23.1825, 120, 68, 0.1),
    'apron_015.jpg': (53.1031, 23.1628, 200, 112, 0.15),
    'hangars_015.jpg': (53.1044, 23.1645, 200, 112, 0.15),
    'white_obj_005.jpg': (53.104278, 23.168924, 60, 34, 0.05),
    'windsock1_005.jpg': (53.104039, 23.171309, 40, 22, 0.05),
    'windsock2_005.jpg': (53.099476, 23.172763, 40, 22, 0.05),
    'windsock3_005.jpg': (53.103058, 23.161619, 40, 22, 0.05),
    'gate_main_005.jpg': (53.105040, 23.164720, 60, 34, 0.05),
    'apron_005.jpg': (53.10305, 23.16300, 40, 22.5, 0.05),
    'twy_W_005.jpg': (53.10220, 23.16295, 40, 22.5, 0.05),
    'rwy_Nedge_01.jpg': (53.10125, 23.1665, 240, 30, 0.1),
}
out = {}
for k, (lat, lon, wm, hm, gsd) in P.items():
    x, y = T.transform(lon, lat)
    w = int(round(wm / gsd)); h = int(round(hm / gsd))
    out[k] = ('https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/HighResolution?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap'
              f'&LAYERS=Raster&STYLES=&CRS=EPSG:2180&BBOX={y - hm / 2:.2f},{x - wm / 2:.2f},{y + hm / 2:.2f},{x + wm / 2:.2f}&WIDTH={w}&HEIGHT={h}&FORMAT=image/jpeg')
json.dump(out, open(sys.argv[1], 'w'), indent=1)
print(len(out))
