#!/usr/bin/env python3
"""M51-FIX / samokontrola koron — nałóż korony + zwartą zieleń na ortofoto
w 3 oknach 300x300 m (PNG do ZIP) i policz % środków koron na zieleni
(ExG > 0.06 w pikselu środka; wymóg > 80%).

Okna (deterministycznie):
 W1 — okno przeglądu s17 (zadrzewiona skarpa N od bloków przy Al. Tysiąclecia):
      53.1555 N, 23.1525 E;
 W2 — okno z maksymalną liczbą koron (siatka 300 m, kroki co 100 m);
 W3 — okno wyśrodkowane na największym poligonie zwartej zieleni.

Wyjścia: overlays/w1.png..w3.png (1200 px, RGB) + overlays_check.json.
Użycie: python3 overlays_check.py [orto] [crowns.geojson] [compact_greenery.geojson]"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tm2180 import forward, inverse
import detect_crowns as dc

WIN = 300.0  # m
ZOOM = 4     # px/m -> 1200 px na 300 m
EXG_GREEN = 0.06


def exg_of(mos):
    a = mos.astype(np.float32)
    s = a.sum(axis=2) + 1e-6
    return 2 * a[..., 1] / s - a[..., 0] / s - a[..., 2] / s


def main():
    orto_dir = sys.argv[1] if len(sys.argv) > 1 else 'orto'
    crowns_f = sys.argv[2] if len(sys.argv) > 2 else 'crowns.geojson'
    compact_f = sys.argv[3] if len(sys.argv) > 3 else 'compact_greenery.geojson'
    os.makedirs('overlays', exist_ok=True)
    mos = dc.load_full(orto_dir)
    g = json.load(open(crowns_f))
    P = np.array([forward(f['geometry']['coordinates'][1],
                          f['geometry']['coordinates'][0]) for f in g['features']])
    R = np.array([f['properties']['r_m'] for f in g['features']])
    c = json.load(open(compact_f))
    CP = []
    CA = []
    for f in c['features']:
        ring = f['geometry']['coordinates'][0]
        pts = [forward(lat, lon) for lon, lat in ring]
        CP.append(pts)
        CA.append(f['properties']['area_m2'])
    CAa = np.array(CA)  # CP zostaje lista (nierówne długości pierścieni)

    # W2: okno z max koronami — siatka 300 m co 100 m w obrębie kafla
    half = WIN / 2
    best = None
    for ex in np.arange(dc.E0 + half, dc.E1 - half, 100):
        for ny in np.arange(dc.N0 + half, dc.N1 - half, 100):
            k = ((P[:, 0] >= ex - half) & (P[:, 0] < ex + half) &
                 (P[:, 1] >= ny - half) & (P[:, 1] < ny + half)).sum()
            if best is None or k > best[0]:
                best = (k, ex, ny)
    w2 = (best[1], best[2])
    # W3: środek największego poligonu zwartej zieleni
    i = int(np.argmax(CAa))
    w3 = (float(np.mean([p[0] for p in CP[i]])),
          float(np.mean([p[1] for p in CP[i]])))
    # W1: okno przeglądu
    w1 = forward(53.1555, 23.1525)
    centers = {'w1_skarpa': w1, 'w2_max_korony': w2, 'w3_max_zwarta': w3}

    out = []
    for name, (cx, cy) in centers.items():
        px0 = (cx - half - dc.E0) / dc.GSD
        px1 = (cx + half - dc.E0) / dc.GSD
        py0 = (cy - half - dc.N0) / dc.GSD
        py1 = (cy + half - dc.N0) / dc.GSD
        crop = mos[int(py0):int(py1), int(px0):int(px1)]
        crop = np.repeat(np.repeat(crop, ZOOM, axis=0), ZOOM, axis=1)
        im = Image.fromarray(crop)
        dr = ImageDraw.Draw(im, 'RGBA')
        # zwarta zieleń — cyjan (poligony przecinające okno)
        n_zwarta = 0
        for pts in CP:
            pxs = [p[0] for p in pts]
            pys_ = [p[1] for p in pts]
            if (min(pxs) < cx + half and max(pxs) > cx - half and
                    min(pys_) < cy + half and max(pys_) > cy - half):
                n_zwarta += 1
                poly = [(((e - (cx - half)) * ZOOM), ((n_ - (cy - half)) * ZOOM))
                        for e, n_ in pts]
                dr.polygon(poly, outline=(0, 220, 220, 255), width=3)
        # korony — czerwone okręgi + środek
        inwin = ((P[:, 0] >= cx - half) & (P[:, 0] < cx + half) &
                 (P[:, 1] >= cy - half) & (P[:, 1] < cy + half))
        xs = P[inwin][:, 0]
        ys = P[inwin][:, 1]
        rs = R[inwin]
        for x, y, r in zip(xs, ys, rs):
            u, v = (x - (cx - half)) * ZOOM, (y - (cy - half)) * ZOOM
            rr = r * ZOOM
            dr.ellipse([u - rr, v - rr, u + rr, v + rr], outline=(255, 40, 40, 255), width=2)
            dr.ellipse([u - 2, v - 2, u + 2, v + 2], fill=(255, 40, 40, 255))
        # % środków na zieleni (ExG > 0.06) — w oryginalnej rozdzielczości
        exg = exg_of(mos[int(py0):int(py1), int(px0):int(px1)])
        ii = ((ys - (cy - half)) / dc.GSD).astype(int)
        jj = ((xs - (cx - half)) / dc.GSD).astype(int)
        ok = (ii >= 0) & (ii < exg.shape[0]) & (jj >= 0) & (jj < exg.shape[1])
        vals = exg[ii[ok], jj[ok]]
        pct = 100 * (vals > EXG_GREEN).mean()
        # pokrycie zwartej zieleni w oknie
        cov = 100 * float((exg > EXG_GREEN).mean())
        lat, lon = inverse(cx, cy)
        rec = {'okno': name, 'srodek_wgs84': [round(lon, 6), round(lat, 6)],
               'korony_w_oknie': int(inwin.sum()),
               'pct_srodkow_na_zieleni_ExG>0.06': round(pct, 1),
               'pokrycie_zieleni_okna_ExG>0.06_pct': round(cov, 1),
               'zwarta_zielen_poligony_przecinajace_okno': n_zwarta}
        out.append(rec)
        im.save(f'overlays/{name}.png')
        print(rec, flush=True)
    with open('overlays_check.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    total = sum(r['korony_w_oknie'] for r in out)
    wavg = sum(r['pct_srodkow_na_zieleni_ExG>0.06'] * r['korony_w_oknie']
               for r in out) / total
    print(f'łącznie koron w 3 oknach: {total}; ważony % środków na zieleni: {wavg:.1f}')


if __name__ == '__main__':
    main()
