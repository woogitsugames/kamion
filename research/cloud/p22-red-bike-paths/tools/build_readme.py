#!/usr/bin/env python3
"""M65: generuje README.md (tabele z manifest.csv / inventory.json / data/observations.py + tekst staly z data/readme_text.md)."""
import csv, json, os, sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'data')); sys.dont_write_bytecode = True
import observations as O

def f(v):
    return '—' if v is None else (('%.2f' % v).rstrip('0').rstrip('.').replace('.', ',') if isinstance(v, float) else str(v))

def main():
    rows = list(csv.DictReader(open(os.path.join(HERE, 'manifest.csv'), encoding='utf-8')))
    inv = json.load(open(os.path.join(HERE, 'inventory.json'), encoding='utf-8'))
    cross = {c['node_id']: c for c in json.load(open(os.path.join(HERE, 'crossings.json'), encoding='utf-8'))}
    rid = {r['url_źródła'].rsplit('/', 1)[1]: r['id'] for r in rows if r['kategoria'] in ('odcinek', 'przejazd')}
    T = {}
    # inwentarz
    out = ['| id | region | way_id | highway | surface | segregated | długość [m] | w kaflu [m] | jezdnia równoległa (way) | oś–oś [m] | nawierzchnia wg orto | szer. [m] |', '|---|---|---|---|---|---|---|---|---|---|---|---|']
    for w in inv['ways']:
        t = w['tags']; p = w['parallel'] or {}; o = O.W.get(w['way_id'])
        kol = '—' if not o else ('czerwonobrązowy asfalt' if o[1] == O.CB else 'czerwona (kostka?)' if o[1] == O.CK else 'jasna kostka' if o[1] == O.JK else o[1].split(' (')[0])
        out.append('| %s | %s | %d | %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (rid[str(w['way_id'])], w['region'], w['way_id'], t['highway'], t.get('surface', 'brak tagu'), t.get('segregated', 'brak tagu'),
                   f(w['length_m']), f(w['length_in_tile_m']), ('%s (%d)' % (p['name'] or p['highway'], p['way_id'])) if p else '—', f(p['dist_median_m']) if p else '—', kol, f(o[2]) if o else '—'))
    T['INWENTARZ'] = '\n'.join(out)
    s = []
    for reg in ('C', 'Dojlidy'):
        ws = [w for w in inv['ways'] if w['region'] == reg]
        s.append('- **%s**: %d odcinków, suma długości wg OSM **%s m** (całe way) / **%s m** w granicach kafla.' % (reg, len(ws), f(round(sum(w['length_m'] for w in ws), 1)), f(round(sum(w['length_in_tile_m'] for w in ws), 1))))
    T['SUMY'] = '\n'.join(s)
    # szerokosci
    out = ['| way_id | region | przekrój | nawierzchnia | DDR/ciąg [m] | chodnik [m] | zieleń przy jezdni [m] | układ od jezdni |', '|---|---|---|---|---|---|---|---|']
    reg = {w['way_id']: w['region'] for w in inv['ways']}
    for wid, o in O.W.items():
        if o[2] is None: continue
        out.append('| %d | %s | %s | %s | %s | %s | %s | %s |' % (wid, reg[wid], o[0], o[1].split(' (')[0], f(o[2]), f(o[3]), f(o[4]), o[5]))
    T['SZEROKOSCI'] = '\n'.join(out)
    # przejazdy
    out = ['| id | region | node | lat, lon | jezdnia (way) | czerwone pole | s [m] | zebra [m] | wyspa | sygnalizacja (OSM) | wycinek |', '|---|---|---|---|---|---|---|---|---|---|---|']
    for nid, o in list(O.X.items()) + [(k, (v[0], v[1], None, None, 'UNVERIFIED', v[2])) for k, v in O.XC.items()]:
        c = cross[nid]; rd = c['roads'][0]
        out.append('| %s | %s | %d | %.6f, %.6f | %s (%d) | %s | %s | %s | %s | %s | %s |' % (rid[str(nid)], c['region'], nid, c['lat'], c['lon'], rd['name'] or rd['highway'], rd['way_id'],
                   o[1].upper() if o[1] == 'tak' else o[1], f(o[2]), f(o[3]), o[4].split(' (')[0], c['node_tags'].get('crossing', 'brak tagu'), o[0]))
    T['PRZEJAZDY'] = '\n'.join(out)
    out = ['| id | region | node | DDR (way) | wycinek | co widać |', '|---|---|---|---|---|---|']
    for nid, o in O.D.items():
        c = cross[nid]
        out.append('| %s | %s | %d | %d | %s | %s |' % (rid[str(nid)], c['region'], nid, c['cycle_ways'][0]['way_id'], o[0], o[1]))
    T['WJAZDY'] = '\n'.join(out)
    out = ['| id | obiekt | rozbieżność |', '|---|---|---|']
    for r in rows:
        for u in r['uwagi'].split('; '):
            if u.startswith('ROZBIEŻNOŚĆ') or u.startswith('OSM surface='):
                out.append('| %s | %s | %s |' % (r['id'], r['url_źródła'].replace('https://www.openstreetmap.org/', ''), u))
    T['ROZBIEZNOSCI'] = '\n'.join(out)
    out = ['| id | źródło | data | lat, lon | kierunek | way (odl.) | przejazd w kadrze |', '|---|---|---|---|---|---|---|']
    for r in rows:
        if r['kategoria'] == 'kadr' and 'Ortofotomapa' not in r['opis_co_widać'] and 'przekrój' not in r['opis_co_widać']:
            u = r['uwagi'].split('; ')
            out.append('| %s | %s | %s | %s, %s | %s | %s | %s |' % (r['id'], r['url_źródła'].split('/')[2], r['data_zdjęcia'], r['lat'], r['lon'], r['kierunek_deg'], u[0].replace('najbliższy odcinek DDR: ', ''), u[1].replace('przejazd rowerowy w kadrze: ', '')))
    T['KADRY'] = '\n'.join(out)
    from collections import Counter
    c = Counter(r['kategoria'] for r in rows)
    T['LICZBY'] = '%d wierszy: odcinek %d, przejazd %d (w tym %d wjazdów), nawierzchnia %d, kadr %d' % (len(rows), c['odcinek'], c['przejazd'], sum(1 for r in rows if r['opis_co_widać'].startswith('WJAZD')), c['nawierzchnia'], c['kadr'])
    txt = open(os.path.join(HERE, 'data', 'readme_text.md'), encoding='utf-8').read()
    for k, v in T.items():
        assert '{{%s}}' % k in txt, k
        txt = txt.replace('{{%s}}' % k, v)
    open(os.path.join(HERE, 'README.md'), 'w', encoding='utf-8').write(txt)
    print('README.md', len(txt))

if __name__ == '__main__':
    main()
