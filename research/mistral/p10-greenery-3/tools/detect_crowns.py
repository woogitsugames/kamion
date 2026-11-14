#!/usr/bin/env python3
"""M51 / zad. 3 — odtwarzalna detekcja koron drzew/krzewów na kaflu EPSG:2180
[776971, 595199, 779019, 597247] (Białystok, osiedle przy Al. Tysiąclecia),
na ortofotomapie GUGiK (usługa WMS StandardResolution, warstwa "Raster",
licencja CC BY 4.0).

POPRAWKA M51-FIX (rejestracja): kafle GetMap są odbierane z błędem lustrzanym
północ–południe — wiersz 0 pobranego obrazu to PÓŁNOC kafla, nie południe:
    N = n0 + 1024 - wiersz * 0.25
Stąd w load_full() każdy kafel jest odwracany pionowo (a[::-1]) przed wklejeniem
do mozaiki [y=N, x=E]. Weryfikacja rejestracji (check_flip2.py): centroidy
buildings.geojson pod hipotezą flipa trafiają na jasne dachy (mean V=141.7,
77.8% pikseli V>110), bez flipa — na losowy teren (mean V=120.8, 53.6%).

POPRAWKA M51-FIX (zwarta zieleń): poprzedni filtr r <= 6.5 m wycinał zwarty
drzewostan (las, zadrzewiona skarpa, rzędy drzew). Bloki maski o promieniu
równoważnym > 6.5 m trafiają teraz do OSOBNEJ warstwy compact_greenery.geojson
(poligony, uproszczone Douglas-Peuckerem), więc korony punktowe i zwarta
zieleń nie konkurują o jeden filtr rozmiaru.

POPRAWKA M51-FIX (nie-roślinność): zielone dachy/pojazdy odfiltrowane po
kształcie i jasności (patrz NONVEG_* poniżej) — wydłużone wypełnione bloby
(autobusy: aspekt > 3.0 i wypełnienie > 0.72) oraz jasne prostokąty o gładkiej
teksturze (dachy: wypełnienie > 0.85, std(V) < 3.5, V > 115).

DATA ORTOFOTO: pobierana automatycznie z metadanych WMS GetFeatureInfo usługi
PZGIK/ORTO/WMS/SkorowidzeWgAktualnosci (warstwa SkorowidzeOrtofotomapy2024,
info_format=text/html, rekordy skorDo5cm w osadzonym JS) — NIE z pamięci.
Test 2026-11-13: kafel pokrywają arkusze N-34-107-C-b-1-1/-1-2 i
N-34-107-A-d-3-3/-3-4, wszystkie aktualność 2024-05-27, 0.25 m/px, PL-1992,
zgłoszenie DFT.7201.011.2024.

METODA (krok po kroku):
1. GetMap WMS 1.3.0 (CRS=EPSG:2180, kolejność osi N,E) — 4 kafle 1024x1024 m
   (4096x4096 px), razem 2048x2048 m = cały kafel zadania.
2. Mozaika [y=N, x=E] z odbiciem pionowym każdego kafla (FIX rejestracji).
3. Maska roślinności (korony): ExG = 2g - r - b (rgb znormalizowane) > 0.12
   ORAZ kanał G > 60 (usuwa cienie/przygaszone). Maska "zwartej zieleni":
   ExG > 0.06 (miękki próg — ciemny baldachim lasu/skarpy ma ExG ~0.06-0.12,
   patrz diag_mask.py; w oknie skarpy przy Al. Tysiąclecia 1,5% vs 15,1%
   pokrycia dla progów 0.12/0.06).
4. Oczyszczenie morfologiczne: opening 3x3 px, closing 5x5 px.
5. Segmentacja: scipy.ndimage.label (spójne składowe), kafle rdzeniowe z
   marginesem 32 px (8 m), centroid w rdzeniu kafla = policzony raz.
6. Rozdział na warstwy: korony — bloby maski twardej o
   r = sqrt(A*0.0625/pi) w [0.7, 6.5] m (crowns.geojson); zwarta zieleń —
   bloby maski miękkiej o r > 6.5 m (compact_greenery.geojson).
7. Filtr nie-roślinności (kształt+jasność, obie warstwy): pojazdy i jasne
   prostokątne dachy (progi NONVEG_*).
8. Klasyfikacja iglaste/liściaste (ESTIMATED, heurystyka jasność+tekstura):
   iglaste gdy V < 85 (ciemna zieleń) LUB std(V) < 4.0 (gładka faktura tuji);
   inaczej liściaste.
9. Środek korony = centroid bloba; EPSG:2180 -> WGS84 (tools/tm2180.py,
   walidacja roundtrip < 1e-8 st.). Poligony zwartej zieleni: kontur
   marching-squares (matplotlib) na masce przeskalowanej do 1 m/px,
   uproszczenie Douglas-Peucker (tol 1.5 m).

Użycie: python3 detect_crowns.py [katalog_z_ortofoto] [crowns.geojson] \
           [compact_greenery.geojson]
Kafle PNG pobierane curl-em gdy brak. Wymaga numpy, scipy, Pillow, matplotlib.
"""
import json
import os
import re
import subprocess
import sys
import urllib.request

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tm2180 import inverse

