#!/usr/bin/env python3
"""M51-FIX: samokontrola 20% manifestu (nowe losowanie, nowy seed 20261114).

Dla wylosowanych wierszy:
- kadry zdjeciowe: "co widac" w uwagach + ulica z OSM (przeliczona odleglosc geotagu
  od osi ulicy wg roads.graph.json, EPSG:2180) + kierunek UNVERIFIED + licencja;
- odcinki zywoplotow: dodatkowo typ/gatunek + wysokosc ESTIMATED + id zdjecia w uwagach;
- wiersze koron: odsetek srodkow koron na zieleni (ExG>0,06) w 3 oknach 300x300 m
  z overlays_check.json (prog >80%);
- wiersze BIP/przetarg: status + licencja.
Wynik: audit_20_percent.json (nadpisuje poprzednia samokontrole z seedem 20261113).
"""
import csv, json, math, random, re, sys, os
from math import ceil
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'tools'))
from tm2180 import forward

SEED = 20261114
TOL = 25.0

def load_axes():
    g = json.load(open(os.path.join(HERE, 'data', 'roads.graph.json')))
    axes = {}
    for e in g['edges']:
        a = e.get('attrs') or {}
        nm = a.get('name'); nm = nm.get('v') if isinstance(nm, dict) else nm
        if nm: axes.setdefault(nm, []).append([(p[0], p[1]) for p in e['geometry']])
    return axes

def dist_to_street(axes, lat, lon, street):
    if street not in axes: return None
    x, y = forward(lat, lon)
    best = float('inf')
    for pts in axes[street]:
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            dx, dy = x2 - x1, y2 - y1; L2 = dx * dx + dy * dy
            t = 0 if L2 == 0 else max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / L2))
            d = math.hypot(x - (x1 + t * dx), y - (y1 + t * dy))
            if d < best: best = d
    return best

def main():
    rows = list(csv.DictReader(open(os.path.join(HERE, 'manifest.csv'), newline='', encoding='utf-8-sig')))
    ids = [r['id'] for r in rows]
    n = len(ids)
    k = ceil(0.2 * n)
    sample = sorted(random.Random(SEED).sample(ids, k))
    axes = load_axes()
    ov = json.load(open(os.path.join(HERE, 'overlays_check.json')))

    wyniki = []
    for rid in sample:
        r = next(x for x in rows if x['id'] == rid)
        checks = {}
        obiekt = r['obiekt'] or ''
        is_photo = obiekt.startswith('zdjęcie z poziomu')
        is_hedge = 'żywopłot' in obiekt or 'odcinek' in obiekt
        is_crown = 'detekcja koron' in obiekt or 'koron' in obiekt.lower()
        # kazdy wiersz: status + licencja
        checks['status'] = {'ok': r['status'] in ('SOURCED', 'ESTIMATED', 'UNVERIFIED'),
                            'info': r['status']}
        checks['licencja'] = {'ok': bool(r['licencja']),
                              'info': r['licencja'][:60] if r['licencja'] else 'brak'}
        if is_photo or is_hedge:
            # co widac
            has_desc = len((r['uwagi'] or '')) > 40
            checks['co_widac'] = {'ok': has_desc,
                                  'info': (r['uwagi'] or '')[:110] + ('…' if len(r['uwagi'] or '') > 110 else '')}
            # ulica z OSM + odleglosc do osi
            lat = float(r['lat']) if r['lat'] else None
            lon = float(r['lon']) if r['lon'] else None
            ul = r['ulica'] or ''
            if lat is None:
                checks['ulica_osm'] = {'ok': False, 'info': 'brak geotagu'}
            elif not ul:
                ok = ('POZA progiem' in (r['uwagi'] or '')) or ('kwartał' in (r['uwagi'] or ''))
                checks['ulica_osm'] = {'ok': ok, 'info': 'ulica pusta; uwagi: ' + (r['uwagi'] or '')[:80]}
            else:
                d = dist_to_street(axes, lat, lon, ul)
                if d is None:
                    checks['ulica_osm'] = {'ok': False, 'info': f'ulicy {ul} nie ma w grafie OSM'}
                elif d <= TOL:
                    checks['ulica_osm'] = {'ok': True,
                                           'info': f'{ul}: geotag {d:.1f} m od osi (reguła <=25 m)'}
                else:
                    disclosed = 'POZA progiem' in (r['uwagi'] or '')
                    checks['ulica_osm'] = {'ok': disclosed,
                                           'info': (f'{ul}: geotag {d:.1f} m od osi (>25 m); '
                                                    + ('ujawnione w uwagach (POZA progiem, atrybucja ESTIMATED)' if disclosed else 'NIEUJAWNIONE'))}
            # kierunek
            checks['kierunek'] = {'ok': 'UNVERIFIED' in (r['kierunek_deg'] or ''),
                                   'info': r['kierunek_deg']}
        if is_hedge:
            checks['typ_gatunek'] = {'ok': bool(r['gatunek']), 'info': r['gatunek']}
            checks['wysokosc_estimated'] = {'ok': bool(r['wysokość_m']) and 'ESTIMATED' in (r['metoda'] or ''),
                                            'info': r['wysokość_m']}
            checks['id_zdjecia'] = {'ok': 'id zdjęcia' in (r['uwagi'] or ''), 'info': 'w uwagach' if 'id zdjęcia' in (r['uwagi'] or '') else 'brak'}
        if is_crown:
            key = 'pct_srodkow_na_zieleni_ExG>0.06'
            try:
                vals = [(w.get('okno', i), float(w[key])) for i, w in enumerate(ov)]
                w_ok = all(v > 80 for _, v in vals)
                info = ', '.join(f"{nm}: {v:.1f}%" for nm, v in vals)
            except Exception as e:
                w_ok, info = False, f'błąd parsowania: {e}'
            checks['korony_3_okna'] = {'ok': w_ok, 'info': info + ' (próg >80%)'}
        wyniki.append({'id': rid, 'checks': checks,
                       'pass': all(c['ok'] for c in checks.values())})

    out = {
        'zadanie': 'M51-FIX — samokontrola 20% manifestu (nowe losowanie po naprawach)',
        'data': '2026-11-13',
        'seed': SEED,
        'generator': f'random.Random({SEED}).sample(ids, ceil(0.2*n)); sort()',
        'poprzedni_seed': 20261113,
        'n_wierszy': n,
        'n_probek': k,
        'probki': sample,
        'korony_3_okna': [dict(w) for w in ov],
        'wyniki': wyniki,
        'pass_all': all(w['pass'] for w in wyniki),
    }
    json.dump(out, open(os.path.join(HERE, 'audit_20_percent.json'), 'w'), ensure_ascii=False, indent=1)
    print(f'n={n}, próbek={k}, PASS={out["pass_all"]}')
    for w in wyniki:
        print(f"  {w['id']}: {'PASS' if w['pass'] else 'FAIL'}")
        for cn, c in w['checks'].items():
            if not c['ok']: print(f'    ! {cn}: {c["info"]}')

if __name__ == '__main__':
    main()
