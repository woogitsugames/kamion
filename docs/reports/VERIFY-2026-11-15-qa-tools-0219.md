# VERIFY 2026-11-15 — PR #95 `qa-tools-0219` (ADR 0219)

Weryfikacja lokalna (Windows, z Data/raw) w worktree `verify-cloud-b`. Baza: origin/main `657b85837` (+ #90); PR: `2ce9b03e1`, scalony lokalnie jako `fc62185cf` (bez konfliktów).

## 1. Wynik: DONE — werdykt **FIX** (2 drobne poprawki testów/atrybutów; kod narzędzi działa zgodnie z opisem)

## 2. Ustalenia
1. **Fidelity Dojlidy naprawione.** Na main `fidelity/run.py --region bialystok-dojlidy --no-tile` kończy się rc=1: `ValueError: invalid literal for int() … 'Bw443103344:6284342131-6610648269:0s'` w `metrics.node_arm_check` (l. 628). Po #95: rc=0 z `--no-tile` (65 s) i bez (98 s). W `route_node_arms` 18 wierszy, w tym 2 cięcia granicy kafla ze `skipped: tile_boundary` (`Bw443103344…:0s`, `Bw236885860…:0e`).
2. **Metryki C bez zmian.** Pełny przebieg `--region bialystok-industrial-c` po #95 vs `Data/Regions/bialystok-industrial-c/generated/fidelity_qa.json` z origin/main: identyczne po pominięciu pól `overlay` (17 ścieżek do JPG, które zależą od mojego `--art`). `route_node_arms` 30/30 identyczne, `summary` identyczne, `inputs_sha256` identyczne. Przebieg `--no-tile` na main vs po #95: różnią się tylko te same ścieżki overlay (11).
3. **FIX 1 — `tests/gis/test_qa_tools_0219.py::test_committed_prg_boundaries_and_manifest` pada na Windows** (77 passed, 1 failed). Manifest ma sha256 pliku z LF (`f90444f8…`, 139 359 B = blob w gicie), a checkout z `* text=auto` daje CRLF na końcu (`fb0489b3…`, 139 360 B). Poprawka: `Data/Admin/*.geojson -text` (albo `text eol=lf`) w `.gitattributes`, albo liczenie skrótu po normalizacji końców linii.
4. **FIX 2 / warunek scalenia — `tests/gis/test_far_field_boundary.py::test_regenerated_building_rectangles_do_not_intersect_region` pada z Data/raw**: `far-field-gis-cache/11` (cache C na dysku) ≠ `GIS_CACHE_SCHEMA` 12 po PR. W chmurze test był pomijany (brak cache). Zzielenieje dopiero po regeneracji far_field regionu C (pkt 2 komend lidera) — scalenie i regeneracja C muszą iść razem, albo test powinien pomijać nieaktualny schemat cache.
5. **Wybór powiatów działa na kaflu granicznym** (dw671-tykocin-01, `build_world`, 174 s). Atrybucja trzema buildami (commit w gicie → narzędzia main → narzędzia #95): #95 zmienia wyłącznie `far_field_qa.json`, sekcję far_field w `world_manifest.json` oraz `far_field.glb`, `far_field.low.glb`, `far_field_gis_cache.json` (pozostałe 194 pliki `Data/raw/derived/…/world` bit w bit). Far field: budynki 0 → **1677**, lasy 0 → **472**, słupy 27 → 342, linie 1 → 137; tris High **35 458**, Low **7 926** (budżet Low ≤ 30 000).
6. Pozostałe różnice tykocina względem gita (łaty dróg 101 → 125, tris dróg +70 itp.) występują już na narzędziach z main — `generated/` tykocina w gicie jest nieświeże względem main, to nie #95.
7. Testy powiązane (11 plików dopasowanych wzorcem far_field*/knyszyn*/kleeberga/maczka/knyszynska/road_fidelity/route_connectivity/water_0210/determinism*, bez `hash_seed`): 99 passed, 1 failed (pkt 4), 1 xfailed, 1 deselected.

## 3. Zmienione pliki
Żadnych w PR. Raport: ten plik. `generated/*` regionów C i Dojlidy przywrócone, nic nie zacommitowane.

## 4. Dowody (`C:\Users\matma\Documents\Claude\kamion\artifacts\verify-cloud-b\pr95\`)
- `before/bialystok-dojlidy.log` (traceback na main), `before/bialystok-industrial-c.fidelity_qa.json`.
- `after/*.notile.log`, `after/*.full.log`, `after/*.fidelity_qa.json`, overlaye w `after/art*/`.
- `pytest-0219.log`, `pytest-related.log`.
- `tykocin/generated-main|generated-mainbuild|generated-after95/`, `tykocin/derived-*.sha256`, `tykocin/build_world*.log`.

## 5. Uruchomione / zmierzone
- Uruchomione: pytest 0219, pytest powiązane, fidelity C i Dojlidy (`--no-tile` i pełne), build_world tykocina ×2.
- NIE uruchomione (zakaz dotykania regionów lub poza zleceniem): fidelity maczka/kleeberga/knyszynska/dk65-0*, far_field dla C/dojlidy/dk65/knyszyn*, woda dk65-02 (`water_sources.json`), `lod2_extract`, pełne `tests/gis`. Horyzont tykocina z nowym far fieldem jest na renderach z weryfikacji #96 (`artifacts/verify-cloud-b/pr96/vqa/`).

## 6. Ryzyka i znane braki
- Typologia far fieldu tykocina: `office` 1204 z 1677 budynków na wiejskim kaflu (house 175, hall 293) — wygląda na błędną klasyfikację budynków LoD1; nie wpływa na budżet, może wpływać na wygląd horyzontu. Do sprawdzenia przy regeneracji.
- W Dojlidach `sites_iou` ma klucze miejsc regionu C (`01_gate`, …) z IoU 0,0 — lista miejsc w `fidelity/run.py` jest ustawiona pod C; metryka dla innych regionów jest pusta, nie błędna.
- Zmiana `water.extract()` (strefa 0213) niezweryfikowana na danych.

## 7. Następny krok
Autor: FIX 1 i decyzja co do FIX 2. Lider po scaleniu: regeneracja far_field regionów granicznych (pkt 2 PR) razem z C, potem `pytest tests/gis -k far_field` i oględziny horyzontu.
