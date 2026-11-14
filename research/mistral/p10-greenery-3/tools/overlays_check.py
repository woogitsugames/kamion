#!/usr/bin/env python3
"""M51-FIX-2 / samokontrola koron — nakładki koron (+ zwarta zieleń + osie
dróg OSM) na ortofoto GUGiK w 3 oknach 300x300 m i % środków koron na zieleni
(ExG > 0.06 w pikselu środka; wymóg > 80 %).

POPRAWKA M51-FIX-2 (przegląd s19 §3.1): poprzednia wersja (a) zapisywała
wycinek mozaiki [y=N] bez odwrócenia — wiersz 0 obrazu = POŁUDNIE (obraz
odwrócony N–S względem WMS), (b) powiększała wycinek x4 (4800 px), a znaczniki
rysowała w skali 4 px/m (układ 1200 px) — trafiały tylko w lewy-górny róg.
Teraz:
  * obraz okna pobierany WPROST z WMS GetMap (WMS 1.3.0, EPSG:2180, oś N,E)
    — standard WMS: wiersz 0 = PÓŁNOC (north-up), kolumna 0 = zachód;
  * jedna skala dla obrazu i znaczników: s = PX / 300 m (px/m), gdzie PX =
    rozmiar okna w pikselach (domyślnie 1200 = natywne 0,25 m; do gita 960);
    kolumna = (E - E_min) * s, wiersz = (N_max - N) * s;
  * dodatkowo cienkie żółte osie dróg z roads.graph.json (OSM/BDOT10k) — kontrola
    rejestracji (osie muszą leżeć na jezdniach) i orientacji (north-up);
  * % trafień liczony na tym samym (natywnym) obrazie, z tą samą konwencją
    wierszy; dla kontroli także % po odbiciu N–S (stara, błędna konwencja).

Okna (deterministycznie):
 W1 — okno przeglądu s17/s19 (skarpa N od bloków przy Al. Tysiąclecia):
      53.1555 N, 23.1525 E;
 W2 — okno z maksymalną liczbą koron (siatka 300 m, kroki co 100 m);
 W3 — okno wyśrodkowane na największym poligonie zwartej zieleni.

Wyjścia: <out>/w1_skarpa.png, w2_max_korony.png, w3_max_zwarta.png +
<out>/overlays_check.json (+ kopia pod --json).
Użycie:
  python3 overlays_check.py --crowns crowns.geojson \
      --compact compact_greenery.geojson --roads roads.graph.json \
      --px 1200 --out overlays [--json overlays_check.json] [--cache dir]
      [--palette 124]   (do gita: --px 960 --palette 124)
Wymaga numpy, Pillow; sieć do mapy.geoportal.gov.pl (ortofoto CC BY 4.0).
"""
import argparse
import io
import json
import os
import sys
import time
import urllib.request

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tm2180 import forward, inverse  # noqa: E402

WMS = ('https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/StandardResolution'
       '?service=WMS&version=1.3.0&request=GetMap&layers=Raster&styles='
       '&format=image/png&CRS=EPSG%3A2180&BBOX={n0:.2f},{e0:.2f},{n1:.2f},{e1:.2f}'
       '&WIDTH={w}&HEIGHT={h}')
WIN = 300.0  # m
NATIVE_PX = 1200  # 300 m / 0,25 m
EXG_GREEN = 0.06
E0, N0, E1, N1 = 776971, 595199, 779019, 597247  # kafel zadania
UA = 'kamion-research-fetch/1.0 (generic research client)'
CAR_HW = {'motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'unclassified',
          'residential', 'living_street', 'service', 'motorway_link', 'trunk_link',
          'primary_link', 'secondary_link', 'tertiary_link', 'busway'}


def exg_of(img):
    a = img.astype(np.float32)
    s = a.sum(axis=2) + 1e-6
    return 2 * a[..., 1] / s - a[..., 0] / s - a[..., 2] / s


