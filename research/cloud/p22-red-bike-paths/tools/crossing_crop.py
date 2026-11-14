#!/usr/bin/env python3
"""M65: wycinki przejazdow z ortofotomapy GUGiK (WMS HighResolution, 5 cm/px), obrocone tak, by os JEZDNI (way z crossings.json)
byla pionowa; przejazd biegnie wtedy poziomo, a jego szerokosc czyta sie z pionowej linijki (kreski co 1 m, 0 = wezel OSM).
Okno 20 x 14 m (w poprzek jezdni x wzdluz), 3,125 cm/px po przeskalowaniu. Uzycie: python3 -I tools/crossing_crop.py <out> node_id ..."""
import json, os, sys, time, urllib.request, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geo import to2180
from transect import WMS, UA, HERE

def main():
    from PIL import Image, ImageDraw
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    cr = {c['node_id']: c for c in json.load(open(os.path.join(HERE, 'crossings.json'), encoding='utf-8'))}
    res = []
    for n, arg in enumerate(sys.argv[2:]):
        c = cr[int(arg)]
        px, py = to2180(c['lat'], c['lon']); px, py = round(px, 1), round(py, 1)
        url = WMS.format(px - 22, py - 22, px + 22, py + 22)
        raw = os.path.join(out, 'c%02d_%d.jpg' % (n, c['node_id']))
        if not os.path.exists(raw):
            rq = urllib.request.Request(url, headers={'User-Agent': UA})
            open(raw, 'wb').write(urllib.request.urlopen(rq, timeout=120).read()); time.sleep(1)
        im = Image.open(raw).convert('RGB').rotate(c['road_bearing_deg'], resample=Image.BICUBIC)
        im = im.crop((440 - 200, 440 - 140, 440 + 200, 440 + 140)).resize((640, 448), Image.LANCZOS)  # 20 x 14 m, 32 px/m
        dr = ImageDraw.Draw(im)
        for m in range(-7, 8):
            y = 224 - m * 32
            dr.line([(314, y), (326 if m % 5 else 338, y)], fill=(255, 255, 0), width=1)
            if m % 5 == 0:
                dr.text((340, y - 5), str(m), fill=(255, 255, 0))
        dr.line([(320, 0), (320, 448)], fill=(255, 255, 0), width=1)
        im.save(os.path.join(out, 'c%02d_%d_ruler.png' % (n, c['node_id'])))
        res.append({'n': n, 'node_id': c['node_id'], 'x2180': px, 'y2180': py, 'road_bearing_deg': c['road_bearing_deg'], 'url': url,
                    'file': os.path.basename(raw), 'sha256': hashlib.sha256(open(raw, 'rb').read()).hexdigest(), 'bytes': os.path.getsize(raw)})
    json.dump(res, open(os.path.join(out, 'crossing_crops.json'), 'w'), indent=1)
    print(len(res), 'wycinkow')

if __name__ == '__main__':
    main()
