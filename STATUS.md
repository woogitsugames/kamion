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

## codex-review-day27-s24
- Krok 1. Ustalono migawkę bfaccaf1a i zakres 34 scaleń (33 na pierwszym rodzicu), przeczytano zasady oraz kontekst ADR.
- Następny krok: `git diff 2d5744863^1 bfaccaf1a -- '*.cs' '*.hlsl' '*.shader' '*.py'`.

- Krok 2. Porównano 34 scalenia z pierwszym rodzicem i sprawdzono połączone ścieżki renderingu, streamingu, HUD i danych. Cztery bramki GIS: 62/62 w 60,29 s.
- Następny krok: `git diff 2d5744863^1 bfaccaf1a -- tests/gis` oraz izolowane reprodukcje rozbieżności.

- Krok 3. Zweryfikowano 8 znalezisk: 6 ważnych i 2 drobne. Rozszerzone GIS: 289 pass, 9 fail. Obejrzano istniejące pary PNG High clear/overcast. Raport w `artifacts/codex-review-day27-s24/REVIEW.md`.
- Następny krok dla lidera: `git show codex-review-day27-s24:artifacts/codex-review-day27-s24/REVIEW.md`.

- Krok 4. Sprawdzono istniejącą poprawkę GIS z `c92a9912e`: 9/9 zmienionych przypadków wykonanych w pamięci na kodzie migawki. Uzupełniono raport i opublikowano kopię w katalogu dowodów.
- Następny krok dla lidera: `git show c92a9912e`, potem ponowny przebieg wskazanych testów po integracji.

### codex-gen-fix-s25 — pomiary bazowe
- Przeczytano reguły, recenzję i ADR 0023/0334/0351/0352. Gałąź zawiera scalenie GIS s24. Wrapper działa. Odczytano 54 cache: 23/41 samotnych wież, 4/6 różnic po odwróceniu listy przęseł (Low/High). Maski 1/3/5 m: 13/1/1 kart z końcem w masce.
- Następny krok po poprawce WN: `cmd /c C:/Users/matma/Documents/Claude/kamion/scripts/cli-jobs/wgpy.cmd -m pytest -q tests/gis/test_hv_wires_0351.py`.

### codex-gen-fix-s25 — LOD i determinizm WN
- Eksport przepuszcza wyłącznie podpory WN z przęseł LOD. QA zapisuje liczniki Low/High. Kanoniczny klucz rozstrzyga remisy. Testy WN 14 PASS, na 54 cache sieroty i różnice po permutacji: 0/0.
- Następny krok po poprawce masek: `cmd /c C:/Users/matma/Documents/Claude/kamion/scripts/cli-jobs/wgpy.cmd -m pytest -q tests/gis/test_fields_r3_0334.py tests/gis/test_fields_r4_0334.py`.

### codex-gen-fix-s25 — podstawy kart kukurydzy
- Sprawdzanie komórek maski po transformacji obejmuje też krótkie karty i strays. Dla pasów 1/3/5 m zniknęło odpowiednio 13/1/1 kart; na podstawie trójkątów 0 przecięć. Testy pól: 21 PASS.
- Następny krok po zmianie kolejności gatunków: `cmd /c C:/Users/matma/Documents/Claude/kamion/scripts/cli-jobs/wgpy.cmd -m pytest -q tests/gis/test_treerows_0222.py tests/gis/test_trees_0352.py`.

### codex-gen-fix-s25 — kanoniczne mieszanki szpalerów
- Klucze `species` i `young_species` sortowane przed losowaniem. Oba warianty nowego testu odtwarzają błąd na bazie i przechodzą po zmianie. Zestaw szpalerów: 26 PASS.
- Następny krok po oględzinach i aktualizacji bramek atlasów: `cmd /c C:/Users/matma/Documents/Claude/kamion/scripts/cli-jobs/wgpy.cmd -m pytest -q tests/gis/test_world_v34.py tests/gis/test_vegetation_r2.py`.

### codex-gen-fix-s25 — bramki impostorów
- ADR 0023: atlas 4096 × 1024, wyjątek pineyoung 2048 × 512, granice widoków z zaokrągleniem. Na 18 widokach sosny przy 2048 × 512: odłączone maks. 1,89%, największy element 1,03%. Obejrzano PNG i archiwalne High clear/overcast. Testy atlasów i roślinności: 31 PASS.
- Następny krok: `cmd /c C:/Users/matma/Documents/Claude/kamion/scripts/cli-jobs/wgpy.cmd -m pytest -q tests/gis/test_budget_0221.py tests/gis/test_typology_0238.py tests/gis/test_world_v31.py tests/gis/test_hero_bridge.py tests/gis/test_far_field.py tests/gis/test_hv_wires_0351.py tests/gis/test_embankment_pylons_s24.py tests/gis/test_fields_r3_0334.py tests/gis/test_fields_r4_0334.py tests/gis/test_treerows_0222.py tests/gis/test_trees_0352.py tests/gis/test_world_v34.py tests/gis/test_vegetation_r2.py`.

