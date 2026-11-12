# STATUS g3b-lowread (ADR 0127)

## 1. Worktree + baseline + kod (2026-11-12)
Worktree `.claude/worktrees/g3b-lowread` (gałąź `g3b-lowread` z main 31e54e00), dane skopiowane, junctiony Data/raw/{gugik,osm,refs,mapillary,fab}, Library skopiowane.
Baseline = świat main (regen d) bez przebudowy: 40 SBS Low-overcast + Low-clear w `artifacts/g3b-lowread/baseline/renders/`.
Kod: bramownica LOD1 = kratownica (było: 2 pudła), polityka LOD portal/tablice OB [100,800]/[50,800] (Low: 50/400 m, było 25/125), tablice stoją na belce (+0,25 m), tył tablic OB gładki; słup WN 3 poprzeczniki + LOD1 grubszy + pylon_steel ciemny, 6 przewodów + odgromowy na ramionach; ekrany: słupy 0,22 m (wiadukt co 2 m), szkło `screen` (horyzont nieba, film, linie na wiadukcie; keyword _SCREEN_SHEET). Testy `tests/gis/test_g3b_lowread.py` 9 passed.
NASTĘPNY KROK: `pwsh artifacts/g3b-lowread/run-build.ps1 -Log build-world-1.log; pwsh artifacts/g3b-lowread/run-import.ps1 -Log import-1.log; pwsh artifacts/g3b-lowread/run-sbs.ps1 -Name after1`
