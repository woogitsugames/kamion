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

## 4. Sesja 12: wznowienie po restarcie 03:44
Scalono main (76b3fb76) -> 5a4f0dd7; konflikt tylko `generated/world_manifest.json` (ours, regeneracja w buildzie 2). Build 2 sprzed restartu: build_world OK, import zabity restartem (exit 1073807364) - cały cykl od nowa na kodzie po scaleniu.
Poprawki builda 2 w kodzie: rząd flag (rotate 10 deg, baner 1x4 m, maszt 8,5 m - już w b89e4ced), maszt kratowy: nogi 0,16 m (było 0,10), rygle 0,10, skratowania 0,11.
NASTĘPNY KROK: `pwsh artifacts/g3b-frontage/run-cycle.ps1 -Name after -Tag 2; bash artifacts/g3b-frontage/make-pairs.sh after; python artifacts/g3b-frontage/stats-diff.py after`

## 5. Build 2 + build 3 (sesja 12)
Build 2 (po scaleniu main): nogi masztu OK, ale 3 flagi nadal zlewały się w jeden żółty blok (rząd 142 deg = na wprost z jezdni). Build 3: rząd obrócony na ~167 deg (rotate_deg 35), baner 0,8 m -> 3 osobne flagi jak na zdjęciach 2024.
Build 3: build_world 492 s, import OK (64 chunki), 40 SBS + 4 kontrolne Low-overcast. pytest gis: 626 passed, 1 xfailed, 1 failed (fidelity stale) -> po `fidelity/run.py` test_road_fidelity + test_g3b_frontage 18 passed, 1 xfailed. EditMode 317/317.
Low-overcast G3-B (20 kamer, vs baseline 1d4674ab, zawiera scalenia s11): draws razem -30..+11, mediana 0; 150280 +6, 297817 -4, 3281350 +11.
ADR 0126 uzupełniony (Results), LICENSES wiersz `world-g3b-frontage`. Dowody skopiowane do main `artifacts/g3b-frontage/`.
NASTĘPNY KROK (lider): visual-critic na `artifacts/g3b-frontage/pairs-after/sbs-g3-b-{150280503737744,297817221966185,3281350541967811}.jpg` + `pairs-2024/`; potem `git merge g3b-frontage` i regeneracja (build_world -> import -> fidelity/run.py).