### codex-gen-fix-s25 — zweryfikowane i przekazane
- 224/224 celowanych GIS, w tym 62/62 budżetowych. Low −476 i High −1968 tri WN łącznie. Zero nowych sektorów z WN. Raport i dowody w `artifacts/codex-gen-fix-s25/`.
- Następny krok lidera: `git diff --stat e8b5d5e8f..codex-gen-fix-s25`, następnie kolejka fali 14 wg `artifacts/regen-wave-14-s24/README.md`.
- 2026-11-27T23:42:09 regen-wave-14-s24 — profil koron. Następny krok: `pwsh -NoProfile -File artifacts/regen-wave-14-s24/chain.ps1 -Chain A`
- 2026-11-28T01:12:00 regen-wave-14-s24 — kafle gotowe (1). Następny krok: `pwsh -NoProfile -File artifacts/regen-wave-14-s24/final.ps1`
- 2026-11-28T01:25:16 regen-wave-14-s24 — kafle gotowe (1). Następny krok: `pwsh -NoProfile -File artifacts/regen-wave-14-s24/final.ps1`
- 2026-11-28T01:50:38 regen-wave-14-s24 — kafle gotowe (1). Następny krok: `pwsh -NoProfile -File artifacts/regen-wave-14-s24/final.ps1`
- 2026-11-28T02:11:13 regen-wave-14-s24 — kafle gotowe (1). Następny krok: `pwsh -NoProfile -File artifacts/regen-wave-14-s24/final.ps1`
- 2026-11-28T02:29:25 regen-wave-14-s24 — kafle gotowe (1). Następny krok: `pwsh -NoProfile -File artifacts/regen-wave-14-s24/final.ps1`
- 2026-11-28T02:46:19 regen-wave-14-s24 — kafle gotowe (1). Następny krok: `pwsh -NoProfile -File artifacts/regen-wave-14-s24/final.ps1`
- 2026-11-28T02:59:25 regen-wave-14-s24 — kafle gotowe (1). Następny krok: `pwsh -NoProfile -File artifacts/regen-wave-14-s24/final.ps1`
- 2026-11-28T03:13:11 regen-wave-14-s24 — kafle gotowe (1). Następny krok: `pwsh -NoProfile -File artifacts/regen-wave-14-s24/final.ps1`
- 2026-11-28T03:22:43 regen-wave-14-s24 — kafle gotowe (1). Następny krok: `pwsh -NoProfile -File artifacts/regen-wave-14-s24/final.ps1`
- 2026-11-28T03:35:48 regen-wave-14-s24 — kafle gotowe (1). Następny krok: `pwsh -NoProfile -File artifacts/regen-wave-14-s24/final.ps1`
- 2026-11-28T03:47:20 regen-wave-14-s24 — kafle gotowe (1). Następny krok: `pwsh -NoProfile -File artifacts/regen-wave-14-s24/final.ps1`
- 2026-11-28T03:52:04 regen-wave-14-s24 — kafle gotowe (1). Następny krok: `pwsh -NoProfile -File artifacts/regen-wave-14-s24/final.ps1`
- 2026-11-28T04:02:54 regen-wave-14-s24 — kafle gotowe (1). Następny krok: `pwsh -NoProfile -File artifacts/regen-wave-14-s24/final.ps1`
- 2026-11-28T04:07:40 regen-wave-14-s24 — kafle gotowe (1). Następny krok: `pwsh -NoProfile -File artifacts/regen-wave-14-s24/final.ps1`
- 2026-11-28T04:13:25 regen-wave-14-s24 — kafle gotowe (1). Następny krok: `pwsh -NoProfile -File artifacts/regen-wave-14-s24/final.ps1`
- 2026-11-28T04:23:24 regen-wave-14-s24 — kafle gotowe (1). Następny krok: `pwsh -NoProfile -File artifacts/regen-wave-14-s24/final.ps1`
- 2026-11-28T04:28:00 regen-wave-14-s24 — kafle gotowe (1). Następny krok: `pwsh -NoProfile -File artifacts/regen-wave-14-s24/final.ps1`
- 2026-11-28T04:36:56 regen-wave-14-s24 — kafle gotowe (1). Następny krok: `pwsh -NoProfile -File artifacts/regen-wave-14-s24/final.ps1`
- 2026-11-28T04:41:30 regen-wave-14-s24 — kafle gotowe (1). Następny krok: `pwsh -NoProfile -File artifacts/regen-wave-14-s24/final.ps1`
- 2026-11-28T04:50:05 regen-wave-14-s24 — kafle gotowe (1). Następny krok: `pwsh -NoProfile -File artifacts/regen-wave-14-s24/final.ps1`
- 2026-11-28T04:54:51 regen-wave-14-s24 — kafle gotowe (1). Następny krok: `pwsh -NoProfile -File artifacts/regen-wave-14-s24/final.ps1`
- 2026-11-28T05:00:25 regen-wave-14-s24 — kafle gotowe (1). Następny krok: `pwsh -NoProfile -File artifacts/regen-wave-14-s24/final.ps1`
- 2026-11-28T05:05:13 regen-wave-14-s24 — kafle gotowe (1). Następny krok: `pwsh -NoProfile -File artifacts/regen-wave-14-s24/final.ps1`
- 2026-11-28T05:10:21 regen-wave-14-s24 — kafle gotowe (1). Następny krok: `pwsh -NoProfile -File artifacts/regen-wave-14-s24/final.ps1`
