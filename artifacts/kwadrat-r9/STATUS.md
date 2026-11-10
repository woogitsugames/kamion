# Kwadrat Park (hero, ADR 0071) — STATUS

Worktree `.claude/worktrees/agent-a1409e374f8c12b4f`, gałąź `worktree-agent-a1409e374f8c12b4f` (od main 947749e).

## Ustalenia
- Obiekt: główna hala `bdot:9962cca0…` (21 399 m², LoD1 10,16 m), fasada placu = SE (130,7 m po odcięciu 3 przybudówek).
- Referencje (tylko otwarte): ortofoto GUGiK 2024-05-27 0,25 m (`refs/grid_*.jpg`), zdjęcia CC0 Rakoon / Commons
  `cm109685822` (20210904_101250: narożnik S, fasady SW+SE) i `cm157094809` (2024: fasada SW z daleka). Katalog
  `artifacts/refs/kwadrat-park/` nie istniał — refs zebrane samodzielnie w `artifacts/kwadrat-r9/refs/`.
- „11 bram” z PHOTO-LIST to wynik starej reguły generatora, NIE fakt: ortofoto nie pokazuje bram (elewacja w cieniu,
  zestawy stoją równolegle do ściany). Zachowane 11 doków w tych samych pozycjach (u0 = 7,815 m, co 4,0 m) jako
  WORKING_VALUE — fizyka/plac/trasa bez zmian.
- Widać na zdjęciach: jasnoszara blacha pozioma, cynobrowe ramy pasma okien (SE) i żaluzji (SW przy narożniku), wysoki
  cynobrowy portal na SE, ciemna attyka, wentylatory dachowe; ortofoto: dach bitumiczny z siatką świetlików, białe pole
  membrany przy SE, jaśniejszy niższy dach w pierścieniu, czerwone daszki 2 przybudówek, asfalt + auta przed rzędem lokali.

## Architektura
- Override `kind: hero_depot` (`overrides.yaml: kwadrat-park-hero`) → `tools/worldgen/streetscape/hero_depot.py`
  (`plan()` spec + sha, `apply()` instancje + kolizja odbojnic) → spec `Data/Regions/<id>/generated/landmarks/kwadrat_park.spec.json`
  → `tools/blender/world/landmarks/make_depot.py` → `art-source/world/landmarks/kwadrat_park/kwadrat_park.glb` + `_meta.json`.
- `buildings_mesh.build(heroes=…)`: doki z speca (ten sam dict co `docks_for`), widoczne warstwy hali usuwane gdy asset aktualny,
  pryzmat kolizji zostaje. Prototypy `landmark_depot_kwadrat_park_NN` (+`.lod1/.lod2`, `_roof`), LOD [100, 400, 20000] m.
- Materiały: nazwy z `streetscape/materials.py` (nowe `kp_wall`, `kp_accent`, `kp_glass_block`, `kp_roof_white`), UV0 w metrach.
- Plac: `paved_area kwadrat-park-units-forecourt` (asfalt + parking przed lokalami), `kwadrat-park-trade-units` (ściana szara).

## Dziennik
- Baseline build_world (log `logs/build_world_baseline.log`, QA `logs/streetscape_qa_baseline.json`): kwadrat_park_gate
  High 922 881 / Low 331 911 tr.
- Blender it1–it3 (`blender/it*/`, montaże `montage/it2_photo_vs_render.jpg`, `it3_photo_vs_render.jpg`, `it2_ortho_vs_top.jpg`):
  it1 pierwsza bryła; it2 dziedziniec, sufit otwartego doku, pasmo 2,0 m / parapet 6,6 m, portal 12,6 m, kamera foto
  (95 m na S od narożnika, hfov 22°); it3 attyka 0,30 m, szerokie lamele żaluzji, jaśniejsze luksfery.

## NASTĘPNY KROK
    bash artifacts/kwadrat-r9/render.sh itN [kamery]        # iteracja assetu (render kontrolny)
    blender -b --factory-startup -P tools/blender/world/landmarks/make_depot.py -- --spec Data/Regions/bialystok-industrial-c/generated/landmarks/kwadrat_park.spec.json   # eksport GLB + meta
    KAMION_BLENDER=<blender.exe> uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c
