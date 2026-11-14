#!/usr/bin/env python3
"""M51-FIX-2 / zad. 5 — filtr nie-roślinności na gotowym crowns.geojson
(post-filtr; nie zmienia detekcji ani numeracji pozostałych koron).

Problem (przegląd s19 §3.1): filtr z detect_crowns.py usunął 1 obiekt
(5259 -> 5258); zielony autobus na jezdni Al. Tysiąclecia (ok. 53,1556 N,
23,1524 E) nadal był „koroną”.

Metoda (dwa niezależne kryteria, oba odtwarzalne):
1. Jezdnia z OSM: osie dróg samochodowych z roads.graph.json regionu
   bialystok-industrial-c (OSM Geofabrik podlaskie + szerokość BDOT10k; kafel
   = dokładnie kafel zadania). Pas jezdni = oś ± szerokość/2 (width z BDOT10k;
   brak -> lanes x 3,0 m, min. 4 m). Overpass API był nieosiągalny z kontenera
   (2026-11-14: connection reset), dlatego użyto lokalnej, już zrzuconej
   pochodnej OSM — ta sama geometria osi, szerokość z BDOT10k.
2. Kształt bloba (maska jak w detekcji: ExG>0.12 & G>60, opening 3x3,
   closing 5x5, składowa zawierająca środek korony; mozaika ortofoto GUGiK
   2024-05-27 z detect_crowns.load_full):
     wydłużenie  = sqrt(l1/l2) (osie główne, PCA pikseli),
     prostokątność = pole / pole najmniejszego prostokąta obróconego wg osi PCA.
Reguła usunięcia:
   A) środek na jezdni drogi głównej (trunk/primary/secondary/tertiary/
      residential/unclassified/*_link) AND (wydłużenie > 2 OR prostokątność
      > 0.80 OR jasność V > 140) — zielone autobusy (jasne, wydłużone) i ich
      fragmenty; drzewo nie stoi na jezdni, a nawis korony daje blob ciemny,
      okrągły i nieprostokątny;
   B) gdziekolwiek: jasność bloba V = mean(R,G,B) > 140 — jasnozielony/
      turkusowy lakier pojazdów (autobusy BKM, dostawczaki na parkingach) i
      turkusowe pokrycia dachów; w kaflu tylko 13 koron ma V > 140 i wszystkie
      13 obejrzane na ortofoto to nie-roślinność (README, arkusz
      nonveg_check). Bloby 130 < V <= 140 obejrzane: 5/6 to krzewy/drzewa
      (jedyny pojazd, autobus C00291 V=133, łapie reguła A).
   Osie service/living_street NIE są użyte jako jezdnia (w danych OSM to też
   podwórka, place i dojścia; na nich korony to trawniki i krzewy).
   Wersja 1 tego filtra (odrzucona po obejrzeniu próbki 2026-11-14) usuwała
   też poza jezdnią małe wydłużone, gładkie prostokąty (wydł. > 2,5, prost.
   > 0,85, std(V) < 6): 14/14 obejrzanych to roślinność (ogródki działkowe,
   las) — kryterium usunięte; podobnie 1 krzew przy ścieżce (service) — stąd
   ostrzejsza reguła B.
Wyjścia: crowns.geojson (nadpisany, korony bez zmian id), nonveg_removed.geojson
(usunięte z cechami i regułą), wydruk liczników.
Użycie: python3 filter_nonveg.py <orto_dir> <crowns.geojson> <roads.graph.json>
        [--dry]
"""
import json
import os
import sys

import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import detect_crowns as dc  # noqa: E402
from tm2180 import forward  # noqa: E402

CAR_HW = {'motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'unclassified',
          'residential', 'living_street', 'service', 'motorway_link', 'trunk_link',
          'primary_link', 'secondary_link', 'tertiary_link', 'busway'}
MINOR_HW = {'service', 'living_street'}  # w danych: też podwórka, place, dojścia
HALF = 48  # px (12 m) — okno lokalne wokół korony
ELONG, RECT, V_BRIGHT = 2.0, 0.80, 140.0  # A: drogi główne; B: V > V_BRIGHT


def carriageways(path):
    g = json.load(open(path, encoding='utf-8'))
    segs = []  # (x1, y1, x2, y2, half_width)
    for e in g['edges']:
        a = e.get('attrs') or {}
        hw = (a.get('highway') or {}).get('v')
        if hw not in CAR_HW:
            continue
        w = (a.get('width') or {}).get('v')
        if not w:
            lanes = (a.get('lanes') or {}).get('v') or 1
            w = max(4.0, 3.0 * float(lanes))
        pts = e['geometry']
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            segs.append((x1, y1, x2, y2, float(w) / 2, 0.0 if hw in MINOR_HW else 1.0))
    return np.array(segs)


def on_road(S, x, y):
    x1, y1, x2, y2, hw, major = S.T
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    t = np.clip(((x - x1) * dx + (y - y1) * dy) / np.where(L2 == 0, 1, L2), 0, 1)
    d = np.hypot(x1 + t * dx - x, y1 + t * dy - y)
    inside = d <= hw
    if inside.any():  # na jezdni: preferuj drogę główną, potem najbliższą oś
        cand = np.nonzero(inside)[0]
        k = int(cand[np.lexsort((d[cand], -major[cand]))[0]])
    else:
        k = int(np.argmin(d - hw))
    return bool(d[k] <= hw[k]), float(d[k]), float(hw[k]), bool(major[k])


