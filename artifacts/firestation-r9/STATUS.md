# Straż pożarna JRG2 (hero, ADR 0070) — STATUS

Worktree `.claude/worktrees/agent-aa9c74c62497e5d1f`, gałąź `worktree-agent-aa9c74c62497e5d1f` (od main 947749e).

## Ustalenia
- Obiekt: JRG nr 2, Andersa 46, OSM way 211035271 (`amenity=fire_station`), BDOT `bdot:2BE4B431-C784-1BF0-E053-CC2BA8C0D140`
  (funkcja "straż pożarna", 1317,7 m2) + budynek gospodarczy `bdot:2BE4B431-C7B4-1BF0-E053-CC2BA8C0D140` (245 m2).
  W kaflu, 52,2 m od osi trasy startowej (stacja s=1335 m z 2401 m), po prawej stronie kierunku jazdy.
- Wymiary: LoD2 GUGiK 2017 (`art-source/world/landmarks/fire_station_jrg2/lod2_roofs.json`): wozownia okap 6,05 / kalenica 6,96;
  część środkowa okap 6,56–7,31 / 9,2; wieża okap 10,45 / szczyt 12,42; hala z dachem łukowym 10,6–12,27; budynek gosp. 9,0/10,55, wieżyczka 13,04.
- Referencje (otwarte): Commons cm151035820 (Rakoon, CC0), Mapillary 767523907280643/171742518208129 (richlv), 471355742447021 (strudel),
  2934972690092373 (grobin), KartaView kv993066550 (CC BY-SA 4.0, tylko wzór), ortofoto GUGiK 0,25 m. Kadry: `artifacts/firestation-r9/refs/z_*.jpg`.
- Junction `Data/raw` -> main (usunąć `cmd /c rmdir Data\raw` przed kasowaniem worktree). Mapillary dociągnięte do `Data/raw/mapillary/fire-station` (150 szt.).

## Dziennik
- Znaleziony obiekt (`tools/worldgen/streetscape/find_fire_station.py`), LoD2 (`lod2_extract.py`), referencje obejrzane.
- NASTĘPNY KROK: `tools/blender/world/landmarks/make_fire_station.py` + spec JSON, render kontrolny.
- Lider wskazał CC0 `Data/photos/nowe/7197_May_2021_in_Białystok.jpg` — potwierdzone: to JRG2 (kategoria Commons "Fire station JRG 2 Białystok (Andersa Street)" ma tylko 2 pliki, oba mamy). Główna referencja.
- Atlas `fire_station` 14x14 m (2048 High; skany CC0 Poly Haven painted_plaster_wall, brick_wall_006, concrete_wall_008) + `art-source/world/textures/fire_station_alpha.png`; `dims.json`; `tools/worldgen/streetscape/hero_building.py` (spec/plan/apply); `tools/blender/world/landmarks/make_fire_station.py`.
- Blender it1/it2 obejrzane (`artifacts/firestation-r9/blender/it2/compare_it2.jpg`), it3: hala NW blacha, tuje smuklejsze, płot ciemniejszy, gąsiory. GLB: trójkąty LOD0/1/2 = 8246/2956/164.
- NASTĘPNY KROK: hooki worldgen (stage.py, buildings_mesh.py, build_world.py, materials.py, export.py), InstanceImporter (biblioteki landmarków), kamera QA, potem `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c`.
- Hooki worldgen + importer + testy + ADR 0070 + LICENSES + WORLD_GENERATION zrobione. `build_world` OK (log `logs/build_world_1.log`): `hero buildings {'applied': ['andersa-jrg2-fire-station-hero'], 'stale': []}`, instancja `landmark_fire_station_jrg2` w (-262.92, -142.67, 131.256), trójkąty 8240/2950/164, 61 boksów kolizji płotu. Kamery QA: fire_station_route / _abeam / _ref7197 / _above.
- Blender it3: `blender/it3/compare_it3.jpg` (montaż z referencjami). `tests/gis/test_hero_building.py` 7 passed, 1 skipped (przed buildem); pełny `pytest tests/gis` w toku (poprawiony test_streetscape: prototypy z bibliotek landmarków).
- W TLE: `pwsh scripts/import-region.ps1 -Region bialystok-industrial-c` (log `logs/import_region_1.log`, koniec = `EXIT 0`). Library skopiowane z main, LFS pull zrobiony, junction Data/raw.
- NASTĘPNE KROKI:
  1. sprawdzić `logs/import_region_1.log` (IMPORT_RESULT: OK); jeśli brak: `pwsh scripts/import-region.ps1 -Region bialystok-industrial-c`
  2. `pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier High -Lighting overcast -Cameras fire_station_route,fire_station_abeam,fire_station_ref7197,fire_station_above -OutputDir artifacts/firestation-r9/unity/High-overcast` (+ Low, lowsun); zmniejszyć PNG, montaż z `refs/lead_7197_960.jpg`
  3. `uv run --project tools/worldgen pytest tests/gis -q`; `pwsh scripts/test.ps1 -Platform EditMode`
  4. cofnąć efekty uboczne Unity (M_Sky.mat, QualitySettings.asset, ProjectSettings.asset, Assets/Resources), commit, skopiować `artifacts/firestation-r9` do main, visual-critic (lider).
