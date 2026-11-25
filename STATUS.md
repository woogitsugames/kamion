# STATUS — agent seams-w10 (analiza FAIL szwów fali 10)

- [krok 1] Raport fali 10 == fala 9 (diff identyczny), zestaw FAIL stały od fali 2 po ADR 0310 (21.11 04:12). Narzędzie liczy z grafu + overrides w gicie (derived:network), więc przebudowa kafli nie zmienia wyniku. Fala 11 (e9e03c56f) nie zmienia tools/worldgen ani grafów/overrides → jej raport szwów będzie identyczny z falą 10.
- [krok 2] 9 FAIL "położenie osi na szwie" = D94 gameplay_widen: przesunięcie osi liczone osobno w każdym kaflu; seam_taper wyrównywał szerokość, nie oś.
- [krok 3] 7 FAIL "pobocze" = assign_sides na kontekście przyciętym do bbox + przycięcia skrzyżowań (2. przebieg) na krótkich łańcuchach przy szwie — tylko propozycja.
- [krok 4] Poprawka w roads/seam_taper.py (+ etykieta w qa/seams.py), test tests/gis/test_seam_axis_w10.py. Testy: test_seam_axis_w10 + test_seam_taper_0275 28 passed; seams_0224/seams_fix_s23/dk65_seam_knyszyn_0233/dk8_seam_cli/effective_graph_readers/road_widen_0306 101 passed, 2 skipped.
- [krok 5] Pełny seams (20 szwów): FAIL 18 → 7 (tylko pobocza), UWAGA 11 → 6. Dowód: artifacts/seams-w10-s24/seams_after_fix.{md,json} (też w main artifacts/).
- Następny krok (lider): review + merge; po merge przebudowa kafli z szwami miejskimi i dk65-04/05/06 (`uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region <id>`), potem pass na pobocza (handshake boków na szwie).
