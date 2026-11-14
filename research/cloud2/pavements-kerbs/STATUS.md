# STATUS — R6 pavements-kerbs

## Krok 1 (2026-11-14 ~17:10 UTC) — worktree, dane OSM
- Worktree `/workspace/wt/pavements-kerbs`, gałąź `research/cloud2-pavements-kerbs`.
- Overpass (overpass-api.de, lz4, z, kumi, private.coffee, mail.ru) niedostępny przez proxy sesji → surowe dane z OSM API 0.6 `/map` (24 kafle, 85 MB, `files/osm/`, poza gitem) — `osm_fetch.py`.
- `osm_analyze.py` → `osm_summary.json`: ulice trasy C i Dojlid (way_id, długości, surface), ciągi boczne ≤30 m, węzły kerb/manhole/tactile_paving. `manhole=*` przy trasie: 0 węzłów.
- NASTĘPNY KROK: `python3 research/cloud2/pavements-kerbs/docs_fetch.py` (Dz.U. 2022 poz. 1518, wytyczne ZDM, OST/KTKNPiP/DSN GDDKiA) i wyciąg cytatów.

## Krok 2 (2026-11-14) — dokumenty normowe (część 1)
- Pobrane do `files/docs/`: Dz.U. 2022 poz. 1518 (ELI), Dz.U. 2016 poz. 124 (uchylone, ELI), Wytyczne ZDM 2025 (BIP 103311), OST D-08.01.01b (kopia BIP Pomiechówek), SST D-05.03.23a (Krasnobród), SST D-08.03.01 (Czernica), WR-D-83-2 (kopia z platformazakupowa.pl).
- Ustalenia: Dz.U. 2022/1518 NIE podaje liczbowej wysokości krawężnika jezdni (tylko § 36 ust. 3 uskok „dostosowany”, § 45 ust. 4 uskok ≤ 0,01 m, § 89 ≥ 0,12 m przy barierze); liczby 6–16 cm i ≤ 2 cm są w uchylonym Dz.U. 2016 poz. 124 (§ 43 ust. 5, § 127 ust. 10); OST: światło 10–12 cm (6/16 wyjątkowo).
- Niedostępne przez proxy: gov.pl, archiwum.gddkia.gov.pl, web.archive.org, yadda.icm.edu.pl (403) → KTKNPiP / DSN GDDKiA oryginały = luka; zamiast tego WR-D-83-2.
- NASTĘPNY KROK: szukanie rozstawu wpustów (BIP Białystok), kart producentów (kostka, kraty), WR-D-42 (czerwona nawierzchnia); potem `python3 research/cloud2/pavements-kerbs/frames_search.py`.