def fetch_window(cx, cy, cache):
    """Okno 300x300 m wokół (cx, cy) [EPSG:2180] w natywnej rozdzielczości
    0,25 m (1200 px). Zwraca uint8 RGB, wiersz 0 = PÓŁNOC."""
    half = WIN / 2
    key = os.path.join(cache, f'wms_{cx:.1f}_{cy:.1f}_{NATIVE_PX}.png') if cache else None
    if key and os.path.exists(key):
        return np.asarray(Image.open(key).convert('RGB'))
    url = WMS.format(n0=cy - half, e0=cx - half, n1=cy + half, e1=cx + half,
                     w=NATIVE_PX, h=NATIVE_PX)
    for i in range(5):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=180) as r:
                b = r.read()
            im = Image.open(io.BytesIO(b)).convert('RGB')
            break
        except Exception as e:  # noqa: BLE001 — sieć: ponów z backoffem
            print('WMS błąd', e, '— ponawiam', flush=True)
            time.sleep(10 * (i + 1))
    else:
        raise RuntimeError('WMS GUGiK nieosiągalny')
    if key:
        os.makedirs(cache, exist_ok=True)
        im.save(key)
    return np.asarray(im)


MARK_COLORS = [(255, 40, 40), (0, 220, 220), (255, 230, 0), (255, 255, 255)]


def to_palette(im, n):
    """Paleta: n kolorów dobranych do obrazu + czyste kolory znaczników
    (sama kwantyzacja gubi nieliczne czerwone piksele okręgów)."""
    base = im.quantize(colors=n, method=Image.Quantize.MEDIANCUT)
    pal = base.getpalette()[:3 * n]
    for c in MARK_COLORS:
        pal += list(c)
    pal += [0] * (768 - len(pal))
    pimg = Image.new('P', (1, 1))
    pimg.putpalette(pal)
    return im.quantize(palette=pimg, dither=Image.Dither.NONE)


