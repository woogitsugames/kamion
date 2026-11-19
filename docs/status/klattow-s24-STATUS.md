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
