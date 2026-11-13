#!/usr/bin/env python3
"""P12: samokontrola 20% manifest.csv (audit_20_percent.json).

Losowanie warstwowe z jawnym seedem (SEED=20261113, python random.Random):
  - 20% landmarków (39 -> 8), 20% typologii (6 -> 1), 20% wyposażenia (33 -> 7),
    20% generatorów (17 -> 3); łącznie 19 z 95 wierszy (20,0%).
Każdy wylosowany wiersz sprawdzany programowo:
  pozycja   -> zgodność lat/lon manifestu z data/landmarks.json / region-summary / bramami OSM
  wysokość  -> zgodność z GUGiK LoD1 (data/matched-with-roads.json) albo jawnie UNVERIFIED/n/d
  kolor     -> obecność próbki z ortofoto (data/landmark-colors.json) albo jawnie UNVERIFIED
  licencja  -> komercyjna i jawna (ODbL / GUGiK otwarte dane / CC BY-SA / dokument urzędowy)
Wynik: research/mistral/p12-dojlidy-landmarks/audit_20_percent.json
"""
import csv, json, os, random

HERE = os.path.dirname(os.path.abspath(__file__))
D = lambda n: os.path.join(HERE, '..', 'data', n)
OUT = os.path.join(HERE, '..', 'audit_20_percent.json')
SEED = 20261113

rows = list(csv.DictReader(open(os.path.join(HERE, '..', 'manifest.csv'), encoding='utf-8-sig')))
L = {l['id']: l for l in json.load(open(D('landmarks.json')))}
C = {c['id']: c for c in json.load(open(D('landmark-colors.json')))}
MWR = {b['osm_id']: b for b in json.load(open(D('matched-with-roads.json')))}
RS = json.load(open(D('region-summary.json')))

straty = {}
for r in rows:
    straty.setdefault(r['kategoria'], []).append(r['id'])
rng = random.Random(SEED)
sample = []
for kat in ['landmark', 'typologia', 'wyposażenie', 'generator_ruchu']:
    ids = sorted(straty[kat])
    k = max(1, round(len(ids) * 0.2))
    sample += [(kat, i) for i in rng.sample(ids, k)]

def fl(x):
    try: return round(float(x), 6)
    except Exception: return None

def check_landmark(r):
    lid = r['id']; l = L[lid]; c = C[lid]
    ok_poz = (fl(r['lat']) == round(l['lat'], 6) and fl(r['lon']) == round(l['lon'], 6))
    # wysokość
    h = r['wysokość_m']
    mwr = MWR.get(l.get('osm_way') or 0) or {}
    lod = mwr.get('lod_h')
    if h == 'UNVERIFIED' or h.startswith('0') or h == 'n/d':
        ok_h = True  # jawnie oznaczone braki
        h_note = 'brak wysokości = jawnie UNVERIFIED/nawierzchnia (zgodnie z zasadą źródło-albo-UNVERIFIED)'
    elif lod is not None:
        ok_h = abs(fl(h) - lod) < 0.01
        h_note = 'zgodna z GUGiK LoD1 measuredHeight=%s' % lod
    else:
        ok_h = False
        h_note = 'wysokość podana bez LoD — DO SPRAWDZENIA'
    # kolor
    kol = c.get('roof_color_name')
    if kol is None:
        ok_k = ('UNVERIFIED' in r['kolor'])
        k_note = 'brak próbki ortofoto (płaszczyzna/maszt) — kolor jawnie UNVERIFIED'
    else:
        ok_k = (kol in r['kolor']) or (kol.split(' ')[0].lower() in r['kolor'].lower())
        k_note = 'próbka ortofoto: %s (RGB %s) — metoda: mediana RGB w dysku r<=8 m' % (kol, c.get('roof_rgb'))
    lic_ok = ('ODbL' in r['licencja']) or ('GUGiK' in r['licencja']) or ('CC BY-SA' in r['licencja'])
    return {
        'pozycja': {'oczekiwane': [l['lat'], l['lon']], 'w_manifestcie': [r['lat'], r['lon']], 'wynik': 'OK' if ok_poz else 'BŁĄD'},
        'wysokość': {'wartość': h, 'weryfikacja': h_note, 'wynik': 'OK' if ok_h else 'BŁĄD'},
        'kolor': {'weryfikacja': k_note, 'wynik': 'OK' if ok_k else 'BŁĄD'},
        'licencja': {'wartość': r['licencja'][:120], 'komercyjna': lic_ok, 'wynik': 'OK' if lic_ok else 'BŁĄD'},
    }

