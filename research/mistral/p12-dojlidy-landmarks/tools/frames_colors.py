#!/usr/bin/env python3
"""P12: kadry ortofoto WMS PZGiK + próbkowanie kolorów dachów.
Landmarki: data/landmarks.json (definicje) -> pliki JPG w files/ + data/landmark-colors.json
Typologia: frames tymczasowe (/tmp) -> data/typologia-colors.json
Licencja ortofoto: GUGiK, otwarte dane (PZGiK ORTO WMS StandardResolution).
Kolor dachu: ESTIMATED — mediana RGB w dysku wokół centroidu budynku (r = sqrt(area/pi)/2,
max 8 m), mapowanie na nazwę koloru przez paletę referencyjną (najbliższe Dopasowanie RGB).
"""
import json, math, os, sys, urllib.request
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from epsg2180 import tm_forward, tm_inverse
from PIL import Image
import numpy as np

WMS = ("https://mapy.geoportal.gov.pl/wss/service/PZGiK/ORTO/WMS/StandardResolution?"
       "SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&LAYERS=Raster&SRS=EPSG:2180"
       "&BBOX=%s&WIDTH=%d&HEIGHT=%d&FORMAT=image/jpeg&STYLES=")

def get_frame(cx, cy, size_m=400, px=1600, path=None, retries=3):
    """cx,cy w EPSG:2180 (środek); zwraca (bbox, Image) lub None."""
    bb = (cx - size_m/2, cy - size_m/2, cx + size_m/2, cy + size_m/2)
    bbs = ",".join(f"{v:.0f}" for v in bb)
    url = WMS % (bbs, px, px)
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'kamion-research-p12'})
            data = urllib.request.urlopen(req, timeout=60).read()
            im = Image.open(io.BytesIO(data)) if (io := __import__('io')) else None
            if path:
                with open(path, 'wb') as f: f.write(data)
            return bb, im
        except Exception as e:
            print('  retry', i+1, str(e)[:80])
    return None, None

# paleta nazw kolorów dachów (RGB referencyjny)
PALETA = {
 'czerwona (dachówka ceramiczna)': (150, 60, 50),
 'ciemnoczerwona/brązowa': (110, 55, 45),
 'grafitowa/ciemnoszara': (70, 70, 72),
 'antracytowa': (55, 58, 62),
 'czarna': (38, 38, 40),
 'szara': (120, 120, 122),
 'jasnoszara': (170, 170, 170),
 'jasna/biała': (215, 215, 215),
 'srebrno-szara (ocynk)': (145, 152, 158),
 'zielona': (60, 100, 75),
 'niebieska': (70, 100, 130),
 'beżowa/kremowa': (200, 185, 150),
 'żółto-brązowa': (170, 140, 90),
 'rdzawa/pomarańczowa (blacha)': (170, 95, 55),
}
def nazwa_koloru(rgb):
    r, g, b = rgb
    # regula barwy czerwonej/rdzawej (rozbielone przez slonce dachowki/blacha lakierowana)
    if r > g + 25 and r > b + 25: return 'czerwona/rdzawa (dachowka lub blacha lakierowana)'
    if r > g + 10 and r > b + 10: return 'czerwonorudawa (rozbielona dachówka)'
    if g > r + 10 and g > b + 10: return 'zielona'
    best, bd = None, 1e18
    for n, c in PALETA.items():
        if 'czerwona' in n or n == 'zielona': continue
        d = sum((a-b)**2 for a, b in zip(rgb, c))
        if d < bd: bd, best = d, n
    return best

def probka_rgb(im, bbox, lat, lon, area_m2):
    """mediana RGB w dysku wokół centroidu (EPSG:2180 -> piksele kadru)."""
    x, y = tm_forward(lat, lon)
    x0, y0, x1, y1 = bbox
    W, H = im.size
    px = (x - x0) / (x1 - x0) * W
    py = (y1 - y) / (y1 - y0) * H  # obraz y rośnie w dół
    r_m = min(max(math.sqrt(max(area_m2, 20) / math.pi) / 2, 2), 8)
    r_px = r_m / (x1 - x0) * W
    arr = np.array(im)
    yy, xx = np.ogrid[:H, :W]
    mask = (xx - px)**2 + (yy - py)**2 <= r_px**2
    sel = arr[mask]
    if len(sel) < 20: return None
    med = np.median(sel, axis=0)
    return tuple(int(v) for v in med)

def main():
    os.makedirs('files', exist_ok=True)
    L = json.load(open('data/landmarks.json'))
    mwr = json.load(open('data/matched-with-roads.json'))
    byid = {b['osm_id']: b for b in mwr}
    out = []
    for l in L:
        cx, cy = tm_forward(l['lat'], l['lon'])
        fn = 'files/' + l['frame'] + '.jpg'
        bb, im = get_frame(cx, cy, size_m=l.get('frame_m', 400), px=800, path=fn)
        if im is None:
            print('BŁĄD kadru', l['id'], fn); continue
        kol = probka_rgb(im, bb, l['lat'], l['lon'], l.get('area_m2', 500)) if l.get('sample_roof', True) else None
        rec = dict(l)
        rec['roof_rgb'] = kol
        rec['roof_color_name'] = nazwa_koloru(kol) if kol else None
        rec['frame_bbox_2180'] = [round(v, 1) for v in bb]
        rec['frame_file'] = fn
        rec["frame_px"] = 800
        out.append(rec)
        print(l['id'], l['nazwa'][:40], '->', fn, 'kolor:', rec['roof_color_name'])
    json.dump(out, open('data/landmark-colors.json', 'w'), ensure_ascii=False, indent=1)

if __name__ == '__main__':
    main()