WMS = ('https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/StandardResolution'
       '?service=WMS&version=1.3.0&request=GetMap&layers=Raster&styles='
       '&format=image/png&CRS=EPSG%3A2180&BBOX={bbox}&WIDTH=4096&HEIGHT=4096')
SKOROWIDZE = ('https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/'
              'SkorowidzeWgAktualnosci?service=WMS&version=1.3.0&request=GetFeatureInfo'
              '&layers=SkorowidzeOrtofotomapy2024&query_layers=SkorowidzeOrtofotomapy2024'
              '&CRS=EPSG%3A2180&BBOX={bbox}&WIDTH=200&HEIGHT=200&I=100&J=100'
              '&info_format=text/html')
GSD = 0.25
E0, N0, E1, N1 = 776971, 595199, 779019, 597247
CHUNKS = [('sw.png', 595199, 776971), ('se.png', 595199, 777995),
          ('nw.png', 596223, 776971), ('ne.png', 596223, 777995)]
EXG_TH, EXG_TH_SOFT, G_TH = 0.12, 0.06, 60
R_MIN, R_MAX = 0.7, 6.5
V_DARK, STD_SMOOTH = 85.0, 4.0
MARGIN = 32  # px (8 m)
# filtry nie-roślinności (M51-FIX): pojazdy (wydłużone + wypełnione + GŁADKIE
# i jasne — jednolity dach autobusu; rzędy drzew mają teksturę std(V)>3.5) i
# jasne gładkie prostokąty (zielone dachy); progi zwalidowane wizualnie na
# kandydatach (patrz README, sekcja "nie-roślinność")
NONVEG_ASPECT_MAX, NONVEG_FILL_VEH, NONVEG_STD_VEH, NONVEG_V_VEH = 3.0, 0.72, 3.5, 100.0
NONVEG_FILL_ROOF, NONVEG_STD_ROOF, NONVEG_V_ROOF = 0.85, 3.5, 115.0
POLY_DS, POLY_TOL = 4, 1.5  # downsampling maski do 1 m/px, tolerancja DP [m]


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


