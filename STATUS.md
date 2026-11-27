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

## codex-sidewalk-var-s24
- Przeczytano zasady i ADR 0237. Kafel Tykocin skopiowano do prywatnego derived; junction do main odłożono pod inną nazwą.
- Następny krok: `pwsh artifacts/codex-sidewalk-var-s24/qa.ps1 before`
- Mechanizm gotowy za flagą regionu. COLOR_0 wybiera skan/pigment, spoiny i naprawy są w shaderze, krawężniki używają UV1 i koloru. Dodano test stabilności i zachowania granicy w jednym prymitywie.
- Następny krok: dokończyć `pwsh artifacts/codex-sidewalk-var-s24/qa.ps1 before`, następnie włączyć flagi w overrides obu miast.
- Dopisano kontrakt wariantów do ADR 0237. Przygotowano testy pod slotem heavy oraz lokalne kopie instancji regionu C potrzebne do bramek.
- Następny krok po renderach: `pwsh artifacts/codex-sidewalk-var-s24/test.ps1`
- Dopasowano skalę tekstury krawężnika do istniejącego zestawu z prefabrykatami metrowymi. Ubytek moduluje też normalną. Obejrzano referencje Commons cs153250600 i cs202183436.
- Następna komenda po zakończeniu kolejki i bazowego przebiegu: `pwsh artifacts/codex-sidewalk-var-s24/qa.ps1 after`
- Włączono odmiany kostki i krawężników dla knyszyn, knyszyn-w i knyszyn-s. W tych kaflach fallback zachowuje kostkę zgodnie z uwagą właściciela.
- Następny krok: zakończyć `pwsh artifacts/codex-sidewalk-var-s24/qa.ps1 before`; potem aktywować Tykocin i uruchomić `pwsh artifacts/codex-sidewalk-var-s24/qa.ps1 after`.
- Bazowy generator wyeksportował 64 chunki High i Low, kopia metryk jest w `artifacts/codex-sidewalk-var-s24/before/`. Bazowy import czeka na slot Unity i czyta zachowany manifest.
- Włączono warianty w danych Tykocina i wpis szarej kostki dla północnej pierzei, na podstawie dwóch zdjęć Commons.
- Następna komenda po bazowym visual-QA: `pwsh artifacts/codex-sidewalk-var-s24/qa.ps1 after`
- Testy z portfela budżetowego, chodników ADR 0237 i Knyszyna D38: 123 passed, 234,44 s. Log w `artifacts/codex-sidewalk-var-s24/pytest.log`.
- Następny krok: po bazowym imporcie i renderach uruchomić `pwsh artifacts/codex-sidewalk-var-s24/qa.ps1 after`.
- Bazowy import Win64 High i visual-QA clear/overcast zakończyły się sukcesem. Zapisano po 10 PNG, logi i statystyki kamer. GLB road High/Low: 192 589 tris i 120 prymitywów.
- Następny krok: `pwsh artifacts/codex-sidewalk-var-s24/qa.ps1 after`
