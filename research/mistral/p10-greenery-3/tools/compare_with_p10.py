#!/usr/bin/env python3
"""M51 / zad. 3 — porównanie własnej detekcji koron (crowns.geojson)
z wartościami P10-201…237 (pokrycie osi w buforze 8 m, odcinki 100 m)
i P10-301…313 (młode drzewa r 0.7-2.0 m w buforze 20 m alei/Andersa)
z research/gptpro/p10-street-greenery-2/manifest.csv.

Dwie metryki M51:
- "korony": próbka osi (co 5 m) ma >=1 KORONĘ (centroid z crowns.geojson)
  w buforze 8 m — bezpośredni odpowiednik definicji P10;
- "maska": w buforze 8 m od próbki jest jakikolwiek piksel maski roślinności
  (ExG>0.12 & G>60, jak w detect_crowns.py) — kontrola obecności zieleni
  niezależna od podziału na korony.

Okno: punkty osi ulicy (roads.graph.json, resampling co 1 m) w promieniu L/2
od punktu P10 (L = długość odcinka P10; pełny = 100 m). Uwaga: dokładne
granice okien P10 (liczone wzdłuż osi od południa) nie są zapisane w manifeście
— rekonstrukcja przez środek + promień jest przybliżeniem; dla prostych
odcinków ulic równoważna, dla zakrętów może przesuwać próbkowanie o kilka m.

Wyniki: comparison_p10.json (per wiersz P10) + street_agg.json
(agregaty dla 9 ulic zadania i alei/Andersa).
"""
import csv
import json
import math
import os
import re
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tm2180 import forward

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) or '.'
GSD = 0.25
E0, N0, E1, N1 = 776971, 595199, 779019, 597247
CHUNKS = [('sw.png', 595199, 776971), ('se.png', 595199, 777995),
          ('nw.png', 596223, 776971), ('ne.png', 596223, 777995)]
EXG_TH, EXG_TH_SOFT, G_TH = 0.12, 0.06, 60
STREETS = ['Kowieńska', 'Lidzka', 'Skidelska', 'Wołkowyska', 'Świsłocka',
           'Wileńska', 'Grodzieńska', 'Racławicka', 'Łańcucka']


def resample(geom, step=1.0):
    pts = []
    for i in range(len(geom) - 1):
        x0, y0 = geom[i]
        x1, y1 = geom[i + 1]
        d = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(d / step))
        for k in range(n):
            pts.append((x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n))
    pts.append(tuple(geom[-1]))
    return np.array(pts)


def build_mask():
    """Maska roślinności całego kafla (jak detect_crowns.py)."""
    mask = np.zeros((int((N1 - N0) / GSD), int((E1 - E0) / GSD)), bool)
    for name, n0, e0 in CHUNKS:
        im = np.asarray(Image.open(os.path.join(BASE, 'orto', name))).astype(np.float32)
        s = im.sum(axis=2) + 1e-6
        exg = 2 * im[..., 1] / s - im[..., 0] / s - im[..., 2] / s
        m = (exg > EXG_TH) & (im[..., 1] > G_TH)
        m = ndimage.binary_opening(m, np.ones((3, 3)))
        m = ndimage.binary_closing(m, np.ones((5, 5)))
        iy, ix = int((n0 - N0) / GSD), int((e0 - E0) / GSD)
        mask[iy:iy + 4096, ix:ix + 4096] = m
        print('maska', name, flush=True)
    return mask


