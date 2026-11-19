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
