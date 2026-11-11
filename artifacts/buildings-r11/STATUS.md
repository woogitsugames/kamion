# STATUS buildings-r11 (ADR 0091, gałąź worktree-buildings-r11, z main d205d4a)

## 2026-11-11 krok 0 — rozpoznanie + baza
- Library skopiowane z main (robocopy), bazowy build_world 264 s OK, runda bazowa (import + High/Low overcast + High clear) uruchomiona:
  `artifacts/buildings-r11/base/`.
- Dane domów: 270 domów, 196 już ma dach dwuspadowy (warunek: obrys ~ prostokąt, typ LoD2 1030/1130/None); 74 to kostki
  (38 x typ 1010 jednospadowy, 33 x obrys nieprostokątny, 3 x 1000 płaski). Kalenica LoD2 (`height_lod2_2017_m`) i okap
  (`lod2_eave_rel_m`) są w danych, a kalenica nie była używana (dach liczony od wysokości LoD1).
- Dachy `roof_tiles_*` / `roof_metal_*` nie mają zestawu tekstur (płaski kolor URP Lit). Balkony istnieją, ale tylko na
  elewacjach najdalszych od drogi (stąd „bloki bez balkonów” przy trasie). Rozbryzg (_SPLASH) zasłonięty cokołem bez rozbryzgu.
- NASTĘPNY KROK: zmiany w `tools/worldgen/streetscape/buildings_mesh.py` (dach ogólny, balkony, cokół), potem
  `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c` ->
  `pwsh artifacts/buildings-r11/run_round.ps1 -Round r1 -Configs High:overcast,Low:overcast,High:clear`

## krok 1 — kod r1 (commit 8f34efe6) + baza zmierzona
- Baza (main d205d4a, High overcast, `measure.py`): niebo 238, szary tynk 92,1 (szczyt) / 97,9 (front), pieprz hf 8,60, cegła 70/41/34
  (R/B 2,07), cokół 56,5. Low: szary 85,6 / 91,8. stats Low: block_2 483 draws / 651k tris, house_2 242 / 396k.
- Kod: `streetscape/roofs.py` (dwuspadowy / czterospadowy / jednospadowy nad PRAWDZIWYM obrysem; kalenica z LoD2, okap z LoD2,
  LoD1 = okap + 0,55 x wznios - zmierzone na 229 domach), okna w szczytach, kominy na połaci, okap 0,5 m z podbitką i deską czołową;
  270 domów: 200 dwuspad., 30 czterospad., 36 jednospad. (połówki bliźniaków), 4 płaskie. Balkony: strona SSW + 35 % obie strony,
  poręcz jako geometria. Cokoły 3 tony + `splash_h`. Zestaw `roof_tiles` (512 px, +0,6 MB High). Tynk: hf_ratio 0,2233 -> 0,0697.
  Cegła: fuga -45 %, nasycenie tintu -20 %, `macro` [48 m; 0,18]. plaster_grey 0,36 -> 0,62, plaster_white 0,60 -> 0,76.
- Tekstury świata (estymata ASTC): 197,5 / 39,6 / 7,3 MB -> 198,1 / 39,7 / 7,3 MB (H / M / L).
- build_world OK (235 s), runda r1 uruchomiona (import + High/Low overcast + High clear).
- NASTĘPNY KROK: obejrzyj `artifacts/buildings-r11/r1/*/1280/r10_*.jpg`, potem
  `uv run --project tools/worldgen python artifacts/buildings-r11/measure.py artifacts/buildings-r11/r1/High-overcast`
  (jeśli brak "round done" w r1/round.log: `pwsh artifacts/buildings-r11/run_round.ps1 -Round r1 -Configs High:overcast,Low:overcast,High:clear`)

## krok 2 — rundy r1-r3 obejrzane i zmierzone, ADR 0091 (2026-11-11)
- r1: dachy / balkony / tynk OK, ale domy z niskim okapem bez okien, tynk „chmurkowaty”, Low draws +7 % / tris +5 %.
- r2: okna pod niskim okapem, cięcia (parapety 4 tris, poręcz 12 tris, bez plinth_brown / roof_metal_brick / roof_fascia).
- r3: tynk `set_tile` (2 m) + płaski relief, czapa komina i cokół domów bez nowych materiałów.
- Wynik r3 vs baza (High overcast): szary tynk 92,1 -> 127,4 i 97,9 -> 131,1 (niebo 238,2); cegła R/B 2,07 -> 1,66;
  pieprz na ekranie 2,00 -> 1,89 (cel „o połowę” NIE spełniony; zestaw: rozrzut albedo -43 %, relief 5,7 -> 0,7 mm).
- Budżet Low (58 kamer): tris maks. +2,2 %; draws 4 kamery ponad +3 % (dk8-dk19-exit +5,2, r10_fence_1 +3,6, putry-above +3,4,
  r10_block_3 +3,2). Tekstury 197,5 / 39,6 / 7,3 -> 198,1 / 39,7 / 7,3 MB.
- Testy: pytest gis 252 passed / 3 failed (te same co main: road_fidelity stale, route_corridor x2); EditMode 188/191
  (TruckDoorGlassTests x3 - materiał ciężarówki, na main nie sprawdzane).
- Otwarte: visual-critic, telefon, draws na 4 kamerach, pieprz w shaderze, dachy wielopołaciowe domów L, balkony wg zdjęć.
- NASTĘPNY KROK (lider): `git merge worktree-buildings-r11` (generated -> --theirs lub regeneracja) ->
  `uv run --project tools/worldgen python art-source/world/materials/_src/build_all.py --only roof_tiles,plaster,brick` ->
  `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c` ->
  `pwsh scripts/import-region.ps1 -Region bialystok-industrial-c`
