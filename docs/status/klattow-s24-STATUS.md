# STATUS klattow-s24 (Dom Klattów, ADR 0305)

- 10:40 Generator `streetscape/knyszyn_dom_klattow_0305.py` (hero budynku BDOT 2F22) + materiały `log_wall_white`,
  `wood_planks_white`, `wood_planks_stain`, `wood_trim_brown`, `roof_tiles_old`, `fieldstone_plinth`; zestawy proceduralne
  `log_whitewash`, `fieldstone` (bez pobrań). Test na sucho: LOD0 4368 tris, LOD1 99. Kamera `look_dom_klattow_street`.
  Podgląd Blender: `artifacts/klattow-s24/preview/`. Baseline (import + render 2 kamer) w toku: `artifacts/klattow-s24/before.status`.
  NASTĘPNY KROK: `pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner klattow-s24; uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region knyszyn; pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner klattow-s24; pwsh artifacts/klattow-s24/run-vqa.ps1 -Tag r1`
- 10:45 Testy `tests/gis/test_dom_klattow_0305.py` (6) + powiązane: 43 passed. Płot: pas między ścianą a sztachetami musi być
  wolny od obrysu drogi (test znalazł błąd pierwszej wersji). Nadpisanie `look-lamus-plebanski` (BDOT 6fe1, klattow-02) + kamera
  `look_lamus_plebanski`; fallback Domu Klattów = `wood_planks_white`. Baseline nadal w imporcie.
  NASTĘPNY KROK: po `artifacts/klattow-s24/before.status` z `exit=0`: build_world knyszyn (slot heavy) → `pwsh artifacts/klattow-s24/run-vqa.ps1 -Tag r1 -Cameras look_dom_klattow,look_dom_klattow_street,look_lamus_plebanski`
- 11:15 Baseline (main, High clear, edytor): `look-dom-klattow` 600 draws / 865 370 tris; `-street` (11,5 m) 515 / 846 659; `-gable-e` 204 / 405 989;
  `-yard` (stara pozycja, za płotem) 72 / 149 474; `look-lamus-plebanski` 552 / 889 748 (`artifacts/klattow-s24/before2/`). Nadpisanie
  `plot_fence` (styl płotu działki z nadpisania domu) — płot działki Klattów = sztachety. Runda r1 czeka w kolejce slotu heavy;
  EditMode Win64 w toku (`artifacts/klattow-s24/editmode.status`).
  NASTĘPNY KROK: po `artifacts/klattow-s24/r1.status` z `exit=0`: `bash artifacts/klattow-s24/sbs.sh r1` i obejrzeć `artifacts/klattow-s24/sbs/*-r1.jpg`
- 12:15 Runda 1 obejrzana (High = scena `World_knyszyn_High`; wcześniejsze rendery `*-low` to treść Low — scena `World_knyszyn`).
  `look-dom-klattow` High: 615 → 623 draws, 1 481 809 → 1 486 527 tris (przed = `artifacts/knyszyn-p2-s24/stats-after5.txt`, stan main).
  Poprawki do rundy 2: zestawy `roof_tiles_old`, `boards_painted`, `wood_shingles`; lamus jako obiekt autorski; płot na linii czoła
  ganku (na modelowanym chodniku, gdy zostaje ≥ 1,4 m); pas trawy za płotem; `plot_canopy_exclude` (cień domu = 8 „koron”).
  UWAGA: `Data/raw/derived` w tym worktree to teraz KATALOG z junctionami + prywatna kopia `knyszyn` (road-widen-s24 budował
  knyszyn równolegle do tego samego katalogu main) — przed usunięciem worktree odpiąć KAŻDY junction `cmd /c rmdir`, nie `-Recurse`.
  Runda 2 w kolejce slotu heavy (`artifacts/klattow-s24/r2.world.status`).
  NASTĘPNY KROK: po `artifacts/klattow-s24/r2.status` z `exit=0`: `bash artifacts/klattow-s24/sbs.sh r2`; obejrzeć `artifacts/klattow-s24/sbs/*-r2.jpg`
