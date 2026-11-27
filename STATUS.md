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

## codex-main-verify-s24 — 2026-11-27

- Punkt startowy `c8ca07835`. Przeczytane instrukcje i ADR 0332, 0335, 0340 (dopisek 2), 0349. Worktree czysty przed dopiskiem.
- Następny krok: `pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner codex-main-verify-s24`, następnie `pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64`.
- Przygotowano prywatne kopie danych zapisywanych przez testy GIS (kafel `bialystok-industrial-c`, cache i BDOT). Pozostałe kafle dostępne jako wejścia przez junctiony.
- Następny krok po EditMode: `pwsh scripts/test.ps1 -Platform PlayMode -BuildTarget Win64`.
- EditMode Win64: 1641 testów, 1491 zaliczonych, 150 pominiętych, 0 błędów i niejednoznacznych. Kod 0, 508,08 s z importem. XML: `tests/editmode-20261127-162619.xml`.
- Następny krok: `pwsh scripts/test.ps1 -Platform PlayMode -BuildTarget Win64`.
- PlayMode Win64, przebieg bazowy: 224 testy, 183 zaliczone, 23 błędy, 18 pominiętych, 392,16 s. XML: `tests/playmode-20261127-163509.xml`. 22 błędy po braku wygenerowanego TRAKT (NRE w `VehicleBody.Initialize`); 1 po braku mapy nawigacji Krywlany.
- Następny krok: `& $python tools/ui/build_nav_map.py --region bialystok-krywlany` oraz pod slotem heavy `pwsh scripts/build-lab.ps1 -SkipAudio -BuildTarget Win64`.
- Wygenerowano brakującą mapę KNAV Krywlany z istniejących danych regionu (95 973 B, 452 drogi, 689 budynków, 617 punktów trasy) i zapisano metadane wygenerowane przez Unity. Wszystkie 44 unikalne kafle korytarzy mają oba zasoby na dysku.
- Następny krok po generatorze DrivingLab: przywrócić uboczne modyfikacje plików śledzonych przez Git, następnie `pwsh scripts/test.ps1 -Platform PlayMode -BuildTarget Win64`.
