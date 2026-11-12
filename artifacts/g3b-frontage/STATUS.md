# STATUS g3b-frontage (ADR 0126)

## 1. Worktree + rozpoznanie (2026-11-12)
Worktree `.claude/worktrees/g3b-frontage` (gałąź `g3b-frontage` z main 1d4674ab), dane skopiowane, junctiony Data/raw/{gugik,osm,refs,mapillary,fab}.
Baseline izolowany: build_world z kodu main w tym worktree (452 s, typologie = main) -> import -> SBS Low-overcast (`run-cycle.ps1 -Name baseline -Tag 0`).
Identyfikacja pierzei (ortofoto 2024-05-27 + Mapillary 2017/2020/2024): salon meblowy bdot:...C34A (BDOT "magazyn" -> hala z dokami w renderze), salon samochodowy bdot:...C785, przeszklony salon bdot:3c5cd1c0, blok 4-kond. bdot:d0f4dd2c (po 2020). Stan 2024: salon samochodowy ciemny (2017-2020 biały z czerwonym narożnikiem).
NASTĘPNY KROK: `uv run --project tools/worldgen pytest tests/gis/test_g3b_frontage.py -q`

## 2. Generator + dane
Nowy moduł `tools/worldgen/streetscape/frontage.py` (override `set.frontage`: kolor ścian per strona świata, attyka/okap, pasy przeszkleń ze słupkami, pola akcentu, maszty flag / totem / maszt kratowy z owalem bez napisów, szyld funkcyjny) na LOD0 i LOD1; haki w buildings_mesh.build (+ override bloków: wall_material, balconies, bands). 4 wpisy `g3b-frontage-*` w overrides.yaml. Testy: tests/gis/test_g3b_frontage.py 8 passed, 1 skipped (QA po przebudowie).
NASTĘPNY KROK: `pwsh artifacts/g3b-frontage/run-cycle.ps1 -Name after1 -Tag 1` (po zakończeniu baseline), potem `bash artifacts/g3b-frontage/make-pairs.sh after1`

## 3. Baseline + build 1 (after1)
Baseline izolowany (build z kodu main 452 s -> import OK -> 40 renderów SBS Low-overcast w `baseline/renders/`). Arkusze SBS (compose) pominięte: slot heavy był zagłodzony 30 min; własne pary `make-pairs.sh` (zdjęcie | przed / zdjęcie | po).
Build 1 OK (506 s): frontages 3, propsy 3/3 postawione, balkony 3413 -> 3357, without_uv1 0. Import OK. Low-overcast G3-B (20 kamer, `stats-diff.py after1`): draws statyczne -8..+2, razem -32..+2 (mediana 0), tris statyczne -9k..0.
Obejrzane pary after1: 150280 - brązowy salon z ciemnym pasem i okapem, ciemny salon, owal na maszcie, flaga; blok jasny bez galerii. Poprawki do builda 2: rząd flag (3 maszty zlewały się w jeden - obrót rzędu, baner 1x4 m, maszt 8.5 m), grubsze nogi masztu kratowego.
Kamery kontrolne `Data/Regions/bialystok-industrial-c/g3b_frontage_cameras.json` (2 pozy pod zdjęcia strudel 2024, 2 widoki kontrolne) + `run-control.ps1`.
NASTĘPNY KROK: `pwsh artifacts/g3b-frontage/run-cycle.ps1 -Name after -Tag 2` potem `bash artifacts/g3b-frontage/make-pairs.sh after; python artifacts/g3b-frontage/stats-diff.py after`
