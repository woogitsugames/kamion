"""Dopisuje wynik audytu s21b (r3) do audit_20_percent.json. Uruchom z katalogu research/rooftop-gsm-s21: python3 -I tools/s21b/audit_r3.py"""
import json, random
ids = ['K67-%03d' % i for i in range(83, 149)]
random.seed(2026111521)
sample = sorted(random.sample(ids, 14))
P = 'PASS'
R = {
    'K67-087': [P, 'kadr ponownie obejrzany (files/): estakada, akumulator ciepła, drzewa; wieży brak — zgodne'],
    'K67-091': [P, 'chodnik, bloki z żółtymi/zielonymi balkonami zasłaniają kierunek celu — zgodne'],
    'K67-114': [P, 'drewniany dom za zielonym ogrodzeniem — zgodne'],
    'K67-122': [P, 'dom jednorodzinny, samochód przed bramą — zgodne'],
    'K67-123': [P, 'biały drewniany dom za białym płotem — zgodne'],
    'K67-125': [P, 'ogrodzenie budowy z graffiti, w tle domy i blok 4 kond. — zgodne'],
    'K67-128': [P, 'budynek 4 kond. + poddasze, kominy wentylacyjne na dachu, masztów brak — zgodne'],
    'K67-131': [P, 'ulica z domami, antena TV na maszcie przy domu — zgodne'],
    'K67-136': [P, 'skrzyżowanie, baner, w tle blok — zgodne'],
    'K67-137': ['FIX', 'opis „dach dwuspadowy niski” — kształtu dachu w kadrze nie widać; poprawiono na „krawędź dachu bez masztów (kształt dachu niewidoczny)”'],
    'K67-142': [P, 'budynek szkolny 3 kond. z ulicy, drzewa bez liści — zgodne'],
    'K67-144': [P, 'boisko, w tle bloki 5 kond. — zgodne'],
    'K67-145': [P, 'URL itemu Panoramax ponownie: HTTP 200; liczby zgodne z wynikiem tools/s21b/pnx.py'],
    'K67-148': [P, 'node/11285970200 ponownie z API OSM: communication:radio=yes, man_made=mast, tower:construction=guyed_tube — zgodne'],
}
assert sorted(R) == sample, (sample, sorted(R))
a = json.load(open('audit_20_percent.json'))
a['r3_s21b'] = {'zakres': 'nowe wiersze K67-083…148 (66)', 'seed': 2026111521,
                'metoda': 'random.seed(2026111521); random.sample(K67-083…148, 14) — 14/66 = 21 %; ponowne obejrzenie pliku z files/ i ponowne sprawdzenie URL',
                'data': '2026-11-15', 'proba': R, 'wynik': '13 PASS, 1 FIX (K67-137 — opis poprawiony)',
                'dodatkowo': 'pomiary K67-094…096: drugi odczyt na innym kadrze (1326673581) — różnica 0,09–0,12 kond.'}
json.dump(a, open('audit_20_percent.json', 'w'), ensure_ascii=False, indent=1)
print(sample)