def query_orto_dates():
    """Aktualności arkuszy pokrywających kafel — z GetFeatureInfo skorowidzy
    (metadane usługi, nie pamięć). Zwraca {godlo: aktualnosc}."""
    dates = {}
    for _, n0, e0 in CHUNKS:
        x, y = e0 + 512, n0 + 512  # środki ćwiartek pokrywają arkusze 1:5000
        for xx, yy in [(x, y), (e0, n0), (e0 + 1024, n0),
                       (e0, n0 + 1024), (e0 + 1024, n0 + 1024)]:
            bbox = f'{yy - 50:.0f},{xx - 50:.0f},{yy + 50:.0f},{xx + 50:.0f}'
            with urllib.request.urlopen(SKOROWIDZE.format(bbox=bbox), timeout=60) as r:
                html = r.read().decode('utf-8')
            for rec in re.findall(r'skorDo5cm\.push\((\{.*?\})\)', html):
                d = dict(re.findall(r'(\w+):"([^"]*)"', rec))
                if d.get('wielkoscPiksela') == '0.25':
                    dates[d.get('godlo', '?')] = d.get('aktualnosc', '?')
    return dates


def load_full(orto_dir):
    """Pełna mozaika uint8 [y=N, x=E]. FIX M51: wiersz 0 obrazu kafla to
    PÓŁNOC (N = n0 + 1024 - wiersz*0.25), więc kafel jest odwracany pionowo."""
    mos = np.zeros((int((N1 - N0) / GSD), int((E1 - E0) / GSD), 3), dtype=np.uint8)
    for name, n0, e0 in CHUNKS:
        a = np.asarray(Image.open(os.path.join(orto_dir, name)))
        mos[int((n0 - N0) / GSD):int((n0 - N0) / GSD) + 4096,
            int((e0 - E0) / GSD):int((e0 - E0) / GSD) + 4096] = a[::-1]
    return mos


def blob_shape(m):
    """Statystyki kształtu bloba (maska bool w wycinku): wypełnienie prostokąta
    otaczającego i aspekt osi głównych."""
    ys, xs = np.nonzero(m)
    h = np.ptp(ys) + 1
    w = np.ptp(xs) + 1
    fill = m.sum() / (h * w)
    cy, cx = ys.mean(), xs.mean()
    dx, dy = xs - cx, ys - cy
    cxx = (dx * dx).mean()
    cyy = (dy * dy).mean()
    cxy = (dx * dy).mean()
    tr = np.trace(np.array([[cxx, cxy], [cxy, cyy]]))
    det = cxx * cyy - cxy ** 2
    disc = max(tr * tr / 4 - det, 0.0) ** 0.5
    l1, l2 = tr / 2 + disc, tr / 2 - disc
    aspect = (2 * (l1 ** 0.5)) / max(2 * (l2 ** 0.5), 1e-9)
    return fill, aspect


def classify_nonveg(fill, aspect, vm, vs):
    """M51-FIX: nie-roślinność po kształcie i jasności — zielone pojazdy
    (wydłużone, wypełnione, GŁADKIE i jasne: jednolity dach autobusu;
    rzędy drzew mają teksturę std(V) > 3.5) i jasne gładkie prostokątne
    dachy."""
    if (aspect > NONVEG_ASPECT_MAX and fill > NONVEG_FILL_VEH
            and vs < NONVEG_STD_VEH and vm > NONVEG_V_VEH):
        return 'pojazd? (wydłużony, gładki, jasny)'
    if fill > NONVEG_FILL_ROOF and vs < NONVEG_STD_ROOF and vm > NONVEG_V_ROOF:
        return 'jasny prostokąt (dach?)'
    return None


def douglas_peucker(pts, tol):
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    ab = b - a
    n2 = (ab ** 2).sum()
    if n2 == 0:
        d = np.hypot(*(pts - a).T)
    else:
        d = np.abs(np.cross(ab, pts - a)) / n2 ** 0.5
    i = int(np.argmax(d))
    if d[i] <= tol:
        return np.array([a, b])
    return np.vstack([douglas_peucker(pts[:i + 1], tol),
                      douglas_peucker(pts[i:], tol)[1:]])


_POLY_FIG = plt.figure()


