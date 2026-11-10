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
