# Rozszerzenie zakresu fali 15 o poprawki propsów na jezdni (`agy-wave15-props-s25`)

**Gałąź:** `agy-wave15-props-s25` · **Data:** 2026-11-28 · **Bez Unity / bez regeneracji kafli**

---

## 1. Wynik i zakres zmian

Na podstawie `git diff main...agy-props-carriageway-s25` oraz `C:\Users\matma\Documents\Claude\kamion\artifacts\agy-props-carriageway-s25\WYNIKI.md` przeskanowano w pamięci wszystkie **54 kafle** w `Data/raw/derived/<kafel>/world/` (`road_carriage.wkt` + `instances_*.json`) oraz wywołano w pamięci zaktualizowane `furniture.clear_carriageway` z gałęzi `agy-props-carriageway-s25` na kandydatach. Sprawdzono też wszystkie `overrides.yaml` pod kątem `depot_gate` oraz `plantings` (`override:*:island`) używanych przez `meshing.cull_sides_on_carriageway`.

1. **Ustalono dokładnie 11 kafli**, w których poprawki `agy-props-carriageway-s25` zmieniają wynik generatora Pythona:
   - **4 kafle już obecne w `queue.csv`:** `bialystok-mickiewicza` (+3 przesunięte), `bialystok-bojary` (+5 przesuniętych), `bialystok-industrial-c` (+1 przesunięty `sign_post` oraz zachowanie `collision_curb` wysepki `override:kwadrat-park-gate-kit:island`), `dk65-04` (+1 przesunięty `signal_rail_saltire_g3` na `+5,47 cm` wewnątrz jezdni).
   - **7 kafli brakujących w `queue.csv` (dopisano):** `bialystok-wygoda` (2 × `sign_post`), `bialystok-kleeberga` (1 × `sign_post`), `bialystok-maczka` (1 × `sign_post`, 1 × `bollard`), `bialystok-knyszynska` (1 × `sign_post`), `bialystok-krywlany` (1 × `lamp_10m`), `dk65-02` (2 × `signal_rail_saltire_g3`: 1 przesunięty, 1 usunięty), `s8-03` (1 × `lamp_old_steel_8m`).
   - **Dlaczego 11 zamiast 8 z raportu `agy-props-carriageway-s25`:** tam przetestowano w pamięci 10 kafli zgłoszonych przez Unity w `*-props-on-road.txt` (ograniczenie do korytarza trasy, bez `tier: high`, po raycaście w `col_asphalt`). Skan wszystkich 54 kafli z `Data/raw/derived` potwierdził 0 zmian w `bialystok-dojlidy` i `bialystok-porosly` oraz wykrył 3 dodatkowe kafle z obiektami wewnątrz `road_carriage.wkt` (`bialystok-wygoda`, `bialystok-krywlany`, `dk65-04`).
   - **Kolizja wysepki bramowej (`meshing.cull_sides_on_carriageway`):** `depot_gate` występuje wyłącznie w `bialystok-industrial-c`, a wyspy `plantings` w `bialystok-dojlidy`, `bialystok-industrial-c` i `knyszyn` nie przecinają `road_carriage.wkt`.

| Kafel | Status w `queue.csv` przed | Zmiana w generatorze (`agy-props-carriageway-s25`) | Zmodyfikowane obiekty (pomiar w pamięci) |
| --- | --- | --- | --- |
| `bialystok-mickiewicza` | był (A) | `clear_carriageway`: 3 przesunięte | `sign_post` × 2 (`2,43 cm`, `3,33 cm`), `lamp_10m` × 1 (`5,45 cm`) |
| `bialystok-bojary` | był (B) | `clear_carriageway`: 5 przesuniętych | `bollard` × 2 (`0,18 cm`, `0,07 cm`), `lamp_11m` × 1 (`0,30 cm`), `sign_post` × 2 (`5,19 cm`, `0,14 cm`) |
| `bialystok-industrial-c` | był (C → D) | `clear_carriageway`: 1 przesunięty + `cull_sides_on_carriageway` | `sign_post` × 1 (`3,58 cm`) + `collision_curb` wyspy `kwadrat-park-gate-kit:island` (`override:putry-ring-s-approach-signal-mast` zachowany na `on_authored_island`) |
| `dk65-04` | był (D) | `clear_carriageway` + `signal_rail`: 1 przesunięty | `signal_rail_saltire_g3` × 1 (`5,47 cm`) |
| `bialystok-wygoda` | **dopisany (C)** | `clear_carriageway`: 2 przesunięte | `sign_post` × 2 (`2,36 cm`, `4,84 cm`) |
| `bialystok-kleeberga` | **dopisany (D)** | `clear_carriageway`: 1 przesunięty | `sign_post` × 1 (`1,21 cm`) |
| `bialystok-maczka` | **dopisany (E)** | `clear_carriageway`: 2 przesunięte | `sign_post` × 1 (`3,28 cm`), `bollard` × 1 (`0,23 cm`) |
| `bialystok-knyszynska` | **dopisany (E)** | `clear_carriageway`: 1 przesunięty | `sign_post` × 1 (`4,27 cm`) |
| `bialystok-krywlany` | **dopisany (E)** | `clear_carriageway`: 1 przesunięty | `lamp_10m` × 1 (`2,78 cm`) |
| `dk65-02` | **dopisany (E)** | `clear_carriageway` + `signal_rail`: 1 przesunięty, 1 usunięty | `signal_rail_saltire_g3` × 2 (`1,918 m` przesunięty, `0,71 cm` usunięty bo kierunek `new` wracał w jezdnię) |
| `s8-03` | **dopisany (E)** | `clear_carriageway`: 1 przesunięty | `lamp_old_steel_8m` × 1 (`5,28 cm`) |

