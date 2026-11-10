# STATUS buildings-r10 (ADR 0081, gałąź worktree-agent-ac404823e7d8b56e7)

## 2026-11-10 krok 0 — rozpoznanie (bez zmian w kodzie)
- Worktree gotowy: junctiony Data/raw/{osm,gugik,cc0,refs,mapillary}, derived skopiowany, Library z main, cc0/_raw skopiowany.
- Bazowy build_world: 3 min 18 s, OK; bazowy budżet w `artifacts/buildings-r10/base/streetscape_qa.json`.
- Dane: 51 bloków, 79 hal, 120 szop/garaży, 270 domów; płot betonowy tylko 558 m (11 odcinków OSM barrier=wall), panelowy 15,8 km.
- Referencje CC0 (Commons, Rakoon): blok przy Rondzie Putry cm121537425 / cm121530695 / cm121537427 (biały tynk, balkony z szaroniebieską
  blachą perforowaną, zabudowy balkonów, anteny, pranie) -> `artifacts/buildings-r10/refs/`.
- Plan (kolejność): (1) atlas PBR `facade_atlas` 16x16 m (okna z firankami/roletami, drzwi, bramy garażowe, balustrady, klimatyzatory)
  + `facade_far` (rzędy okien dla LOD1 zamiast jednolitej siatki shaderowej) w `art-source/world/materials/_src/sets_buildings.py`,
  układ komórek w `tools/worldgen/streetscape/facade_atlas.py`; bez zmian C# (materiał `texture_set` + `set_tile`);
  (2) płot betonowy: przęsła 2 m schodkowane po terenie, słupki H, atlas `fence_concrete`; (3) hale: świetliki łukowe, drabina,
  rury, rampy, żaluzje; (4) balkony/klimatyzatory/anteny/wejścia; (5) garaże.
- NASTĘPNY KROK: napisać `tools/worldgen/streetscape/facade_atlas.py` i `art-source/world/materials/_src/sets_buildings.py`, potem
  `uv run --project tools/worldgen python art-source/world/materials/_src/build_all.py --only facade_atlas,facade_far`

## krok 1 — atlasy (kod + pierwsze PNG)
- `tools/worldgen/streetscape/facade_atlas.py` (układ 103 komórek 16x16 m, rzędy LOD1 24x23,4 m, płot 16x4,5 m), `art-source/world/materials/_src/sets_buildings.py`
  (malarze okien/drzwi/bram/balustrad/płotu), wpis w `build_all.py`; budowa 3 zestawów 60 s; podglądy `artifacts/buildings-r10/atlas/*_v1.jpg`.
- Kamery kontrolne: `tools/worldgen/qa/buildings_cameras.py` -> `Data/Regions/bialystok-industrial-c/buildings_r10_cameras.json` (19 kamer).
- UWAGA worktree: `git lfs checkout` konieczny (trees.glb był wskaźnikiem LFS -> import FAILED). Runda bazowa: `pwsh artifacts/buildings-r10/run_round.ps1 -Round base`.
- NASTĘPNY KROK: podpiąć atlas w `buildings_mesh.py`/`facade_kit.py`/`materials.py` (okna jako komórki, rzędy LOD1), potem
  `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c` i `pwsh artifacts/buildings-r10/run_round.ps1 -Round r1 -Configs High:overcast,Low:overcast`

## krok 2 — przejęcie po agencie ubitym limitem: podpięcie atlasów (commit ea9f339)
- LOD0: każde okno/drzwi/brama = komórka `facade_atlas` (bez geometrii ram i słupków: -20 tris/okno), ościeża i parapet zostają;
  bloki/biura czytają plan rzędów `FA.far_plan` (ten sam co LOD1), okna skalują się z wysokością kondygnacji (k = sh/2,8).
- LOD1: strefa okien = quady z rzędów `facade_far` (1 quad na paczkę kolejnych rzędów x 8 przęseł), UV0 w metrach atlasu; bez UV1.
- Balkony: front z komórki `balf` (wariant = rząd LOD1), 14 % zabudów, 18 % anten, 30 % prania; klimatyzatory 5 % okien bloków / 10 % biur.
- Płot betonowy: `furniture.concrete_fence` - przęsła 2 m poziome, schodkowane po terenie, 2 lica z różnych odlewów, słupki 12x14 cm.
- Testy: `tests/gis/test_world_v31.py` (+4 nowe). STATUS kopiowany do `artifacts/buildings-r10/STATUS.md`.
- NASTĘPNY KROK: `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c` ->
  `uv run --project tools/worldgen pytest tests/gis -q` -> `pwsh artifacts/buildings-r10/run_round.ps1 -Round r1 -Configs High:overcast,Low:overcast`

## krok 3 — stop na LIMIT 95 % (WIP)
- Kod: 14 rzędów `facade_far` (balkon 4, blok 4, biuro białe 2, biuro antracyt 2, wstęga 2), LOD1 = 1 quad na paczkę rzędów + 2 marginesy,
  attyka dopięta; akcent tylko na szczytach; czerpnie + drabina z koszem na halach; ADR `docs/adr/0081-buildings-r10-facade-atlases.md` (szkic).
- build_world OK (260 s). Budżet estymaty (`streetscape_qa.json` baza -> teraz, 19 kamer): Low tris -487..+556 (max +0,07 %),
  materiały Low -3..-7, High tris -0,4..-4,4 % (zabudowa High -20..-30 %). Pamięć tekstur nowa: facade_atlas 39,8/7,8/1,4 MB (H/M/L).
