#!/usr/bin/env python3
"""P12: typologia kolorów dachów — próbkowanie z kadrów ortofoto.
Kadry: files/P12-A*.jpg (istniejące, landmarkowe) + dodatkowe kadry pobrane do /tmp (próbka).
Próba: wszystkie budynki danej klasy (wg BDOT10k/OSM), których centroid wpada w kadr.
Kolor: mediana RGB w dysku (r = sqrt(area/pi)/2, max 8 m) -> najbliższa nazwa z palety.
Wyjście: data/typologia-colors.json (metoda, N, rozkład kolorów per klasa).
"""
import json, math, os, sys
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from epsg2180 import tm_forward
from PIL import Image
import numpy as np
from frames_colors import PALETA, nazwa_koloru, get_frame, probka_rgb

EXTRA_FRAMES = [  # (lat, lon) — rejony zabudowy mieszkalnej bez pokrycia kadrów landmarkowych
    (53.1110, 23.1675), (53.1020, 23.1830), (53.1150, 23.1710),
    (53.1090, 23.1790), (53.1010, 23.1760), (53.1130, 23.1870),
]

def klasa(b):
    if b.get('klasa') == 'altana_ROD': return 'altana_ROD'
    ob = (b.get('osm_building') or ''); sz = (b.get('bdot_funkcja_sz') or ''); og = (b.get('bdot_funkcja_og') or '')
    if 'allotment' in ob: return 'altana_ROD'
    if sz == 'budynek jednorodzinny' or ob in ('house','detached','semidetached_house','bungalow','farm'): return 'dom_jednorodzinny'
    if sz in ('budynek wielorodzinny','budynek zbiorowego zamieszkania') or ob in ('apartments','residential','dormitory'): return 'blok_wielorodzinny'
    if sz in ('produkcyjny','magazyn') or ob in ('industrial','warehouse','hangar','silo') or og.startswith('budynki przemysłowe') or og.startswith('zbiorniki'): return 'hala_przemysłowa'
    if sz in ('obiekt handlowo-usługowy','stacja paliw') or ob in ('retail','commercial','supermarket') or og.startswith('budynki handlowo'): return 'handlowo_usługowy'
    return 'gospodarcze_i_inne'

def main():
    mwr = json.load(open('data/matched-with-roads.json'))
    lc = json.load(open('data/landmark-colors.json'))
    frames = {}
    for r in lc:
        fn = r['frame_file']
        if fn not in frames:
            im = Image.open(fn)
            frames[fn] = (tuple(r['frame_bbox_2180']), im)
    for i, (la, lo) in enumerate(EXTRA_FRAMES):
        cx, cy = tm_forward(la, lo)
        fn = f'/tmp/P12-S{i+1:02d}.jpg'
        bb, im = get_frame(cx, cy, size_m=400, px=800, path=fn)
        if im is None:
            print('pomijam kadr', fn); continue
        frames[fn] = (bb, im)
    print('kadrów:', len(frames))

    from collections import defaultdict, Counter
    res = defaultdict(lambda: {'n': 0, 'kolory': Counter(), 'rgb': []})
    for b in mwr:
        if not b.get('lod_h'): continue
        k = klasa(b)
        for fn, (bb, im) in frames.items():
            x, y = tm_forward(b['lat'], b['lon'])
            if not (bb[0] <= x <= bb[2] and bb[1] <= y <= bb[3]): continue
            rgb = probka_rgb(im, bb, b['lat'], b['lon'], b['area_m2'])
            if rgb:
                res[k]['n'] += 1
                res[k]['kolory'][nazwa_koloru(rgb)] += 1
                res[k]['rgb'].append(rgb)
            break
    out = {}
    for k, v in res.items():
        n = v['n']
        med_rgb = [int(np.median([c[i] for c in v['rgb']])) for i in range(3)] if v['rgb'] else None
        out[k] = {'n_probkowane': n,
                  'rozklad_kolorow': {c: round(100 * cnt / n, 1) for c, cnt in v['kolory'].most_common()},
                  'mediana_rgb': med_rgb}
        print(k, 'N =', n, out[k]['rozklad_kolorow'])
    json.dump({'metoda': ('census próbek: wszystkie budynky klasy z centroidem w kadrach 400x400 m '
                          '(kadry landmarkowe + 6 kadrów dodatkowych na rejony mieszkalne); kolor dachu = '
                          'mediana RGB w dysku r=min(sqrt(A/pi)/2, 8 m); klasyfikacja do palety nazw kolorów'),
               'klasy': out}, open('data/typologia-colors.json', 'w'), ensure_ascii=False, indent=1)

if __name__ == '__main__':
    main()