- Unity: pierwszy render pokazał atlas powielony co 4 m (WorldPbrMaterials nie zapisywał `_Tile`); naprawa tylko dla zestawów `"atlas": true`. Runda r2 OK: `unity/r2/{High,Low}-{overcast,lowsun}/`, montaż `unity/r2/compare_unity_r2.jpg`. pytest tests/gis 173 passed (359 s); EditMode 176: 164 passed, 0 failed, 5 inconclusive (brak prefabu TRAKT w worktree), 7 skipped.
- Efekty uboczne Unity cofnięte (M_Sky.mat, QualitySettings, ProjectSettings; brak Assets/Resources).
- UWAGA: `Data/raw` to junction do main, więc `build_world` z tej gałęzi nadpisał `Data/raw/derived/bialystok-industrial-c/world/*` w main (instancja `landmark_fire_station_jrg2`, brak generycznej bryły remizy). Main bez tej gałęzi: `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c`.
- OTWARTE: visual-critic (lider); dach w Unity jaśniejszy / mniej nasycony niż na zdjęciach (zmniejszyć `chalk`, szorstkość ok. 0,6 w `sets_fire_station.py`, przebudować atlas); okna szczytu płaskie; elewacje podwórza WORKING_VALUE; kadr `fire_station_ref7197` szerszy niż zdjęcie; po scaleniu wiaduktu `git merge main` i oznaczyć `viaduct_concrete` jako `atlas`.
- NASTĘPNY KROK: `git merge main` (po scaleniu ADR 0067), konflikty w build_all.py / materials.py / InstanceImporter.cs / build_world.py, potem `pwsh artifacts/firestation-r9/scripts/unity_round.ps1 -Tag r3`.
- SESJA 2: `git merge main` zrobiony (27c6ed9 + fix): wspólne tabele `HERO_LOD_ENDS` (build_world) / Policy (InstanceImporter), `HERO_ATLASES` (build_all), `_Tile` w jednym miejscu (set_tile || atlas), `viaduct_concrete` atlas=true. generated/*.json = main (regeneracja przez build_world).
- Junction `Data/raw` zastąpiony: katalog z junctionami cc0/gugik/mapillary/osm/refs + LOKALNA kopia `derived` (640 MB). Przed kasowaniem worktree: `cmd /c rmdir` na 5 junctionach.
- NASTĘPNY KROK: poprawki wyglądu (dach, okna szczytu, bramy, detale) w `sets_fire_station.py` / `make_fire_station.py`, potem build_world + `pwsh artifacts/firestation-r9/scripts/unity_round.ps1 -Tag r3`.
- r3 (sesja 2): atlas: dach nasycony (chalk 0,02, szorstkość ≥0,6), obróbki; okna szczytu z prawdziwą głębią (ościeże 0,20 m, opaska 3 cm przed licem, szprosy) i przemierzone na zdjęciu 7197 (łukowe 4,7×4,6 m, okrągłe d 3,4 m, napis wyżej); rynny, lampy nad bramami/drzwiami; ogrodzenie na linii OSM way 258562003 + `hero_building.fence_cut` (generyczny płot tej drogi wycięty, w r2 był podwójny biały); kamery QA (abeam +9 m, ref7197 fov 24,5° pion). Blender it4: LOD 9006/2950/164 (`blender/it4/compare_it4.jpg`). Testy: +2 (wspólny mechanizm, fence_cut).
- W TOKU: build_world (log `logs/build_world_r3.log`) na dims SPRZED łatki szczytu; po nim trzeba powtórzyć.
- NASTĘPNY KROK: `$env:KAMION_BLENDER='C:/Users/matma/AppData/Local/Programs/Blender4.2/blender-4.2.9-windows-x64/blender.exe'; uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c` → `pwsh artifacts/firestation-r9/scripts/unity_round.ps1 -Tag r3` → obejrzeć PNG, montaż z `refs/lead_7197_960.jpg` → `uv run --project tools/worldgen pytest tests/gis -q`, `pwsh scripts/test.ps1 -Platform EditMode` → cofnąć efekty uboczne Unity → kopia dowodów do main.
