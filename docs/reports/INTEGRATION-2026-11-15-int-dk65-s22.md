# INTEGRATION 2026-11-15/16 — int-dk65-s22 (DK65 K1 + rondo Knyszyn + szpalery)

Gałąź `int-dk65-s22` (worktree `.claude/worktrees/int-dk65-s22`), baza main 612185470, scalony `origin/main` 16.11
04:2x (72 commity, m.in. spawn-fix-0262 r2). Format: `docs/09` §4.

## 1. Wynik
**PARTIAL — gotowe do scalenia: PATRZ §8** (werdykt zależy od pełnego `pytest tests/gis` i EditMode, które biegną
odłączone: `artifacts/int-dk65-s22/logs/final.status`).

## 2. Ustalenia
1. **Scalone PR-y:** #98 dk65-k1-0220 (przekrój K1, linie krawędziowe przerywane, zatoki), #97 roundabout-0218
   (`truck_apron`), #101 treerows-0222 (szpalery). #93 nie włączony.
2. **D75 materiał opaski:** nowy `apron_paving_light` — faktura kostki z istniejącego zestawu `paving_20x10_grey`,
   albedo [0,42 0,42 0,415] `WORKING_VALUE` (tint silnika 0,42 / 0,26 ≈ 1,6), `ground_grime` z prawie wyłączonymi
   kałużami. Bez nowej tekstury → bez wpisu w `docs/LICENSES.md`. Wymiary wg D75: asfalt 5,0 m + opaska 3,2 m.