def blob_polygon(m, gy0, gx0):
    """Kontur bloba (maska bool w wycinku) -> poligon WGS84 (uproszczony).
    (gy0, gx0) = globalne piksele mozaiki lewego-górnego rogu wycinka m.
    Maska downsamplowana do 1 m/px, kontur marching-squares (matplotlib
    contour, poziom 0.5), DP tol POLY_TOL m. Zwraca tylko pierścień
    zewnętrzny (najdłuższy segment; ewentualne dziury bloba pomijane)."""
    ys, xs = np.nonzero(m)
    y0, x0 = ys.min(), xs.min()
    h, w = np.ptp(ys) + 1, np.ptp(xs) + 1
    pad_h, pad_w = (-h) % POLY_DS, (-w) % POLY_DS
    m2 = np.zeros((h + pad_h, w + pad_w), bool)
    m2[:h, :w] = m[y0:y0 + h, x0:x0 + w]
    m2 = m2.reshape(m2.shape[0] // POLY_DS, POLY_DS,
                    m2.shape[1] // POLY_DS, POLY_DS).any(axis=(1, 3))
    ax = _POLY_FIG.add_axes([0, 0, 1, 1])
    try:
        cs = ax.contour(m2.astype(float), levels=[0.5])
        segs = cs.allsegs[0] if cs.allsegs else []
    finally:
        _POLY_FIG.delaxes(ax)
    if not segs:
        return None
    pts = np.asarray(max(segs, key=len))  # zewnętrzny kontur
    simp = douglas_peucker(pts, POLY_TOL / POLY_DS)
    if len(simp) < 4:
        return None
    # kontur biegnie po połowach komórek siatki 1 m: komórka [r,c] (grid 4 px)
    # pokrywa mozaikowe px [x0+c*4, x0+(c+1)*4); granica komórek c/c+1 ma
    # współrzędną konturu xc=c+0.5 -> px = x0+(xc+0.5)*4
    X_px = gx0 + x0 + (simp[:, 0] + 0.5) * POLY_DS
    Y_px = gy0 + y0 + (simp[:, 1] + 0.5) * POLY_DS
    ring = [tuple(inverse(E0 + x * GSD, N0 + y * GSD)[::-1])
            for x, y in zip(X_px, Y_px)]
    if ring[0] != ring[-1]:
        ring.append(ring[0])
    return ring


def detect_chunk(mos, cy0, cx0):
    """Kafel rdzeniowy [cy0:cy0+4096, cx0:cx0+4096] z marginesem MARGIN.
    Dwie maski: korony = ExG>0.12 (jasne rozłączne korony), zwarta zieleń =
    ExG>0.06 (miękki próg — ciemny baldachim lasu/skarpy nie przechodzi przez
    próg 0.12; patrz diag_mask.py: okno skarpy 1,5% vs 15,1% pokrycia).
    Zwraca (korony, zwarta zieleń, odrzucone-nie-roślinność)."""
    H, W, _ = mos.shape
    y0 = max(0, cy0 - MARGIN)
    y1 = min(H, cy0 + 4096 + MARGIN)
    x0 = max(0, cx0 - MARGIN)
    x1 = min(W, cx0 + 4096 + MARGIN)
    reg = mos[y0:y1, x0:x1].astype(np.float32)
    s = reg.sum(axis=2) + 1e-6
    exg = 2 * reg[..., 1] / s - reg[..., 0] / s - reg[..., 2] / s
    g = reg[..., 1]
    V = reg.mean(axis=2)
    del s, reg

    # --- korony (jasne, rozłączne) ---
    mask = ndimage.binary_closing(
        ndimage.binary_opening((exg > EXG_TH) & (g > G_TH), np.ones((3, 3))),
        np.ones((5, 5)))
    lab, n = ndimage.label(mask)
    del mask
    objs = ndimage.find_objects(lab)
    crowns, dropped = [], []
    for i in range(n):
        sl = objs[i]
        if sl is None:
            continue
        m = lab[sl] == i + 1
        cy, cx = ndimage.center_of_mass(m)
        gy, gx = sl[0].start + cy, sl[1].start + cx
        core_y0, core_x0 = cy0 - y0, cx0 - x0
        if not (core_y0 <= gy < core_y0 + 4096 and core_x0 <= gx < core_x0 + 4096):
            continue
        A = int(m.sum())
        r = (A * GSD ** 2 / np.pi) ** 0.5
        fill, aspect = blob_shape(m)
        px = V[sl][m]
        vm, vs = float(px.mean()), float(px.std())
        e, n_ = E0 + (x0 + gx) * GSD, N0 + (y0 + gy) * GSD
        if not (R_MIN <= r <= R_MAX):
            continue
        nonveg = classify_nonveg(fill, aspect, vm, vs)
        if nonveg:
            dropped.append((e, n_, r, nonveg))
            continue
        typ = 'iglaste' if (vm < V_DARK or vs < STD_SMOOTH) else 'liściaste'
        crowns.append((e, n_, r, typ, vm, vs))
    del lab, objs

    # --- zwarta zieleń (miękka maska, tylko closing — opening rzedzi krawędzie
    # baldachimu; blobs r > 6.5 m same odfiltrują szum) ---
    mask = ndimage.binary_closing((exg > EXG_TH_SOFT) & (g > G_TH), np.ones((5, 5)))
    del exg, g
    lab, n = ndimage.label(mask)
    del mask
    objs = ndimage.find_objects(lab)
    compact = []
    for i in range(n):
        sl = objs[i]
        if sl is None:
            continue
        m = lab[sl] == i + 1
        cy, cx = ndimage.center_of_mass(m)
        gy, gx = sl[0].start + cy, sl[1].start + cx
        core_y0, core_x0 = cy0 - y0, cx0 - x0
        if not (core_y0 <= gy < core_y0 + 4096 and core_x0 <= gx < core_x0 + 4096):
            continue
        A = int(m.sum())
        r = (A * GSD ** 2 / np.pi) ** 0.5
        if r <= R_MAX:
            continue
        fill, aspect = blob_shape(m)
        px = V[sl][m]
        vm, vs = float(px.mean()), float(px.std())
        if classify_nonveg(fill, aspect, vm, vs):
            continue
        ring = blob_polygon(m, y0 + sl[0].start, x0 + sl[1].start)
        if ring:
            e, n_ = E0 + (x0 + gx) * GSD, N0 + (y0 + gy) * GSD
            compact.append((e, n_, r, A * GSD ** 2, ring, vm, vs))
    return crowns, compact, dropped


def main():
    orto_dir = sys.argv[1] if len(sys.argv) > 1 else 'orto'
    out = sys.argv[2] if len(sys.argv) > 2 else 'crowns.geojson'
    out_c = sys.argv[3] if len(sys.argv) > 3 else 'compact_greenery.geojson'
    fetch(orto_dir)
    dates = query_orto_dates()
    print('aktualności arkuszy (GetFeatureInfo):', dates)
    orto_date = sorted(set(dates.values()))
    assert len(orto_date) == 1, f'różne aktualności arkuszy: {dates}'
    orto_date = orto_date[0]
    mos = load_full(orto_dir)
    crowns, compact, dropped = [], [], []
    for name, n0, e0 in CHUNKS:
        c, k, d = detect_chunk(mos, int((n0 - N0) / GSD), int((e0 - E0) / GSD))
        crowns += c
        compact += k
        dropped += d
        print(name, 'korony:', len(crowns), 'zwarta:', len(compact),
              'odrzucone:', len(dropped), flush=True)

    feats = []
    for kk, (e, n_, r, typ, vm, vs) in enumerate(
            sorted(crowns, key=lambda c: (c[1], c[0]))):
        lat, lon = inverse(e, n_)
        feats.append({
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [round(lon, 6), round(lat, 6)]},
            'properties': {'id': f'C{kk + 1:05d}', 'r_m': round(r, 2), 'typ': typ,
                           'v_mean': round(vm, 1), 'v_std': round(vs, 1),
                           'crs_src': 'EPSG:2180', 'orto_data': orto_date,
                           'gsd_m': 0.25},
        })
    gj = {'type': 'FeatureCollection',
          'name': ('korony M51 — kafel EPSG:2180 [776971, 595199, 779019, 597247] '
                   f'(poprawka rejestracji N–S; ortofoto {orto_date} wg GetFeatureInfo)'),
          'crs': 'WGS84 (EPSG:4326)',
          'properties': {
              'metoda': ('ExG>0.12 & G>60; opening 3x3, closing 5x5; kafle 1024 m '
                         'z odbiciem N-S (wiersz0=Pólnoc) i marginesem 8 m; '
                         'r=sqrt(A*GSD^2/pi) in [0.7,6.5] m; '
                         'nie-roslinnosc odrzucona (pojazdy: aspect>3.0 & fill>0.72; '
                         'jasne dachy: fill>0.85 & std(V)<3.5 & V>115); '
                         'iglaste: V<85 or std(V)<4; '
                         f'ortofoto GUGiK {orto_date}, GSD 0.25 m, CC BY 4.0'),
              'orto_arkusze': {k: v for k, v in dates.items()},
              'source_wms': 'https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/StandardResolution',
              'source_wms_metadata': 'https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/SkorowidzeWgAktualnosci',
              'generator': 'research/mistral/p10-greenery-3/tools/detect_crowns.py'}}
    gj['features'] = feats
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(gj, f, ensure_ascii=False)
    igl = sum(1 for c in crowns if c[3] == 'iglaste')
    print(f'korony: {len(crowns)} (iglaste {igl}, liściaste {len(crowns) - igl})')
    rs = np.array([c[2] for c in crowns])
    print('r percentyle [50,75,90]:', np.percentile(rs, [50, 75, 90]).round(2))

    cfeats = []
    for kk, (e, n_, r, area, ring, vm, vs) in enumerate(
            sorted(compact, key=lambda c: (c[1], c[0]))):
        cfeats.append({
            'type': 'Feature',
            'geometry': {'type': 'Polygon', 'coordinates': [ring]},
            'properties': {'id': f'Z{kk + 1:04d}', 'area_m2': round(area),
                           'r_m': round(r, 1), 'v_mean': round(vm, 1),
                           'v_std': round(vs, 1), 'crs_src': 'EPSG:2180',
                           'orto_data': orto_date,
                           'typ': 'zwarta zieleń (maska ExG; las/skarpa/rząd drzew/trawnik — bez rozdziału, ESTIMATED)'},
        })
    cgj = {'type': 'FeatureCollection',
           'name': ('zwarta zieleń M51 (poligony masek r>6.5 m) — kafel '
                    '[776971, 595199, 779019, 597247]'),
           'crs': 'WGS84 (EPSG:4326)',
           'properties': {
               'metoda': ('bloki maski ExG>0.06 & G>60 (miękki próg — baldachim) o promieniu równoważnym '
                          '>6.5 m; kontur marching-squares (maska 1 m/px), '
                          'Douglas-Peucker tol 1.5 m; nie-roslinnosc odrzucona '
                          'jak w crowns.geojson; ortofoto GUGiK ' + orto_date),
               'source_wms': 'https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/StandardResolution',
               'generator': 'research/mistral/p10-greenery-3/tools/detect_crowns.py'}}
    cgj['features'] = cfeats
    with open(out_c, 'w', encoding='utf-8') as f:
        json.dump(cgj, f, ensure_ascii=False)
    print(f'zwarta zieleń: {len(compact)} poligonów; '
          f'nie-roślinność odrzucona: {len(dropped)}')
    with open(os.path.join(os.path.dirname(out) or '.', 'nonveg_dropped.json'),
              'w', encoding='utf-8') as f:
        json.dump([{'lon': round(inverse(e, n_)[1], 6),
                    'lat': round(inverse(e, n_)[0], 6),
                    'r_m': round(r, 2), 'powod': p} for e, n_, r, p in dropped],
                  f, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
