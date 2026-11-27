# STATUS neon-avenue-s24 (szpalery drzew przy drodze — koniec „klonów bliźniaków”, dopisek ADR 0352)

- Worktree `neon-avenue-s24`, gałąź `neon-avenue-s24`. Nie scalane ani nie pushowane.
- Środowisko: prywatne kopie `Data/raw/derived/{knyszyn-w,dk65-07}` (pozostałe kafle junction do main, bez zapisu do main), Win64 `game/Library` lokalnie.
- [krok 1] Import bazowy Win64 (`knyszyn-w`, `dk65-07`) + rendery PRZED (`before`, High PC 1920×1080, `clear` + `overcast`, 10 kamer `knyszyn-w` + 6 kamer `dk65-07` = 32 PNG) w `artifacts/neon-avenue-s24/before/`.
- [krok 2] Implementacja w `tools/worldgen/streetscape/tree_rows.py` i `tools/worldgen/streetscape/vegetation.py` (commit `fb6c4e06e`):
  - Zmienność wieku/skali `0.70–1.15 × href_m`, brak powtarzania wariantu modelu (`v0/v1/v2`) na sąsiednich drzewach tego samego gatunku, separacja obrotu `yaw >= 1.05 rad` (~60°), pochylenie `0.005–0.065 rad`.
  - Przesunięcia wzdłuż (`10–16 m` BDOT / `12–18 m` `tree_rows`) i w poprzek (`σ = 1.0–1.05 m`, clamp `±2.5 m`), przerwy (`missing_share` 0.16–0.18), pojedyncze młode nasadzenia/samosiejki w ~35% luk (`birchyoung`/`linden`/`maple`/`shrub` 2–8,2 m), domieszka gatunków z dębem (`linden`/`maple`/`oak`/`birch`/`alder`). Zero nowych prototypów.
- [krok 3] Przebudowa `knyszyn-w` i `dk65-07` w prywatnej kopii `Data/raw/derived/`, import Win64, rendery PO (`after`, High PC 1920×1080, `clear` + `overcast`, 32 PNG) oraz porównania SBS ≤ 960 px (`artifacts/neon-avenue-s24/sbs/`), skopiowane do `C:\Users\matma\Documents\Claude\kamion\artifacts\neon-avenue-s24\`.
  - `knyszyn-w`: `treerow` 85 → 88 (16 luk, 4 `replants`, 26 dębów, h `11.2–18.9` → `2.4–19.5 m`), `total_trees` 11 360 → 11 327 (−33), `violations_after: 0`; visual-QA High: `scene_draws` −1..+0, `scene_tris` −25 954..−5 216, `inst_draws` −1..+7 (dąb ADR 0352 względem derived main z 17.11), `inst_tris` −104..+2 986.
  - `dk65-07`: `treerow` 18 → 17 (4 luki, 2 `replants`, 11 dębów, h `11.2–18.8` → `3.7–17.8 m`), `total_trees` 166 578 → 166 534 (−44), `violations_after: 0`; visual-QA High: `scene_draws` −1..+0, `scene_tris` −13 876..−10 860, `inst_draws` +0..+2, `inst_tris` −84..+728.
- [krok 4] Testy:
  - `test_budget_0221.py`, `test_typology_0238.py`, `test_world_v31.py`, `test_hero_bridge.py`: **62 passed**.
  - `test_treerows_0222.py`, `test_trees_0308.py`, `test_trees_0352.py`, `test_trees_0347.py`: **73 passed, 1 failed** (`test_profile_table_matches_the_glb` — pre-existing różnica CRLF vs LF w hashu `trees_meta.json`, 29/29 prototypów identycznych; wszystkie 28 kafli korytarza ADR 0347 przeszły).
- [krok 5] Dopisek do `docs/adr/0352-drzewa-gatunki-tint-per-drzewo-dab.md`, cofnięty efekt uboczny Unity (`game/Assets/Resources.meta`), commit końcowy na `neon-avenue-s24`.
- GOTOWE DO SCALENIA PRZEZ LIDERA.
- NASTĘPNY KROK (lider): przejrzeć diff na `neon-avenue-s24` i dowody w `artifacts/neon-avenue-s24/sbs/`, scalić gałąź, a następnie w kolejnej fali regeneracji przebudować kafle z szpalerami (`knyszyn-w`, `dk65-01..11`, `dw671-tykocin-*`, `dk65-monki-*`):
  `git merge --no-ff neon-avenue-s24`

## codex-roofs-s24 — dachy budynków gospodarczych r4
- Krok 1. Odczytano zasady, ADR 0238 i uwagę krytyka. Kafel dk65-07 skopiowano do prywatnego Data/raw/derived.
- Następny krok w slocie heavy: `& $py tools/worldgen/roads/build_world.py --region dk65-07 --context` (stan bazowy r3).
- Krok 2. Generator koduje wariant i ziarno w COLOR_0 w obu LOD-ach. Zachowano podział na materiały r3 oraz jawne override pokrycia. Dodano testy kodowania, pokrycia płaskiego i override.
- Następny krok po eksporcie stanu bazowego: `pwsh artifacts/codex-roofs-s24/run-vqa.ps1 -Phase before`.
- Krok 3. Stan PRZED wyeksportowany z kodu r3: 64 chunki, 430 MiB High i 167 MiB Low. Manifest i log dołączone do dowodów.
- Następny krok: `pwsh artifacts/codex-roofs-s24/run-vqa.ps1 -Phase before`.
- Krok 4. Zapisano decyzję r4 w ADR 0238, odniesienie do ortofoto GUGiK oraz wagi WORKING_VALUE. Import bazowy przygotowuje zestawy PBR w worktree.
- Następny krok po renderach PRZED: zastosować poprawkę shaderów i uruchomić `& $py -m pytest tests/gis/test_rural_outbuildings_props_fix_s24.py -q` w slocie heavy.

- Krok 5. Zapisano implementację obu shaderów i importu w commicie WIP. Do zakończenia renderów PRZED pliki Unity na dysku celowo pozostają w wersji r3. Win64 import r3 zwrócił IMPORT_RESULT: OK. Ponowny visual-qa na nazwie sceny World_dk65-07_High czeka na slot heavy.
- Następny krok po dwóch udanych renderach PRZED: `git checkout -- game/Assets/_Project/Environment/Shaders/WorldPBR.shader game/Assets/_Project/Rendering/Shaders/WorldSurface.shader game/Assets/_Project/World/Import/RegionImporter.cs`, potem `pwsh artifacts/codex-roofs-s24/run-world-after.ps1`.
- Krok 6. Win64 r3 oraz High PC clear i overcast zakończone. Osiem PNG i dwa stats.txt są w before. Włączono na dysku shadery r4 z WIP.
- Następny krok: `pwsh artifacts/codex-roofs-s24/run-after.ps1`.
- Krok 6a. Pierwszy pytest dał 15 PASS i 1 błąd nowej asercji. Test rozróżnia teraz znaczniki połaci od domyślnych zer współdzielonego submesha i sprawdza pokrycie obu LOD-ów.
- Następny krok: `pwsh artifacts/codex-roofs-s24/run-after.ps1`.
- Krok 7. Prototyp r4 wyeksportowany w prywatnym dk65-07. Manifest i log są w katalogu after.
- Następny krok w slocie heavy: `pwsh artifacts/codex-roofs-s24/run-vqa.ps1 -Phase after`.
