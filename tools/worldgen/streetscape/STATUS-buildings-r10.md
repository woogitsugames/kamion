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
