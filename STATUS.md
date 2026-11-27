# STATUS neon-avenue-s24 (szpalery drzew przy drodze — koniec „klonów bliźniaków”, dopisek ADR 0352)

- Worktree `neon-avenue-s24`, gałąź `neon-avenue-s24`. Nie scalane ani nie pushowane.
- Środowisko: prywatne kopie `Data/raw/derived/{knyszyn-w,dk65-07}` (pozostałe kafle junction do main, bez zapisu do main), zbudowany brakujący zestaw PBR `sandstone_weathered_tint`, Win64 `game/Library` lokalnie.
- [krok 1] Import bazowy Win64 (`knyszyn-w`, `dk65-07`) + rendery PRZED (`before`, High PC 1920×1080, `clear` + `overcast`, 10 kamer `knyszyn-w` + 6 kamer `dk65-07` = 32 PNG) w `artifacts/neon-avenue-s24/before/`.
- [krok 2] Implementacja w `tools/worldgen/streetscape/tree_rows.py` i `tools/worldgen/streetscape/vegetation.py`:
  - Zmienność wieku/skali `0.70–1.15 × href_m`, brak powtarzania tego samego wariantu modelu (`v0/v1/v2`) na sąsiednich drzewach tego samego gatunku, separacja obrotu `yaw >= 1.05 rad` (~60°), pochylenie `0.005–0.065 rad`.
  - Przesunięcia wzdłuż (`10–16 m` BDOT / `12–18 m` `tree_rows`) i w poprzek (`σ = 1.0–1.05 m`, clamp `±2.5 m`), przerwy (`missing_share` 0.16–0.18), pojedyncze młode nasadzenia/samosiejki w ~35% luk (`birchyoung`/`linden`/`maple`/`shrub` 2–8,2 m), domieszka gatunków z dębem (`linden`/`maple`/`oak`/`birch`/`alder`). Zero nowych prototypów.
- [krok 3] Testy zielone: `test_treerows_0222.py`, `test_trees_0308.py`, `test_trees_0352.py` (+ nowy test `test_avenue_rows_break_twin_clones_and_stay_within_library_and_clearance`), `test_budget_0221.py`, `test_typology_0238.py`, `test_world_v31.py`, `test_hero_bridge.py` → **99 passed**.
- NASTĘPNY KROK: zająć slot `heavy`, przebudować `knyszyn-w` i `dk65-07` w prywatnej kopii `Data/raw/derived/`, potem zaimportować Win64 i wyrenderować `after` (`clear` + `overcast`):
  `pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner neon-avenue-s24`