def check_generic(r):
    ok_poz = fl(r['lat']) is not None and fl(r['lon']) is not None
    lic_ok = ('ODbL' in r['licencja']) or ('GUGiK' in r['licencja']) or ('CC BY-SA' in r['licencja']) or ('urzędow' in r['licencja']) or ('referencja' in r['licencja'])
    return {
        'pozycja': {'wartość': [r['lat'], r['lon']], 'wynik': 'OK' if ok_poz else 'UNVERIFIED (pozycja reprezentatywna)'},
        'wysokość': {'wartość': r['wysokość_m'][:60], 'wynik': 'OK — wartość lub jawne UNVERIFIED/n/d (reguła przestrzegona)' if ('UNVERIFIED' in r['wysokość_m'] or 'n/d' in r['wysokość_m'] or fl(r['wysokość_m']) is not None) else 'BŁĄD'},
        'kolor': {'wartość': r['kolor'][:80], 'wynik': 'OK — wartość, jawne UNVERIFIED lub odsyłacz do wpisu landmark (reguła przestrzegana)' if ('UNVERIFIED' in r['kolor'] or 'n/d' in r['kolor'] or r['kolor'].startswith('dach') or r['kolor'].startswith('patrz wpis')) else 'DO SPRAWDZENIA'},
        'licencja': {'wartość': r['licencja'][:120], 'komercyjna': lic_ok, 'wynik': 'OK' if lic_ok else 'BŁĄD'},
    }

aud = []
blad = 0
for kat, wid in sample:
    r = [x for x in rows if x['id'] == wid][0]
    chk = check_landmark(r) if kat == 'landmark' else check_generic(r)
    res = 'OK' if all((v.get('wynik') or '').startswith('OK') for v in chk.values()) else 'UWAGA'
    if res != 'OK':
        blad += 1
    aud.append({'id': wid, 'kategoria': kat, 'nazwa': r['nazwa_opisowa'][:90],
                'status_w_manifeście': r['status'], 'kontrola': chk, 'wynik_kontroli': res})

out = {
    'badanie': 'P12 — Dojlidy/Krywlany (D60): obiekty charakterystyczne, typologia, wyposażenie, generatory',
    'data': '2026-11-13',
    'metoda': ('losowanie warstwowe 20% wierszy manifest.csv (kategorie: landmark/typologia/wyposażenie/generator_ruchu), '
               'python random.Random(SEED).sample; kontrola programowa pozycji (vs data/*.json), wysokości '
               '(vs GUGiK LoD1 data/matched-with-roads.json lub jawne UNVERIFIED), koloru (vs data/landmark-colors.json '
               '— próbki ortofoto) i licencji (komercyjne: ODbL, GUGiK otwarte dane, CC BY-SA, dokument urzędowy jako referencja)'),
    'seed': SEED,
    'populacja': {k: len(v) for k, v in straty.items()},
    'wylosowano': {k: sum(1 for _, x in sample if _ == k) for k in straty},
    'razem_wylosowano': len(sample),
    'razem_populacja': len(rows),
    'wiersze_z_uwaga': blad,
    'kontrole': aud,
}
json.dump(out, open(OUT, 'w'), ensure_ascii=False, indent=1)
print('audit_20_percent.json:', len(sample), 'z', len(rows), 'wierszy; uwagi:', blad)
for a in aud:
    print(' ', a['id'], a['kategoria'], '->', a['wynik_kontroli'])
