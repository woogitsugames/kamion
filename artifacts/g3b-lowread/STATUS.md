# STATUS g3b-lowread (ADR 0127)

## 1. Worktree + baseline + kod (2026-11-12)
Worktree `.claude/worktrees/g3b-lowread` (gałąź `g3b-lowread` z main 31e54e00), dane skopiowane, junctiony Data/raw/{gugik,osm,refs,mapillary,fab}, Library skopiowane.
Baseline = świat main (regen d) bez przebudowy: 40 SBS Low-overcast + Low-clear w `artifacts/g3b-lowread/baseline/renders/`.
Kod: bramownica LOD1 = kratownica (było: 2 pudła), polityka LOD portal/tablice OB [100,800]/[50,800] (Low: 50/400 m, było 25/125), tablice stoją na belce (+0,25 m), tył tablic OB gładki; słup WN 3 poprzeczniki + LOD1 grubszy + pylon_steel ciemny, 6 przewodów + odgromowy na ramionach; ekrany: słupy 0,22 m (wiadukt co 2 m), szkło `screen` (horyzont nieba, film, linie na wiadukcie; keyword _SCREEN_SHEET). Testy `tests/gis/test_g3b_lowread.py` 9 passed.
NASTĘPNY KROK: `pwsh artifacts/g3b-lowread/run-build.ps1 -Log build-world-1.log; pwsh artifacts/g3b-lowread/run-import.ps1 -Log import-1.log; pwsh artifacts/g3b-lowread/run-sbs.ps1 -Name after1`

## 2. Build 1 + ADR draft (2026-11-12 ~13:50)
build_world 1 OK (522 s, pylon 26, glazed 616 m, gantries stale 0). Import 1 padł na `ArrayMemoryError` w build_all.py (brak RAM, przejściowe) -> ponowienie importu + SBS after1 biegnie w tle (pętla do 3 prób).
Dodane: strefa glazed dla odsuniętego ekranu przy 1801374 (ortho: świat OK, rozjazd = FOV/poza SBS), ADR 0127 draft, `ortho-check.py`, `proto-preview.py` (sylwetki LOD0/LOD1). Strefa glazed weszła po starcie builda 1 -> potrzebny build 2.
NASTĘPNY KROK: `pwsh artifacts/g3b-lowread/run-import.ps1 -Log import-1.log; pwsh artifacts/g3b-lowread/run-sbs.ps1 -Name after1; bash artifacts/g3b-lowread/make-pairs.sh after1; python artifacts/g3b-lowread/stats-diff.py after1` -> obejrzeć pary (837235, 381800, 297817, 3678296, 494288, 1801374), potem build 2 (`run-build.ps1 -Log build-world-2.log`), pytest (`run-pytest.ps1`), EditMode (`run-editmode.ps1`), SBS Low-clear (`run-sbs.ps1 -Name after -Lighting clear`).

## 3. after1 obejrzane, cykl 2 uruchomiony (~14:20)
Import 1 OK po ponowieniu; SBS Low-overcast after1 (40 kadrów), pary `pairs-after1/`. G3-B (20 kamer, stats-diff-after1.txt): draws razem +0..+13, mediana +1; tris statyczne +1..+3k, instancje +0..+4k.
Obejrzane: 837235 / 297817 / 275528 - portal czyta się jako kratownica (297817: było pełna rama), tablice na belce, tyły gładkie; 3678296 - słup WN ciemny, 3 poprzeczniki, przewody; 494288 - ekran = jasna płaszczyzna z grubymi ciemnymi słupami i liniami. 1801374 bez zmiany (strefa glazed dopiero w buildzie 2).
W tle: `run-all-2.ps1 -Name after -Tag 2` (build 2 -> fidelity -> pytest gis+gate3 || import -> SBS overcast+clear -> EditMode), znacznik `all-2.done`.
NASTĘPNY KROK: po `all-2.done`: `bash artifacts/g3b-lowread/make-pairs.sh after; python artifacts/g3b-lowread/stats-diff.py after > artifacts/g3b-lowread/stats-diff-after.txt; tail artifacts/g3b-lowread/pytest-gis.log artifacts/g3b-lowread/editmode.log` -> ADR Results, LICENSES, kopia dowodów do main.
