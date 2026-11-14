#!/usr/bin/env python3
"""M65: przekroje poprzeczne z ortofotomapy GUGiK (WMS HighResolution, 5 cm/px).
Dla punktu w polowie odcinka DDR (w kaflu) pobiera wycinek 44x44 m (880 px), obraca tak, by os DDR byla pionowa
(kierunek biegu wezlow OSM = gora obrazu), wycina pas 30 m (w poprzek) x 16 m i nanosi linijke co 1 m (0 = os OSM DDR,
dodatnie = prawa strona wzgledem kierunku wezlow). Wynik: <out>/tNN_<way>.jpg (surowy) + <out>/tNN_<way>_ruler.png.
Uzycie: python3 -I tools/transect.py <katalog_wyjsciowy> [way_id[:ulamek] ...]"""
import json, math, os, sys, time, urllib.request, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geo import to2180, from2180
from inventory import TILES
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = 'kamion-research/1.0 (open-data reference collection)'
WMS = ('https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/HighResolution?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap'
       '&LAYERS=Raster&STYLES=&SRS=EPSG:2180&BBOX={:.1f},{:.1f},{:.1f},{:.1f}&WIDTH=880&HEIGHT=880&FORMAT=image/jpeg')

def point_on_way(xy, tile, frac):
    pts = []
    for i in range(len(xy) - 1):
        a, b = xy[i], xy[i + 1]
        n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1])))
        for j in range(n):
            f = j / n
            p = (a[0] + f * (b[0] - a[0]), a[1] + f * (b[1] - a[1]))
            if tile[0] <= p[0] <= tile[2] and tile[1] <= p[1] <= tile[3]:
                pts.append((p, math.degrees(math.atan2(b[0] - a[0], b[1] - a[1])) % 360))
    return pts[min(len(pts) - 1, int(len(pts) * frac))]

def main():
    from PIL import Image, ImageDraw
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    d = json.load(open(os.path.join(HERE, 'overpass-result.json'), encoding='utf-8'))
    inv = {r['way_id']: r for r in json.load(open(os.path.join(HERE, 'inventory.json'), encoding='utf-8'))['ways']}
    ways = {e['id']: e for e in d['elements'] if e['type'] == 'way'}
    res = []
    for n, arg in enumerate(sys.argv[2:]):
        wid, _, fr = arg.partition(':'); wid = int(wid); fr = float(fr or 0.5)
        xy = [to2180(g['lat'], g['lon']) for g in ways[wid]['geometry']]
        (px, py), brg = point_on_way(xy, TILES[inv[wid]['region']], fr)
        px, py = round(px, 1), round(py, 1)
        url = WMS.format(px - 22, py - 22, px + 22, py + 22)
        raw = os.path.join(out, 't%02d_%d.jpg' % (n, wid))
        if not os.path.exists(raw):
            rq = urllib.request.Request(url, headers={'User-Agent': UA})
            open(raw, 'wb').write(urllib.request.urlopen(rq, timeout=120).read()); time.sleep(1)
        im = Image.open(raw).convert('RGB').rotate(brg, resample=Image.BICUBIC)  # obrot CCW o azymut -> kierunek biegu do gory
        cx = cy = 440
        im = im.crop((cx - 300, cy - 160, cx + 300, cy + 160)).resize((960, 512), Image.LANCZOS)  # 30 x 16 m, 3,125 cm/px
        dr = ImageDraw.Draw(im)
        for m in range(-15, 16):
            x = 480 + m * 32
            dr.line([(x, 250), (x, 262 if m % 5 else 274)], fill=(255, 255, 0), width=1)
            if m % 5 == 0:
                dr.text((x + 2, 276), str(m), fill=(255, 255, 0))
        dr.line([(0, 256), (960, 256)], fill=(255, 255, 0), width=1)
        im.save(os.path.join(out, 't%02d_%d_ruler.png' % (n, wid)))
        lat, lon = from2180(px, py)
        res.append({'n': n, 'way_id': wid, 'frac': fr, 'x2180': px, 'y2180': py, 'lat': round(lat, 6), 'lon': round(lon, 6),
                    'way_bearing_deg': round(brg, 1), 'url': url, 'file': os.path.basename(raw),
                    'sha256': hashlib.sha256(open(raw, 'rb').read()).hexdigest(), 'bytes': os.path.getsize(raw)})
    json.dump(res, open(os.path.join(out, 'transects.json'), 'w'), indent=1)
    print(len(res), 'przekrojow')

if __name__ == '__main__':
    main()