def load_roads(path):
    if not path or not os.path.exists(path):
        return []
    g = json.load(open(path, encoding='utf-8'))
    out = []
    for e in g['edges']:
        hw = (e.get('attrs') or {}).get('highway')
        hw = hw.get('v') if isinstance(hw, dict) else hw
        if hw in CAR_HW:
            out.append([(p[0], p[1]) for p in e['geometry']])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--crowns', default='crowns.geojson')
    ap.add_argument('--compact', default='compact_greenery.geojson')
    ap.add_argument('--roads', default='')
    ap.add_argument('--px', type=int, default=NATIVE_PX)
    ap.add_argument('--out', default='overlays')
    ap.add_argument('--json', default='')
    ap.add_argument('--cache', default='')
    ap.add_argument('--palette', type=int, default=0,
                    help='>0: zapis PNG z paletą (N kolorów ortofoto + kolory znaczników) — mały plik do gita')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    g = json.load(open(a.crowns, encoding='utf-8'))
    P = np.array([forward(f['geometry']['coordinates'][1],
                          f['geometry']['coordinates'][0]) for f in g['features']])
    R = np.array([f['properties']['r_m'] for f in g['features']])
    c = json.load(open(a.compact, encoding='utf-8'))
    CP = [[forward(lat, lon) for lon, lat in f['geometry']['coordinates'][0]]
          for f in c['features']]
    CA = np.array([f['properties']['area_m2'] for f in c['features']])
    roads = load_roads(a.roads)

    half = WIN / 2
    best = None
    for ex in np.arange(E0 + half, E1 - half, 100):
        for ny in np.arange(N0 + half, N1 - half, 100):
            k = int(((P[:, 0] >= ex - half) & (P[:, 0] < ex + half) &
                     (P[:, 1] >= ny - half) & (P[:, 1] < ny + half)).sum())
            if best is None or k > best[0]:
                best = (k, float(ex), float(ny))
    i = int(np.argmax(CA))
    centers = {
        'w1_skarpa': forward(53.1555, 23.1525),
        'w2_max_korony': (best[1], best[2]),
        'w3_max_zwarta': (float(np.mean([p[0] for p in CP[i]])),
                          float(np.mean([p[1] for p in CP[i]]))),
    }

    s = a.px / WIN  # px/m — JEDNA skala dla obrazu i znaczników

    def to_px(e, n, cx, cy):
        return (e - (cx - half)) * s, ((cy + half) - n) * s  # wiersz 0 = północ

    out = []
    for name, (cx, cy) in centers.items():
        nat = fetch_window(cx, cy, a.cache)  # 1200x1200, north-up
        assert nat.shape[:2] == (NATIVE_PX, NATIVE_PX), nat.shape
        im = Image.fromarray(nat)
        if a.px != NATIVE_PX:
            im = im.resize((a.px, a.px), Image.LANCZOS)
        dr = ImageDraw.Draw(im, 'RGBA')
        lw = max(1, round(a.px / 600))
        # osie dróg OSM — żółte (kontrola rejestracji/orientacji)
        for pts in roads:
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            if max(xs) < cx - half or min(xs) > cx + half or \
                    max(ys) < cy - half or min(ys) > cy + half:
                continue
            dr.line([to_px(e, n, cx, cy) for e, n in pts], fill=(255, 230, 0, 170), width=lw)
        # zwarta zieleń — cyjan
        n_zwarta = 0
        for pts in CP:
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            if (min(xs) < cx + half and max(xs) > cx - half and
                    min(ys) < cy + half and max(ys) > cy - half):
                n_zwarta += 1
                dr.polygon([to_px(e, n, cx, cy) for e, n in pts],
                           outline=(0, 220, 220, 255), width=lw)
        # korony — czerwone okręgi (promień r_m w tej samej skali) + środek
        inwin = ((P[:, 0] >= cx - half) & (P[:, 0] < cx + half) &
                 (P[:, 1] >= cy - half) & (P[:, 1] < cy + half))
        xs, ys, rs = P[inwin][:, 0], P[inwin][:, 1], R[inwin]
        for x, y, r in zip(xs, ys, rs):
            u, v = to_px(x, y, cx, cy)
            rr = max(r * s, 2)
            dr.ellipse([u - rr, v - rr, u + rr, v + rr], outline=(255, 40, 40, 255), width=lw)
            dr.ellipse([u - 1.5, v - 1.5, u + 1.5, v + 1.5], fill=(255, 40, 40, 255))
        # strzałka N (lewy-górny róg) + skala 50 m (lewy-dolny róg)
        m = 0.03 * a.px
        dr.polygon([(m + 10, m), (m + 2, m + 22), (m + 18, m + 22)], fill=(255, 255, 255, 230))
        dr.text((m + 6, m + 24), 'N', fill=(255, 255, 255, 255))
        dr.line([(m, a.px - m), (m + 50 * s, a.px - m)], fill=(255, 255, 255, 255), width=3)
        dr.text((m, a.px - m - 14), '50 m', fill=(255, 255, 255, 255))
        if a.palette:
            im = to_palette(im, a.palette)
        im.save(os.path.join(a.out, f'{name}.png'), optimize=True)

        # % środków na zieleni — natywny obraz (0,25 m), ta sama konwencja wierszy
        exg = exg_of(nat)
        jj = ((xs - (cx - half)) / 0.25).astype(int)
        ii = (((cy + half) - ys) / 0.25).astype(int)
        ok = (ii >= 0) & (ii < NATIVE_PX) & (jj >= 0) & (jj < NATIVE_PX)
        vals = exg[ii[ok], jj[ok]]
        pct = 100 * float((vals > EXG_GREEN).mean()) if len(vals) else float('nan')
        # kontrola: te same środki w obrazie odwróconym N–S (stara konwencja)
        vals_f = exg[(NATIVE_PX - 1 - ii[ok]), jj[ok]]
        pct_f = 100 * float((vals_f > EXG_GREEN).mean()) if len(vals) else float('nan')
        lat, lon = inverse(cx, cy)
        rec = {'okno': name, 'srodek_wgs84': [round(lon, 6), round(lat, 6)],
               'srodek_epsg2180_EN': [round(cx, 1), round(cy, 1)],
               'png_px': a.px, 'skala_px_na_m': round(s, 4),
               'korony_w_oknie': int(inwin.sum()),
               'pct_srodkow_na_zieleni_ExG>0.06': round(pct, 1),
               'kontrola_pct_po_odbiciu_N-S': round(pct_f, 1),
               'pokrycie_zieleni_okna_ExG>0.06_pct': round(100 * float((exg > EXG_GREEN).mean()), 1),
               'zwarta_zielen_poligony_przecinajace_okno': n_zwarta}
        out.append(rec)
        print(rec, flush=True)
    total = sum(r['korony_w_oknie'] for r in out)
    wavg = sum(r['pct_srodkow_na_zieleni_ExG>0.06'] * r['korony_w_oknie'] for r in out) / total
    summary = {'okna': out, 'koron_w_3_oknach': total,
               'wazony_pct_srodkow_na_zieleni': round(wavg, 1),
               'zrodlo_obrazu': 'GUGiK WMS PZGIK/ORTO StandardResolution (CC BY 4.0), north-up',
               'generator': 'research/mistral/p10-greenery-3/tools/overlays_check.py (M51-FIX-2)'}
    for path in [os.path.join(a.out, 'overlays_check.json'), a.json]:
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=1)
    print(f'łącznie koron w 3 oknach: {total}; ważony % środków na zieleni: {wavg:.1f}')


if __name__ == '__main__':
    main()
