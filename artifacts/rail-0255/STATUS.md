# rail-0255 — oznakowanie dojazdu do przejazdów (§ 79), chmura s21/s22
- Gałąź `claude/awesome-fermi-3s2wdi` na `rail-fix-s21` @ ac928dd32. ADR 0255 (numer do ewentualnej zmiany przez lidera).
- Zrobione: rail_approach.py (plan), rail_signs.py (tarcze), rail_props.place_approach + U-1, haczyki w gate3_landmarks/stage/rail/build_world; 20 testów.
- Testy: test_rail_approach_0255 20/20, test_rail_0217 + import 32/32; podzbiór gate3/sign/landmark/furniture/rail/prop 270 passed.
- Nie zrobione (brak Data/raw, Unity): build_world dw671-tykocin-01, import, visual-qa, A16.
- NASTĘPNY KROK (lider): `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region dw671-tykocin-01` i przegląd `generated/rail.json` → `approach_qa`.
