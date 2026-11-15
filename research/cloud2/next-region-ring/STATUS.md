# STATUS — R9 next-region-ring

## 2026-11-14 17:20 UTC — krok 1
- Worktree /workspace/wt/next-region-ring, gałąź research/cloud2-next-region-ring.
- Proponowany bbox (propozycja): EPSG:2180 764683,584959 → 787211,605439 (11×10 kafli 2048 m, 461,4 km²), siatka zgodna z istniejącymi regionami.
- Overpass: overpass-api.de niedostępny przez proxy (reset), działa mirror maps.mail.ru (504 losowo, retry). Węzły S8/S19 pobrane.
- GUGiK: skorowidze ORTO/NMT/NMPT 2018–2026 (27 zapytań, HTTP 200), pokrycie policzone (gugik/skorowidze_coverage.json); BDOT10k/LoD1/LoD2 GetFeatureInfo; PRG gminy.
- Uwaga: powiat białostocki = TERYT 2002 (nie 2010) — potwierdzone GetFeatureInfo.
- NASTĘPNY KROK: `python3 research/cloud2/next-region-ring/tools/ovp.py highways research/cloud2/next-region-ring/overpass/queries/highways.ql research/cloud2/next-region-ring/files/overpass_raw research/cloud2/next-region-ring/overpass/_log.jsonl` (i pozostałe .ql), potem analiza tagów.

## 2026-11-14 17:27 UTC — krok 2
- Overpass (mirror maps.mail.ru): junctions(11), bridges_tunnels(1169), barriers(810), services(76), signs_furniture(2845) — surowe w overpass/*.json. highways/buildings: brama 504 przy pełnym bboxie → kafle 4×4 (tools/ovp_tiled.py), w toku.
- Panoramax: 653 zdjęcia w bboxie (14 sekwencji; 613 z 2 sekwencji 2019 wzdłuż S8→Trasa Generalska→DK8 N). Pobrano i OBEJRZANO 28 kadrów (files/frames, lista panoramax/frames_selection.json).
- KartaView: 161 zapytań (komórki 600 m korytarzy), 16 sekwencji (API zwraca ~1 zdjęcie/sekwencję/zapytanie) — kartaview/*.json.
- Commons geosearch: w toku (429 losowo, backoff).
- GUGiK: szacunek rozmiaru NMT/NMPT z HEAD (gugik/head_sizes_sample.json).
- NASTĘPNY KROK: `python3 research/cloud2/next-region-ring/tools/osm_analyze.py highways buildings` po zakończeniu ovp_tiled; potem manifest.csv + README.

## 2026-11-14 ~17:45 UTC — krok 3 (ZAMKNIĘCIE na polecenie lidera — limit sesji)
- manifest.csv 371 wierszy; 38 kadrów obejrzanych; audit 75 wierszy seed 20261114: 74 PASS / 1 FAIL (PX20 poprawiony); fetch.py OK (24,9 MB, 0 niezgodnych).
- NIE ZEBRANO: Overpass highways (klasy < primary; 10/16 kafli) i buildings; Commons 17/24 punktów; Mapillary (brak tokenu).
- NASTĘPNY KROK (z katalogu research/cloud2/next-region-ring):
  `python3 tools/ovp_tiled.py highways 4 4 'way({bb})[highway];' 'out tags geom qt;' && python3 tools/ovp_tiled.py buildings 4 4 'way({bb})[building];relation({bb})[building];' 'out tags center qt;' && python3 tools/osm_analyze.py highways buildings && python3 tools/commons_landmarks.py && python3 tools/build_manifest.py && python3 tools/audit.py`
  (potem odświeżyć README §4 i §9; w commons_landmarks.py dodać sprawdzenie klucza `error` w odpowiedzi 200)

## 2026-11-15 — FIX po recenzji lidera (sesja s21)
- F1: UA ogólny `research-fetch/1.0` w fetch.py i tools/*.py; notatka w sources.md.
- F2: pomiar recenzenta (PBF 2026-11-08) wklejony jako ESTIMATED: overpass/reviewer_pbf_measure.json, README §4a, wiersze R9-394…R9-401. Własne Overpass 4×4 i 6×6 przerwane przez 504 (mirror maps.mail.ru).
- F3: Commons 24/24 punktów (commons/geosearch_landmarks.json), 5 plików obejrzanych (CM01…CM05, files/commons/), żaden nie pokazuje celu L03/L19/L23.
- Zdjęcia w repo: files/jpg1600/ (39 JPG ≤1600 px + INDEX.csv), files/commons/.
- Manifest 401 wierszy; audyt uzupełniający (seed 20261115): 10 PASS / 1 FIX (CM01 poprawiony). REVIEW.md: PASS z uwagami P2.
- NASTĘPNY KROK: brak w tym pakiecie; opcjonalnie powtórzyć Overpass z innego środowiska: `python3 tools/ovp_tiled.py highways 6 6 'way({bb})[highway];' 'out tags geom qt;' && python3 tools/osm_analyze.py highways && python3 tools/build_manifest.py`
