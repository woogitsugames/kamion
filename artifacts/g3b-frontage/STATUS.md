# STATUS g3b-frontage (ADR 0126)

## 1. Worktree + rozpoznanie (2026-11-12)
Worktree `.claude/worktrees/g3b-frontage` (gałąź `g3b-frontage` z main 1d4674ab), dane skopiowane, junctiony Data/raw/{gugik,osm,refs,mapillary,fab}.
Baseline izolowany: build_world z kodu main w tym worktree (452 s, typologie = main) -> import -> SBS Low-overcast (`run-cycle.ps1 -Name baseline -Tag 0`).
Identyfikacja pierzei (ortofoto 2024-05-27 + Mapillary 2017/2020/2024): salon meblowy bdot:...C34A (BDOT "magazyn" -> hala z dokami w renderze), salon samochodowy bdot:...C785, przeszklony salon bdot:3c5cd1c0, blok 4-kond. bdot:d0f4dd2c (po 2020). Stan 2024: salon samochodowy ciemny (2017-2020 biały z czerwonym narożnikiem).
NASTĘPNY KROK: `uv run --project tools/worldgen pytest tests/gis/test_g3b_frontage.py -q`

## 2. Generator + dane
Nowy moduł `tools/worldgen/streetscape/frontage.py` (override `set.frontage`: kolor ścian per strona świata, attyka/okap, pasy przeszkleń ze słupkami, pola akcentu, maszty flag / totem / maszt kratowy z owalem bez napisów, szyld funkcyjny) na LOD0 i LOD1; haki w buildings_mesh.build (+ override bloków: wall_material, balconies, bands). 4 wpisy `g3b-frontage-*` w overrides.yaml. Testy: tests/gis/test_g3b_frontage.py 8 passed, 1 skipped (QA po przebudowie).
NASTĘPNY KROK: `pwsh artifacts/g3b-frontage/run-cycle.ps1 -Name after1 -Tag 1` (po zakończeniu baseline), potem `bash artifacts/g3b-frontage/make-pairs.sh after1`
