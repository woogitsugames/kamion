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

## codex-mirror-right-s24
- Krok 1. Przeczytano zasady, ADR 0340 i zidentyfikowano trzy gotowe kamery HUD DrivingLab. Gałąź startuje z czystego drzewa.
- Następny krok: pwsh scripts/visual-qa.ps1 -Scene DrivingLab -BuildTarget Win64 -Pc -Tier High -Width 1920 -Height 1080 -Lighting clear -Cameras 'cab-view-0-fov55-hud,cab-view-b-fov70-hud,cab-view-c-fov75-hud' -OutputDir artifacts/codex-mirror-right-s24/before/clear
- Krok 2. Zapisano bazowe DrivingLab Win64 PC High, 1920 × 1080: 6 PNG (FOV 55/70/75 × clear/overcast) w `artifacts/codex-mirror-right-s24/before/`. Cofnięto zapis QualitySettings z Unity.
- Następny krok: git diff -- game/Assets/_Project/Camera/MirrorWindowLayout.cs game/Assets/_Project/UI/Driving/DrivingHud.cs
- Krok 3. Dodano rezerwę przy fizycznej krawędzi i symetryczne przedłużenie istniejących dwóch członów. Dodano przypadki 55/70/75°, przejścia przez krawędź i asymetrii safe area.
- Następny krok: pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64
- Krok 4. Pierwsze kadry odrzucone po obejrzeniu PNG: brakujący prefab TRAKT (GUID 4cd4c98f4f348194ea87e419fbf570d6). Eksport FBX jest w worktree. Test PlayMode GC objął ruch rzutu prawego słupka.
- Następny krok: Invoke-UnityBatch -BuildTarget Win64 -LogFile artifacts/logs/truck-codex-mirror-right-s24.log -Arguments @('-executeMethod','Game.Editor.Setup.TruckAssetBuilder.BuildBatch')
- Krok 5. EditMode Win64 przed dobudowaniem prefabu: 1496 zielonych, 0 niepowodzeń, 150 pominiętych. Generator utworzył prefab TRAKT w Assets/_Generated tego worktree.
- Następny krok: pwsh scripts/visual-qa.ps1 -Scene DrivingLab -BuildTarget Win64 -Pc -Tier High -Width 1920 -Height 1080 -Lighting clear -Cameras 'cab-view-0-fov55-hud,cab-view-b-fov70-hud,cab-view-c-fov75-hud' -OutputDir artifacts/codex-mirror-right-s24/before/clear
- Krok 6. Odtworzono 12 pełnych kadrów TRAKT na tej samej scenie (przed/po × FOV 55/70/75 × clear/overcast). Statystyki geometrii 3D identyczne. Zestawienia PNG w katalogu dowodów.
- Następny krok: pwsh scripts/test.ps1 -Platform PlayMode -BuildTarget Win64 -Filter Game.Tests.PcHudGc0244Tests
- Krok 7. Obejrzano zestawienia clear/overcast (960 × 870) i zbliżenia. Visual-critic PASS 6/6. Dowody skopiowane do katalogu nadrzędnego, decyzja i liczby sceny 3D zapisane w dopisku 3 ADR 0340.
- Następny krok: pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64
- Krok 8. Cztery bramki budżetowe GIS na wskazanym interpreterze: 62/62 w 90,64 s. Log `gis-tests.txt` w lokalnym i nadrzędnym katalogu dowodów.
- Następny krok: pwsh scripts/test.ps1 -Platform PlayMode -BuildTarget Win64 -Filter Game.Tests.PcHudGc0244Tests
- Krok 9. PlayMode Win64 2/2. Test odświeżania HUD potwierdził aktywną rurę i zastrzał, wygaszoną stopę oraz 0 próbek GC.Alloc przy 500 odświeżeniach z ruchem prawego mocowania na 1920 × 1080 i 2560 × 1080.
- Następny krok to `pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64` z wygenerowanym ciągnikiem.
- Krok 10. Końcowy EditMode Win64 z prefabem TRAKT: 1524 zielone, 0 niepowodzeń, 122 pominięte. MirrorMount0340Tests 13/13. Zapisano XML, log i wyniki w dopisku 3. Slot zwolniony.
- Następny krok dla lidera to `git diff c8ca07835..codex-mirror-right-s24` i przegląd zestawień `artifacts/codex-mirror-right-s24/comparison-*.png`.

## codex-gis-fix-s24
- Krok 1. Przeczytano zasady i ADR. Punkt startowy d15ca070e zawiera cały kod main aed88604d. Różnica dotyczy wyłącznie HANDOVER.md.
- Następny krok to `pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner codex-gis-fix-s24` i bazowe pytest pięciu plików na prywatnych danych.
- Krok 2. Skopiowano 13 798 plików danych pochodnych (44 411 721 665 B) do prywatnego katalogu i odpięto junction. Fixture GIS może zapisać cache wyłącznie w worktree.
- Następny krok to `pwsh scripts/visual-qa.ps1 -Scene DrivingLab -BuildTarget Win64 -Pc -Tier High -Lighting clear` i odpowiednik overcast.
- Krok 3. Cztery pliki bazowe GIS dały 84 PASS, 10 FAIL, 1 XFAIL. Zgodność kopii danych C z manifestem: 192/192 pliki kafla, 2/2 GLB dalekiego planu. Win64 PC High clear i overcast wyrenderowano i obejrzano. Brak TRAKT ogranicza pierwsze kadry do placu testowego.
- Następny krok to `& $py -m pytest -q tests/gis/test_world_roads.py --basetemp artifacts/codex-gis-fix-s24/pytest/world-seed4` i powtórka testu eksportu z seedem 9. Utworzono nadrzędny katalog --basetemp po błędzie przygotowania pierwszego przebiegu.
- Krok 4. Test zjazdu sprawdza wartości 2 cm i rampę zgodnie z ADR 0349. Osiem wariantów testu wieży sprawdza nową sylwetkę ADR 0351 przy właściwym kierunku projekcji.
- Następny krok to `& $py -m pytest -q tests/gis/test_buildings_r7.py tests/gis/test_embankment_pylons_s24.py tests/gis/test_far_field.py tests/gis/test_budget_0221.py tests/gis/test_typology_0238.py tests/gis/test_world_v31.py tests/gis/test_hero_bridge.py`.
- Krok 5. Po korekcie 82 PASS w trzech plikach, 62 PASS w czterech plikach budżetowych. Porównanie hashy potwierdziło cztery nieaktualne źródła fidelity C. Zapisano tabelę 12 przypadków w WYNIKI.md.
- Następny krok to porównać pliki GLB z dwóch instancji `pytest -q tests/gis/test_world_roads.py` i uruchomić `pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64`.
- Krok 6. `test_world_roads.py`, seed 4, dał 14 PASS i 1 FAIL w 21:01. Świeży eksport `0_0` High ma hash a073376b…, kopia fali 13 ee87433a…. W 64 GLB High jest 43 różnic względem fali 13. Drugi proces z seedem 9 porówna te same wejścia.
- Następny krok to `& $py artifacts/codex-gis-fix-s24/compare-exports.py artifacts/codex-gis-fix-s24/pytest/world-seed4/world0 artifacts/codex-gis-fix-s24/pytest/world-seed9/world0 Data/raw/derived/bialystok-industrial-c/world`.
