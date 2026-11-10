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