- pytest gis: 204 passed, 3 failed (te same 3 co na main wg HANDOVER: road_fidelity stale, route_corridor x2), + `test_cc0_scans::test_scan_sets_in_spec_keep_calibration`
  czerwony do czasu przebudowy zestawu fence_concrete (poprawka provenance w `build_all.py` już jest, spec nie przegenerowany).
- Runda r1 (import + kamery High/Low overcast) WYSTARTOWANA, w chwili stopu niezakończona; rendery NIE obejrzane, brak porównania ze zdjęciami,
  brak oceny visual-critic. Po rundzie skrypt sam cofa efekty uboczne Unity.
- NASTĘPNY KROK: `uv run --project tools/worldgen python art-source/world/materials/_src/build_all.py --only fence_concrete` ->
  sprawdź `artifacts/buildings-r10/r1/round.log` (jeśli brak "round done": `pwsh artifacts/buildings-r10/run_round.ps1 -Round r1 -Configs High:overcast,Low:overcast`)
  -> obejrzyj `artifacts/buildings-r10/r1/*/960/r10_*.jpg` vs `artifacts/buildings-r10/refs/` i `base/`, visual-critic, stats.txt Low vs base, uzupełnij ADR 0081.
- Runda r1 ZAKOŃCZONA po stopie (import + kamery High/Low overcast, exit 0); rendery w `artifacts/buildings-r10/r1/` nadal NIE obejrzane - krok 2 z listy pominąć, zacząć od oglądania.

## krok 4 — przejęcie nr 2 (2026-11-10): przegląd r1, budżet tekstur, przyczyna „ciemnych” elewacji
- Szum regeneracji (61 plików art-source/world/{signs,textures,props,landmarks}) cofnięty `git checkout --`.
- r1 obejrzane (19 kamer High + Low): elewacje tynkowe ciemne i przesycone (blok `plaster_grey` 0,36 lin. -> na ekranie 0,095; cokół bez
  tekstury 0,16 jaśniejszy niż ściana 0,36). Przyczyna zmierzona: `_Tint` w Kamion/World PBR to właściwość Color, Unity linearyzuje ją drugi raz
  (kolor^2,2). Poprawka: flaga `tint_linear` (materials.py, tylko powłoka budynków) + `WorldPbrMaterials.cs` zapisuje wartość gamma.
- Cegła: `set_tile` (zestaw 1,506 m był próbkowany co 4 m -> warstwa cegły ~20 cm). Cokół `plinth_dark` dostał zestaw `plaster`.
- Zacieki pod attyką także na tynku/płycie bloków i biur (LOD0; flaga `runoff`, siła x0,6).
- Budżet tekstur (docs/PERFORMANCE_BUDGETS: 64/96/256 MB Low/Medium/High): zestawy świata na main 6,0/33,6/171,9 MB; r1 8,3/46,8/239,6 MB;
  teraz 7,3/39,5/197,1 MB. facade_atlas 39,8/7,8/1,4 -> 17,4/3,8/0,6 MB (Normal/Mask/Var w 1/2 rozdzielczości albedo, `aux_div`),
  facade_far 16,7 -> 4,9 MB High (aux 1/4), fence_concrete 11,2 -> 2,8 MB High (2048 px, kalibracja do 0,30).
- `test_cc0_scans`: 6 passed.
- NASTĘPNY KROK: `git merge main` (generated -> --ours) -> `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c`
  -> `uv run --project tools/worldgen pytest tests/gis -q` -> `pwsh artifacts/buildings-r10/run_round.ps1 -Round r2 -Configs High:overcast,Low:overcast`

## krok 5 — merge main, runda r2, testy (2026-11-10)
- `git merge main` (generated = ours) + build_world (278 s) + import (569 s). pytest gis: 222 passed, 3 failed (road_fidelity stale,
  route_corridor x2 - te same co na main, zadanie 0076), 2 xfailed. EditMode: 188 total, 176 passed, 0 failed, 7 skipped.
- Runda r2 (High + Low overcast) obejrzana vs r1 i refs CC0: tynki jasne (szary/kremowy/brzoskwiniowy jak na zdjęciach), cegła w skali,
  cokół z fakturą, zacieki pod attyką widoczne z bliska; LOD1 na Low zgodny kolorem z LOD0. Rundy poprawek: 1 z 2 wykorzystana.
- stats.txt Low (estymata edytora, r1 -> r2, r2 zawiera też zmiany z main): block_1 418 -> 460 draws / 322k -> 331k tris, block_2 330 -> 372 / 352k -> 361k,
  fence_3 257 -> 243 / 352k -> 355k, office_2 149 -> 150 / 189k -> 174k.
- Otwarte: brak oceny visual-critic (zakaz subagentów w tym zadaniu), brak pomiaru na telefonie, globalna poprawka `_Tint` (ADR 0081, „do decyzji lidera”),
  kamera r10_hall_3 pod terenem, r10_hall_1 zasłonięta naczepą (po merge main), tynk szary z bliska ma za mocny „pieprz” faktury.
- NASTĘPNY KROK (lider): `git merge worktree-agent-ac404823e7d8b56e7` (generated -> --ours) ->
  `uv run --project tools/worldgen python art-source/world/materials/_src/build_all.py --only facade_atlas,facade_far,fence_concrete` ->
  `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c` -> `pwsh scripts/import-region.ps1 -Region bialystok-industrial-c`