3. **Rondo DK65×Tykocka było zepsute geometrycznie już przed 0218** (4 samoprzecinające się płyty, opaska w 8
   klinach; pierwszy render PR #97 = knyszyn r1). Naprawa = **nowy tryb „rondo kompaktowe”** (ADR 0218 §5c):
   moduł `tools/worldgen/roads/compact_roundabout.py`, włączany tylko kluczem override `compact_roundabout` na way
   1426801304 (way jest wyłącznie w kaflu knyszyn). Całe rondo = jedno skrzyżowanie; opaska jako pełny pierścień,
   wyspa `island_sand`, 4 wysepki dzielące z krawężnikiem. Lider zaakceptował geometrię r3 (16.11 04:2x).
4. **Liczby ronda (generator, `pipeline.build("knyszyn")`):** środek −987,29 / −610,73; R osi 8,65 m; asfalt
   pierścienia 5,00 m (r 6,15–11,15); opaska 3,2 m, próg 0,04 m; wyspa r 2,95 m; wysepki 33,7 / 20,5 / 8,6 /
   13,0 m²; `overrides_stale` puste. Dodatkowy override: jezdnie jednokierunkowe DK65 przy rondzie 4,5 m zamiast
   6,0 m z BDOT10k (zdjęcie 9: ~4,2 m, ESTIMATED).
5. **Łańcuch `chain.ps1` („wait bug”):** `Select-String` na nieistniejącym pliku statusu przerywał pętlę
   oczekiwania — import ruszał przed `build_world`. Naprawione (`WorldExit`), dodane ponawianie przy
   exit −1073741502.
6. **Przebudowa:** 14 kafli (knyszyn-s, knyszyn, dk65-01..11, knyszyn-w) — wszystkie `world-*-r1 exit=0`,
   import + VQA Low/High r1: 45 kroków `exit=0`; knyszyn dodatkowo r2 i r3 (rondo kompaktowe), wszystkie `exit=0`.
   Import r3 użył buildu tej gałęzi: 64/64 chunków w `Data/raw/derived/knyszyn/world` ma sha256 z
   `Data/Regions/knyszyn/generated/world_manifest.json` (czasy 04:10:04–07, import 04:10:25).
7. **Szwy (`seams.py`, nieśledzony, z seams-0224):** 11 szwów, 2 FAIL na dk65-11 | knyszyn-s — oba to ograniczenie
   narzędzia (porównuje `sec.lane_w` i maks. `sec.width` profilu, nie zna `width_profile` + `lanes_follow_width`
   z ADR 0233); geometrię tego szwu sprawdza `test_dk65_seam_knyszyn_0233` (passed). 5 UWAG dk65-04 | 05 (drogi
   boczne wzdłuż szwu).
8. **Trasa startowa knyszyn** wyeksportowana ponownie: przesunięcie ≤ 0,02 m (eksport idzie po osiach łańcuchów),
   1,9–2,0 m od wysepek E / S. `export-region-catalog.py`: katalog bez zmian, `--check` rc 0 (startS 90 m z
   spawn-fix-0262 zachowane).

## 3. Zmienione pliki (względem main)
- Generator: `tools/worldgen/roads/{compact_roundabout.py (nowy), network.py, junctions.py, meshing.py, pipeline.py,
  build_world.py, consistency.py, markings.py, route_km.py, swept_path.py}`, `streetscape/{furniture.py, stage.py,
  tree_rows.py, tree_rows_probe.py, vegetation.py}`, `terrain_mesh/conform.py`, `fidelity/{gen.py, planview.py}`,
  `qa/dk65_k1_elements.py`.
- Dane: `Data/Regions/knyszyn/overrides.yaml` (truck_apron, compact, szerokość jezdni DK65 przy rondzie),
  `control_cameras_place.authored.json` (kamera `rondo_dk65_top`), `route_start.json`; overrides dk65-02..05 (0220);
  `generated/` 14 kafli.
- Testy: `tests/gis/test_compact_roundabout_0218.py` (nowy, 9), `test_truck_apron_0218.py`, `test_swept_path_0218.py`,
  `test_dk65_k1_0220.py`, `test_edge_lines_0205.py`, `test_treerows_0222.py`; `tests/physics/swept_path_gate3.py`.
- Docs: ADR 0218 (§5b D75, §5c rondo kompaktowe + Otwarte), 0220, 0222; ten raport.
- Narzędzia agenta (w `artifacts/int-dk65-s22/tools/`): `chain.ps1`, `r2.ps1`, `final.ps1`, skrypty rzutów.

## 4. Dowody
- Testy: `uv run --project tools/worldgen python -m pytest tests/gis/test_compact_roundabout_0218.py
  tests/gis/test_truck_apron_0218.py -q` → 32 passed (po merge main). Wybór `-k "0218 or apron or roundabout or
  junction_seams or knyszyn"` → 95 passed (przed r3; bieg zbiegł się z przebudową knyszyn r2).
- Pełny `pytest tests/gis` i EditMode: `artifacts/int-dk65-s22/logs/{final.status, pytest-gis.log, editmode.log}`
  — wynik w §8.
- Rendery (1920×1080, High i Low, clear): `artifacts/int-dk65-s22/<kafel>/r1/`, `knyszyn/r2/`, `knyszyn/r3/`;
  pomniejszone w main: `artifacts/int-dk65-s22/{knyszyn-r1, knyszyn-r2, knyszyn-r3, k1view, rondo-proto}/`.
  Zestawienie ze zdjęciami właściciela: `artifacts/int-dk65-s22/refs/9.jpg, 10.jpg` (tylko lokalnie).
- Szwy: `artifacts/int-dk65-s22/seams/seams_after.{md,json}`.
- Statusy łańcuchów: `artifacts/int-dk65-s22/logs/chain-world.status`, `chain-unity.status`.

## 5. Napisane / zbudowane / uruchomione / zmierzone
- Napisane: tryb ronda kompaktowego, materiały `apron_paving_light` i `island_sand`, testy, ADR.
- Zbudowane: 14 kafli `build_world` (knyszyn 3×), import do Unity 14 kafli.
- Uruchomione: visual-qa Low/High wszystkich 14 kafli (edytor, nie build gracza), seams, testy jak w §4.
- Zmierzone: tylko geometria z generatora (§2.4) i sha chunków. **Nie mierzono** FPS ani niczego na buildzie
  Windows; albedo materiałów to `WORKING_VALUE`, wymiary ronda ze zdjęcia to `ESTIMATED`.

## 6. Ryzyka i znane braki
- **`generated/` 14 kafli zbudowano PRZED scaleniem main** (main zmienił `streetscape/furniture.py`, `far_field.py`,
  `water.py`, `lod2_extract.py`). Wygenerowane dane nie odpowiadają więc w 100 % kodowi po scaleniu — i tak czeka
  je przebudowa po #138 (ADR 0272).
- `Data/raw` jest junctionem do main: `Data/raw/derived/<kafel>/world` jest wspólne dla wszystkich worktree. Kafel
  knyszyn buduje też knyszyn-rynek-0227 (Codex) — kolejny build nadpisze chunki; import zawsze bierze ostatni.
- Rondo — otwarte (ADR 0218 §5c): szerokie płaty asfaltu między ramionami, krótka wysepka S, brak nasadzeń i
  kamieni, promieniste cieniowanie góry wyspy, P-13 / przejścia przy węźle rozdziału zamiast przy pierścieniu.
- Przejazd zestawu przez wloty z wysepkami 12 cm nie był jechany; `tests/physics/swept_path_gate3.py` nie
  uruchamiany na nowej geometrii.
- Brak oceny `visual-critic` (agent nie tworzy subagentów) — oględziny własne + akceptacja lidera r3.
- Oględziny k1_* (dk65-03/04/05) i szpalerów zrobione na r1: zgodne z ADR 0220 / 0222; asfalt za linią
  krawędziową szeroki (zmieni #138).
- `seams.py` nie zna ADR 0233 (fałszywe FAIL) — do poprawy w gałęzi seams-0224.

## 7. Proponowany następny krok
Scalić do main (jeśli §8 = TAK) → scalić rail-dk65-s22 → #138 → jedna przebudowa wszystkich kafli DK65 / Knyszyn →
oględziny dk65-* i ronda na świeżych danych; osobne zadanie na dopracowanie ronda (ADR 0218 §5c „Otwarte”).

## 8. Gotowe do scalenia
DO UZUPEŁNIENIA po `FINAL DONE` (pełny pytest tests/gis + EditMode).