---

## 2. Zbalansowanie `queue.csv` (19 → 26 kafli)

Wszystkie 26 kafli zbalansowano metodą malejących wag `build_s` przydzielanych do najkrótszego dotąd łańcucha (A–E):

| Łańcuch | Kafle | `build_s` [s] | `total_s` [s] | Czas `build_s` / `total_s` |
| --- | ---: | ---: | ---: | --- |
| A | 1 | 11 183 | 12 288 | 186,4 min / 204,8 min (`3 h 25 min`) |
| B | 2 | 10 327 | 11 685 | 172,1 min / 194,8 min (`3 h 15 min`) |
| C | 4 | 10 309 | 11 425 | 171,8 min / 190,4 min (`3 h 10 min`) |
| D | 9 | 10 139 | 12 989 | 169,0 min / 216,5 min (`3 h 36 min`) |
| E | 10 | 10 288 | 13 282 | 171,5 min / 221,4 min (`3 h 41 min`) |
| **RAZEM** | **26** | **52 246** | **61 669** | **14 h 31 min / 17 h 08 min** |

- Zaktualizowano [`artifacts/regen-wave-15-s25/scope.csv`](../regen-wave-15-s25/scope.csv) (dopisano powody dla 7 nowych kafli oraz uzupełniono powody dla 4 kafli z pierwotnej kolejki).
- Zaktualizowano [`artifacts/regen-wave-15-s25/README.md`](../regen-wave-15-s25/README.md): sekcja `## Zakres`, sekcja `## Czasy`, kroki scalenia gałęzi `agy-props-carriageway-s25` i `agy-prop-colliders-s25` w `## Uruchomienie przez lidera`, uwaga o pełnym reimporcie kolizji placów bez regeneracji Pythona oraz osobny wariant **reimport-only** dla 28 kafli spoza fali 15 (lub 54 kafli przed buildem #11, szacunek `~54 × 5 min ≈ 4 h 30 min` / `~28 × 5 min ≈ 2 h 20 min` `WORKING_VALUE`).

---

## 3. Weryfikacja

- `pwsh -NoProfile -File artifacts/regen-wave-15-s25/chain.ps1 -Chain A..E -WhatIf`: wszystkie 5 łańcuchów (26 kafli) przeszły walidację `common.ps1` i planowanie kolejek (`exit 0`).
- `pwsh -NoProfile -File artifacts/regen-wave-15-s25/chain.ps1 -Tile dk65-04 -WhatIf`: `exit 0`.
- Testy budżetowe przez `wgpy.cmd`:
  - `tests/gis/test_budget_0221.py` + `tests/gis/test_world_v31.py` + `tests/gis/test_hero_bridge.py`: **35 passed** (2,68 s).
  - `tests/gis/test_typology_0238.py`: wszystkie **27 passed** (uruchomione w podzbiorach `-k` po zmianach).

---

## 4. Czego nie zrobiono i następny krok lidera

- **Nie uruchamiano Unity ani `build_world` / `far_field`** (fala 14 w toku; praca wyłącznie na plikach planu fali 15 i odczycie w pamięci z `Data/raw/derived`).
- **Następny krok lidera:** po zakończeniu fali 14 zintegrować `regen-wave-14-s25`, `codex-seam-steps-s25`, `agy-poles-wires-s25`, `agy-props-carriageway-s25`, `agy-prop-colliders-s25` oraz przywrócić `artifacts/regen-wave-15-s25/` z gałęzi `agy-wave15-props-s25` (wg instrukcji w `artifacts/regen-wave-15-s25/README.md`).