def main():
    crowns = json.load(open(os.path.join(BASE, 'crowns.geojson')))
    P = np.array([forward(f['geometry']['coordinates'][1],
                          f['geometry']['coordinates'][0]) for f in crowns['features']])
    R = np.array([f['properties']['r_m'] for f in crowns['features']])
    TYP = np.array([f['properties']['typ'] for f in crowns['features']])
    mask = build_mask()

    def mask_cov(cx, cy, rad):
        px, py = int(round((cx - E0) / GSD)), int(round((cy - N0) / GSD))
        rpx = int(rad / GSD)
        return bool(mask[max(0, py - rpx):py + rpx + 1, max(0, px - rpx):px + rpx + 1].any())

    g = json.load(open(os.path.join(BASE, 'data', 'roads.graph.json')))
    pts_by = {}
    for e in g['edges']:
        nm = e.get('attrs', {}).get('name', {}).get('v')
        if nm:
            pts_by.setdefault(nm, []).append(resample(e['geometry']))

    rows = list(csv.DictReader(open(os.path.join(BASE, 'ref', 'gptpro',
        'p10-street-greenery-2', 'manifest.csv'), encoding='utf-8')))
    out = []
    for r in rows:
        if not (r['id'].startswith('P10-2') or r['id'].startswith('P10-3')):
            continue
        lat, lon = float(r['lat']), float(r['lon'])
        cx, cy = forward(lat, lon)
        is2 = r['id'].startswith('P10-2')
        m = re.search(r'odcinek (\d+) m', r['obiekt'])
        L = int(m.group(1)) if m else 100
        radius, buf = (L / 2, 8.0) if is2 else (50.0, 20.0)
        pts = pts_by.get(r['ulica'])
        if pts is None:
            for nm in pts_by:
                if nm.startswith(r['ulica'][:12]) or r['ulica'].startswith(nm[:12]):
                    pts = pts_by[nm]
                    break
        if pts is None:
            out.append({'id': r['id'], 'ulica': r['ulica'], 'error': 'brak osi'})
            continue
        ap = np.vstack(pts)
        d2 = (ap[:, 0] - cx) ** 2 + (ap[:, 1] - cy) ** 2
        samples = ap[d2 <= radius ** 2][::5]
        if len(samples) == 0:
            out.append({'id': r['id'], 'ulica': r['ulica'], 'error': 'puste okno'})
            continue
        covered, crowns_in, mask_covered = 0, set(), 0
        for s in samples:
            dd = ((P[:, 0] - s[0]) ** 2 + (P[:, 1] - s[1]) ** 2) <= buf ** 2
            idx = np.nonzero(dd)[0]
            if not is2:
                idx = idx[(R[idx] >= 0.7) & (R[idx] <= 2.0)]
            if len(idx):
                covered += 1
                crowns_in.update(idx.tolist())
            if mask_cov(s[0], s[1], buf):
                mask_covered += 1
        win_len = len(samples) * 5
        rec = {'id': r['id'], 'ulica': r['ulica'], 'okno_m': win_len,
               'n_probek': len(samples)}
        if is2:
            p10c = int(re.match(r'(\d+)%', r['gęstość_na_100m']).group(1))
            rec.update({'p10_pokrycie': p10c, 'm51_pokrycie': round(100 * covered / len(samples)),
                        'm51_maska': round(100 * mask_covered / len(samples)),
                        'p10_korony': int(re.search(r'/ (\d+) koron', r['gęstość_na_100m']).group(1)),
                        'm51_korony': len(crowns_in)})
        else:
            p10d = int(re.match(r'(\d+) szt', r['gęstość_na_100m']).group(1))
            rec.update({'p10_na_100m': p10d,
                        'm51_na_100m': round(len(crowns_in) / win_len * 100),
                        
                        'n_mlodych': len(crowns_in)})
        out.append(rec)
        print(rec, flush=True)
    with open(os.path.join(BASE, 'comparison_p10.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    # agregaty per ulica (bufor 8 m od osi, cala dlugosc w kaflu)
    agg = {}
    for nm in STREETS + ['Aleja Tysiąclecia Państwa Polskiego', 'Generała Władysława Andersa']:
        if nm not in pts_by:
            continue
        ap = np.vstack(pts_by[nm])
        L = len(ap)  # punkty co 1 m
        d = np.min(np.hypot(P[:, None, 0] - ap[None, ::5, 0],
                            P[:, None, 1] - ap[None, ::5, 1]), axis=1)
        near = d <= 8.0
        n = int(near.sum())
        agg[nm] = {'os_m': int(L), 'korony_buf8': n,
                   'na_100m': round(n / L * 100, 1),
                   'r_med': float(np.median(R[near])) if n else None,
                   'iglaste_pct': round(100 * (TYP[near] == 'iglaste').sum() / n) if n else None}
        print(agg[nm], nm, flush=True)
    with open(os.path.join(BASE, 'street_agg.json'), 'w', encoding='utf-8') as f:
        json.dump(agg, f, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
