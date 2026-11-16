# STATUS — D15 seam-taper-0275 (chmura D, runda 5, ADR 0275)
- Krok 1: `tools/worldgen/roads/seam_taper.py` (plan z danych sąsiada w gicie, krzywa S po połowie w każdym kaflu; hw + kody pobocza 0272, gdy `roads.xsec` jest) + haki w `pipeline.build_network` / `build`; `qa/seams.py` + test z `seams-0224` zaktualizowane (przejścia 0275, `lanes_follow_width` 0233, wiersze krawędzi asfaltu ±0,02 m). Na danych main: 5 par przejść (kleeberga|knyszynska ×3, kleeberga|maczka, knyszyn-s|dw671), 0 w DK65; `test_seams_0224.py` 15 passed.
- Krok 2: `tests/gis/test_seam_taper_0275.py` (13 passed + 6 pominiętych bez `roads.xsec`; na próbnym scaleniu z `origin/rail-dk65-s22` 18 passed, 1 pominięty), ADR `docs/adr/0275-przejscia-szerokosci-na-szwach-kafli.md`, raport `docs/reports/SEAMS-2026-11-16.md` (+ `.json`): 20 szwów, 103 drogi, FAIL 39 (`--no-taper`) → 19, PRZEJŚCIE 10; szew `dk65-11`|`knyszyn-s` po rail-dk65-s22: krawędź asfaltu 3,65|3,38 → 3,52|3,52 m.
- Krok 3: scalone `origin/main` feb542757 (rail-dk65-s22 + 0272); `seam_taper` na `roads.xsec` wprost; `-k "seam or taper or 0275 or 0224"`: 92 passed, 13 skipped; seams na aktualnych danych: FAIL 43 (`--no-taper`) → 19, PRZEJŚCIE 11; `dk65-11`|`knyszyn-s` krawędź asfaltu 3,65|3,38 → 3,52|3,52 m; rampa w `dk65-06`.
- NASTĘPNY KROK (lider, po scaleniu PR): `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region <dk65-06|dk65-11|knyszyn-s|dw671-tykocin-01|bialystok-kleeberga|bialystok-knyszynska|bialystok-maczka>` → `uv run --project tools/worldgen python -m tools.worldgen.qa.seams --md artifacts/seam-taper-0275/seams.md` → `pwsh scripts/import-region.ps1 -Region <id> -Build` → `pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier High -Lighting clear -Cameras seam_w_top40,seam_w_drive -OutputDir artifacts/seam-taper-0275/vqa/dk65-11`.

# STATUS — G5 summer-cd-0216b (chmura G, rozszerzenie ADR 0216, D68)
- Krok 1: profile `summer-bialystok-cd` + `led-white-4000k-bialystok` (C, Dojlidy) w `Data/Regions/lighting_profiles.json`; NOAA `tools/worldgen/qa/sun_noaa.py` (31 VII −6° 21:06/311,4°; 20 VIII 20:22/299,7°).
- Krok 2: LED głowice tylko na 10 ulicach Dojlid z TED 769998-2024 (override `lamp-policy-led-tender-0216b`, 64 way); C bez zmian (`lamp-policy-unverified-0216b`); generator `furniture.chain_lamp_proto` + `lamp_led_scope`; audyt `tools/worldgen/qa/lamp_family_audit.py`.
- Krok 3: pytest `tests/gis/test_summer_cd_0216b.py` + `test_lamp_led_0216.py` 19 passed; EditMode zaktualizowany (nieuruchomiony); ADR 0216 §0216b.
- NASTĘPNY KROK (lider, po 0221): komendy w `docs/adr/0216-lato-i-biale-led-dk65-knyszyn.md` §0216b „Komendy dla lidera” (build_region → build_world → import-region → visual-qa → EditMode → APK A16).

# STATUS — world2-finish
- Krok 1: VQA przejrzane (uwagi w artifacts/live/world2-finish.md). Krok 2a: materials_spec cofnięty (png_bytes artefakt), nav route.bytes zacommitowane.
- NASTĘPNY KROK: git merge origin/main (generated=ours, region_catalog -> export-region-catalog.py, ADR README -> tools/docs/adr_index.py)
# STATUS — D42 physics-determinism-s23

- Przyczyna flake'a: `TouchSteeringTests.Residual_PlateFrictionSweep_Diagnostic` zmieniał wspólny `ScenarioRunner.Defs` (fifthWheel.plateFrictionCreepRateDegS), a xUnit równolegle uruchamiał kombinacje laden40. Naprawa: każdy przebieg ma prywatny DefinitionSet, Defs jako Lazy, 2 testy regresji.
- Naczepa: `park_brake_hold_no_interlock` 55,2 mm to przeciek relaksacji (4 mm/s bez końca), nie 7,63 m. Poprawka w TrailerModel: 14,4 mm (ustala się).
- Pętle: provoke 198/200 → 0/200; Robustness 0/200 → 0/200; pełny zestaw 0/30 → 0/30 (289/289).
- NASTĘPNY KROK: lider: `pwsh scripts/test.ps1 -Platform EditMode` (TrailerModel.cs współdzielony z Unity), potem scalenie PR.
