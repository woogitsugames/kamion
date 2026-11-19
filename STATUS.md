# STATUS road-widen-s24 (D94, ADR 0306)

- Krok 1: `standards.GAMEPLAY_LANE_WIDEN_M = 0.25` (GAMEPLAY_WIDEN, nie pomiar), `network.gameplay_widen` po wszystkich
  overrides w `network.load`; `compact_roundabout.specs`: `lane_w_m` + delta. maczka: każda sekcja +0,25 m/pas (dev 0,0).
- NASTĘPNY KROK: narzędzie toru zestawu `tools/worldgen/qa/combo_lane_check.py` + raport przed.