def blob_features(mos, x, y):
    gy, gx = int(round((y - dc.N0) / dc.GSD)), int(round((x - dc.E0) / dc.GSD))
    H, W, _ = mos.shape
    y0, y1 = max(0, gy - HALF), min(H, gy + HALF + 1)
    x0, x1 = max(0, gx - HALF), min(W, gx + HALF + 1)
    reg = mos[y0:y1, x0:x1].astype(np.float32)
    s = reg.sum(axis=2) + 1e-6
    exg = 2 * reg[..., 1] / s - reg[..., 0] / s - reg[..., 2] / s
    mask = ndimage.binary_closing(
        ndimage.binary_opening((exg > dc.EXG_TH) & (reg[..., 1] > dc.G_TH), np.ones((3, 3))),
        np.ones((5, 5)))
    lab, _ = ndimage.label(mask)
    cy, cx = gy - y0, gx - x0
    lid = lab[cy, cx]
    if lid == 0:  # środek ciężkości poza maską (blob wklęsły) — najbliższy piksel
        ys, xs = np.nonzero(lab)
        if len(ys) == 0:
            return None
        k = int(np.argmin((ys - cy) ** 2 + (xs - cx) ** 2))
        if (ys[k] - cy) ** 2 + (xs[k] - cx) ** 2 > 16:
            return None
        lid = lab[ys[k], xs[k]]
    m = lab == lid
    ys, xs = np.nonzero(m)
    V = reg.mean(axis=2)[m]
    pts = np.stack([xs - xs.mean(), ys - ys.mean()], 1).astype(np.float64)
    cov = pts.T @ pts / len(pts)
    ev, evec = np.linalg.eigh(cov)
    l2, l1 = max(ev[0], 1e-9), ev[1]
    proj = pts @ evec
    ext = (np.ptp(proj[:, 0]) + 1) * (np.ptp(proj[:, 1]) + 1)
    return {'elong': float(np.sqrt(l1 / l2)), 'rect': float(len(xs) / ext),
            'area_m2': float(len(xs) * dc.GSD ** 2), 'v_std': float(V.std()),
            'v_mean': float(V.mean()),
            'touches_window': bool(ys.min() == 0 or xs.min() == 0 or
                                   ys.max() == m.shape[0] - 1 or xs.max() == m.shape[1] - 1)}


def main():
    orto, crowns_f, roads_f = sys.argv[1:4]
    dry = '--dry' in sys.argv
    S = carriageways(roads_f)
    mos = dc.load_full(orto)
    g = json.load(open(crowns_f, encoding='utf-8'))
    keep, removed, feats_all = [], [], []
    for f in g['features']:
        lon, lat = f['geometry']['coordinates']
        x, y = forward(lat, lon)
        road, d, hw, major = on_road(S, x, y)
        bf = blob_features(mos, x, y)
        rule = None
        if bf:
            if road and major and (bf['elong'] > ELONG or bf['rect'] > RECT
                                   or bf['v_mean'] > V_BRIGHT):
                rule = ('A: jezdnia drogi głównej (OSM) + kształt/jasność '
                        '(wydłużenie>2 lub prostokątność>0.80 lub V>140)')
            elif bf['v_mean'] > V_BRIGHT:
                rule = 'B: jasny blob V>140 (lakier pojazdu / turkusowy dach)'
        rec = {'id': f['properties']['id'], 'lon': lon, 'lat': lat, 'na_jezdni': road,
               'droga_glowna': major,
               'odl_od_osi_m': round(d, 2), 'polszer_jezdni_m': hw,
               **({k: (round(v, 3) if isinstance(v, float) else v) for k, v in bf.items()} if bf else {}),
               'regula': rule}
        feats_all.append(rec)
        if rule:
            removed.append((f, rec))
        else:
            keep.append(f)
    print(f'koron wejściowych: {len(g["features"])}; na jezdni: '
          f'{sum(r["na_jezdni"] for r in feats_all)}; usunięte: {len(removed)} '
          f'(A: {sum(1 for _, r in removed if r["regula"].startswith("A"))}, '
          f'B: {sum(1 for _, r in removed if r["regula"].startswith("B"))}); '
          f'pozostaje: {len(keep)}')
    base = os.path.dirname(os.path.abspath(crowns_f))
    if dry:  # cechy wszystkich koron do inspekcji (nie do repo)
        with open(os.path.join(base, '_nonveg_features.json'), 'w') as fo:
            json.dump(feats_all, fo)
        return
    rem = {'type': 'FeatureCollection',
           'name': 'M51-FIX-2: obiekty usunięte z crowns.geojson przez filter_nonveg.py',
           'features': [{'type': 'Feature', 'geometry': f['geometry'],
                         'properties': {**f['properties'], **{k: v for k, v in r.items()
                                                               if k not in ('lon', 'lat', 'id')}}}
                        for f, r in removed]}
    with open(os.path.join(base, 'nonveg_removed.geojson'), 'w', encoding='utf-8') as fo:
        json.dump(rem, fo, ensure_ascii=False)
    g['features'] = keep
    igl = sum(1 for f in keep if f['properties']['typ'] == 'iglaste')
    meta = g.setdefault('properties', {})
    meta['filtr_M51-FIX-2'] = (
        f'tools/filter_nonveg.py: usunięto {len(removed)} obiektów (reguły A/B, '
        'patrz nonveg_removed.geojson); pozostaje '
        f'{len(keep)} koron ({igl} iglaste / {len(keep) - igl} liściaste)')
    g['name'] = g.get('name', '') + ' + filtr nie-roślinności M51-FIX-2'
    with open(crowns_f, 'w', encoding='utf-8') as fo:
        json.dump(g, fo, ensure_ascii=False)
    print(f'zapisano: {len(keep)} koron (iglaste {igl}, liściaste {len(keep) - igl})')


if __name__ == '__main__':
    main()
