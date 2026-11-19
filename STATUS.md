# STATUS road-widen-s24 (D94, ADR 0306)

- Krok 1: `standards.GAMEPLAY_LANE_WIDEN_M = 0.25` (GAMEPLAY_WIDEN, nie pomiar), `network.gameplay_widen` po wszystkich
  overrides w `network.load`; `compact_roundabout.specs`: `lane_w_m` + delta. maczka: każda sekcja +0,25 m/pas (dev 0,0).
- NASTĘPNY KROK: narzędzie toru zestawu `tools/worldgen/qa/combo_lane_check.py` + raport przed.
- Krok 2: `qa/combo_lane_check.py` (tor zestawu: oś przednia na środku pasa + opcjonalnie najlepszy „swing” kierowcy w
  obrębie własnego pasa; klasy opposite/kerb/apron/off_hard, szwy pomijane) + `qa/combo_topview.py` (rzut z góry).
  Przed (main, widen 0, wszystkie korytarze, bez swing): opp 324, kerb 1782, apron 378, off_hard 792 (w tym artefakty szwów).
- NASTĘPNY KROK: `uv run --project tools/worldgen python tools/worldgen/qa/combo_lane_check.py --widen 0 --swing --out artifacts/road-widen-s24/before/combo_swing.json`
- Krok 3/4 (WIP): reguły w generatorze: `network.curve_widen` (pasy dwukierunkowe GP/G/Z na łukach R<200 m, offtrack
  zestawu, ≤1 m/pas), `compact_roundabout.TRUCK_ENTRY_R_MIN_M 12 / TRUCK_EXIT_R_MIN_M 15`, ring +0,25, `lane_w_m` +0,25.
  knyszyn przebudowany r1 (przed scaleniem main z ADR 0304); main scalony (a464ac123) — kafle trzeba przebudować ponownie.
- NASTĘPNY KROK: `pwsh -File artifacts/road-widen-s24/rebuild.ps1 -Regions knyszyn,bialystok-kleeberga,dk65-05,tykocin -Tag r2`
- 11:5x: testy 0274/0301 na geometrii zmierzonej (`GAMEPLAY_LANE_WIDEN_M=0` wyłącza wszystkie reguły D94), 101 zielonych.
  r2 (knyszyn, tykocin, dk65-05, kleeberga, po merge main) w toku. Zlecenie lidera: fantomowa wyspa C (11_dk8, xy -549.8/218.9,
  między jezdniami trunk w197904074 | w266084696, ortho_road_frac 0,654 ≥ 0,6) — analiza w toku (fidelity zoom).
- NASTĘPNY KROK: po r2 `combo_lane_check --swing` na 4 kaflach; import Win64 + VQA (`pwsh -File artifacts/road-widen-s24/unity.ps1 -Tag after -Import knyszyn`).
- 12:2x: knyszyn po r2: DK65→DW671 W środek pasa kerb 23→15, off 5→0; ze swingiem 0→11 (krawężnik narożnika SE przy wlocie
  z płd. — narożniki zamykane NOSE_R_M 4 m). Dodane `TRUCK_CORNER_R_M 12` (kształt jak zdjęcie drona 9). Kolejka:
  r2 (tykocin, dk65-05, kleeberga) → r3 (knyszyn, knyszyn-s, knyszyn-w) → r4 (C + fidelity). Unity: import knyszyn r2 + VQA (`unity-after`).
- NASTĘPNY KROK: po r3 `combo_lane_check --swing --tiles knyszyn,...`, import r3 knyszyn + VQA (`unity.ps1 -Tag after2 -Import knyszyn,knyszyn-s,knyszyn-w`).
