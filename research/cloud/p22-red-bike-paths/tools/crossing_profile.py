#!/usr/bin/env python3
"""M65: profil jasnosci wzdluz osi jezdni przez przejazd (kontrola odczytow szerokosci P-11).
Dla wycinka z tools/crossing_crop.py (obrot: os jezdni pionowo) liczy dla kazdego wiersza pikseli (5 cm) 85. percentyl jasnosci
w pasie +/-1,5 m wokol osi i wypisuje pasma 'biale' (prog wzgledny) jako [poczatek, koniec] w metrach od wezla (dodatnie = w gore obrazu).
Rzad kwadratow P-11 = pasmo 0,3-0,7 m; zebra = pasmo >= 2 m. Uzycie: python3 -I tools/crossing_profile.py <katalog z c*.jpg> [dx_m]"""
import json, os, sys
from PIL import Image

def main():
    d = sys.argv[1]; dx = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
    for c in json.load(open(os.path.join(d, 'crossing_crops.json'))):
        raw = os.path.join(d, 'c%02d_%d.jpg' % (c['n'], c['node_id']))
        im = Image.open(raw).convert('L').rotate(c['road_bearing_deg'], resample=Image.BICUBIC)
        x0 = 440 + int(dx * 20)
        prof = []
        for y in range(440 - 160, 440 + 160):
            row = sorted(im.getpixel((x, y)) for x in range(x0 - 30, x0 + 30))
            prof.append(row[int(len(row) * 0.85)])
        base = sorted(prof)[len(prof) // 4]; top = max(prof); thr = base + 0.5 * (top - base)
        bands = []; start = None
        for i, v in enumerate(prof + [0]):
            if v >= thr and start is None: start = i
            if v < thr and start is not None:
                bands.append((round((160 - start) * 0.05, 2), round((160 - i) * 0.05, 2))); start = None
        print(c['n'], c['node_id'], 'bazowa', base, 'max', top, [(a, b, round(a - b, 2)) for a, b in bands if a - b >= 0.2])

if __name__ == '__main__':
    main()
