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

## Krok 3 (2026-11-14) — manifest dokumentowy, fetch, samokontrola; PRZERWANE na polecenie lidera (limit sesji)
- `manifest.csv`: 72 wiersze (69 SOURCED, 3 UNVERIFIED) — dokumenty + OSM. `build_manifest.py` = źródło prawdy wierszy.
- `fetch.py` OK (11 dokumentów, 38 MB; `--frames` +31 kadrów, 30 MB). `audit_20_percent.json`: 15 PASS / 0 FAIL, seed 20261114.
- Kadry: 31 pobranych z sha256 (`frames_selected.json`), widoki i wycinki 3× w `files/_view/` — **0 obejrzanych, 0 w manifeście**.
- NIEZROBIONE: zad. 6 (oględziny ≥ 30 kadrów), liczby kadrów per typ, widoczność uszkodzeń asfaltu, opis czerwieni DDR, sekcja CC0, rozstaw wpustów.
- NASTĘPNY KROK: `cd /workspace/wt/pavements-kerbs/research/cloud2/pavements-kerbs && python3 osm_fetch.py && python3 fetch.py --frames && python3 frames_select.py` (odtwarza `files/_view/F??_view.jpg` i `F??_crop3x.jpg`), potem obejrzeć każdy kadr narzędziem Read i dopisać wiersze kadrów w `build_manifest.py`; brakujące ulice: `python3 frames_kv_seq.py` (sekw. 1155711 dla Al. Tysiąclecia).
