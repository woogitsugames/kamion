#!/usr/bin/env python3
"""M51 / zad. 3 — odtwarzalna detekcja koron drzew/krzewów na kaflu EPSG:2180
[776971, 595199, 779019, 597247] (Białystok, osiedle przy Al. Tysiąclecia),
na ortofotomapie GUGiK 2024-05-27, GSD 0.25 m (usługa WMS StandardResolution,
warstwa "Raster", licencja CC BY 4.0).

METODA (krok po kroku):
1. GetMap WMS 1.3.0 (CRS=EPSG:2180, kolejność osi N,E) — 4 kafle 1024x1024 m
   (4096x4096 px), razem 2048x2048 m = cały kafel zadania.
2. Przetwarzanie kafelami z marginesem 32 px (8 m) wokół kafla, tak aby korona
   leżąca na granicy kafli była policzona dokładnie raz (centroid należy do
   dokładnie jednego rdzenia kafla).
3. Maska roślinności: ExG = 2g - r - b (rgb znormalizowane) > 0.12
   ORAZ kanał G > 60 (usuwa cienie/przygaszone).
4. Oczyszczenie morfologiczne: opening 3x3 px, closing 5x5 px.
5. Segmentacja: scipy.ndimage.label (spójne składowe).
6. Filtr rozmiaru: promień równoważny r = sqrt(A * 0.0625 / pi) w [0.7, 6.5] m
   (A = liczba pikseli; 0.0625 m2/px przy GSD 0.25). Mniejsze = szum/trawnik
   przycięty, większe = trawniki/lasy (poza zakresem „korony").
7. Klasyfikacja iglaste/liściaste (ESTIMATED, heurystyka jasność+tekstura):
   iglaste gdy średnia jasność V=(R+G+B)/3 < 85 (ciemna zieleń: świerk, ciemna
   tuja) LUB odchylenie std(V) < 4.0 (gładka faktura: żywopłoty z tuji);
   w przeciwnym razie liściaste (jasne, rozczłonkowane korony z prześwitami).
   Bias: jasne odmiany tuji mogą być liczone jako liściaste — patrz README.
8. Środek korony = centroid bloba; EPSG:2180 -> WGS84 (tools/tm2180.py,
   walidacja roundtrip < 1e-8 st.). Wyjście: crowns.geojson (WGS84, 6 miejsc).

Użycie: python3 detect_crowns.py [katalog_z_ortofoto] [crowns.geojson]
Kafle PNG pobierane curl-em gdy brak. Wymaga numpy, scipy, Pillow.
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tm2180 import inverse

WMS = ('https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/StandardResolution'
       '?service=WMS&version=1.3.0&request=GetMap&layers=Raster&styles='
       '&format=image/png&CRS=EPSG%3A2180&BBOX={bbox}&WIDTH=4096&HEIGHT=4096')
GSD = 0.25
E0, N0, E1, N1 = 776971, 595199, 779019, 597247
CHUNKS = [('sw.png', 595199, 776971), ('se.png', 595199, 777995),
          ('nw.png', 596223, 776971), ('ne.png', 596223, 777995)]
EXG_TH, G_TH = 0.12, 60
R_MIN, R_MAX = 0.7, 6.5
V_DARK, STD_SMOOTH = 85.0, 4.0
MARGIN = 32  # px (8 m)


def fetch(orto_dir):
    os.makedirs(orto_dir, exist_ok=True)
    for name, n0, e0 in CHUNKS:
        path = os.path.join(orto_dir, name)
        if os.path.exists(path) and os.path.getsize(path) > 1e6:
            continue
        bbox = f'{n0},{e0},{n0 + 1024},{e0 + 1024}'  # WMS 1.3.0: N,E
        subprocess.run(['curl', '-sS', '-m', '220', WMS.format(bbox=bbox),
                       '-o', path], check=True)
        assert os.path.getsize(path) > 1e6, f'pusty kafel {name}'


def load_full(orto_dir):
    """Pełna mozaika uint8 [y=N, x=E] — 200 MB; indeks y=0 <-> N0."""
    mos = np.zeros((int((N1 - N0) / GSD), int((E1 - E0) / GSD), 3), dtype=np.uint8)
    for name, n0, e0 in CHUNKS:
        a = np.asarray(Image.open(os.path.join(orto_dir, name)))
        mos[int((n0 - N0) / GSD):int((n0 - N0) / GSD) + 4096,
            int((e0 - E0) / GSD):int((e0 - E0) / GSD) + 4096] = a
    return mos


def detect_chunk(mos, cy0, cx0):
    """Kafel rdzenia [cy0:cy0+4096, cx0:cx0+4096] z marginesem MARGIN.
    Zwraca korony (E, N, r, typ) z centroidem w rdzeniu."""
    H, W, _ = mos.shape
    y0 = max(0, cy0 - MARGIN)
    y1 = min(H, cy0 + 4096 + MARGIN)
    x0 = max(0, cx0 - MARGIN)
    x1 = min(W, cx0 + 4096 + MARGIN)
    reg = mos[y0:y1, x0:x1].astype(np.float32)
    s = reg.sum(axis=2) + 1e-6
    exg = 2 * reg[..., 1] / s - reg[..., 0] / s - reg[..., 2] / s
    mask = (exg > EXG_TH) & (reg[..., 1] > G_TH)
    del exg, s, reg
    mask = ndimage.binary_opening(mask, np.ones((3, 3)))
    mask = ndimage.binary_closing(mask, np.ones((5, 5)))
    lab, n = ndimage.label(mask)
    del mask
    V = mos[y0:y1, x0:x1].astype(np.float32).mean(axis=2)
    objs = ndimage.find_objects(lab)
    out = []
    for i in range(n):
        sl = objs[i]
        # blob w całości w oknie? liczymy tylko te, których centroid w rdzeniu
        cy, cx = ndimage.center_of_mass(lab[sl] == i + 1)
        gy, gx = sl[0].start + cy, sl[1].start + cx
        # rdzeń w współrzędnych okna
        core_y0, core_x0 = cy0 - y0, cx0 - x0
        if not (core_y0 <= gy < core_y0 + 4096 and core_x0 <= gx < core_x0 + 4096):
            continue
        A = int((lab[sl] == i + 1).sum())
        r = (A * GSD ** 2 / np.pi) ** 0.5
        if not (R_MIN <= r <= R_MAX):
            continue
        m = lab[sl] == i + 1
        px = V[sl][m]
        vm, vs = float(px.mean()), float(px.std())
        typ = 'iglaste' if (vm < V_DARK or vs < STD_SMOOTH) else 'liściaste'
        out.append((E0 + (x0 + gx) * GSD, N0 + (y0 + gy) * GSD, r, typ, vm, vs))
    return out


def main():
    orto_dir = sys.argv[1] if len(sys.argv) > 1 else 'orto'
    out = sys.argv[2] if len(sys.argv) > 2 else 'crowns.geojson'
    fetch(orto_dir)
    mos = load_full(orto_dir)
    crowns = []
    for name, n0, e0 in CHUNKS:
        crowns += detect_chunk(mos, int((n0 - N0) / GSD), int((e0 - E0) / GSD))
        print(name, 'łącznie:', len(crowns), flush=True)
    feats = []
    for k, (e, n, r, typ, vm, vs) in enumerate(sorted(crowns, key=lambda c: (c[1], c[0]))):
        lat, lon = inverse(e, n)
        feats.append({
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [round(lon, 6), round(lat, 6)]},
            'properties': {'id': f'C{k + 1:05d}', 'r_m': round(r, 2), 'typ': typ,
                           'v_mean': round(vm, 1), 'v_std': round(vs, 1),
                           'crs_src': 'EPSG:2180', 'orto_data': '2024-05-27',
                           'gsd_m': 0.25},
        })
    gj = {'type': 'FeatureCollection',
          'name': f'korony M51 — kafel EPSG:2180 [776971, 595199, 779019, 597247]',
          'crs': 'WGS84 (EPSG:4326)',
          'properties': {
              'metoda': ('ExG>0.12 & G>60; opening 3x3, closing 5x5; '
                         'r=sqrt(A*GSD^2/pi) in [0.7,6.5] m; kafle 1024 m z marginesem 8 m; '
                         'iglaste: V<85 or std(V)<4; ortofoto GUGiK 2024-05-27, GSD 0.25 m, CC BY 4.0'),
              'source_wms': 'https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/StandardResolution',
              'generator': 'research/mistral/p10-greenery-3/tools/detect_crowns.py'}}
    gj['features'] = feats
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(gj, f, ensure_ascii=False)
    igl = sum(1 for c in crowns if c[3] == 'iglaste')
    print(f'korony: {len(crowns)} (iglaste {igl}, liściaste {len(crowns) - igl})')
    rs = np.array([c[2] for c in crowns])
    print('r percentyle [50,75,90]:', np.percentile(rs, [50, 75, 90]).round(2))


if __name__ == '__main__':
    main()
