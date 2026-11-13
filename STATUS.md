# STATUS region-0166 (ADR 0166 Dojlidy/Krywlany — przygotowanie danych)

- Kafel wybrany: `bialystok-dojlidy` bbox EPSG:2180 [779019, 589055, 781067, 591103] (siatka 2048 m od kafla C, i=+1, j=-3), origin (780043, 590079). Wpis w `tools/worldgen/regions.py` (addytywny, C bez zmian).
- Uzasadnienie (OSM 2026-11-08): w kaflu KAN, Rosti x2, Bravilor, Masterpress, Odlewnia, Bison, PSS Społem DC, BPN-T; lotnisko Krywlany wsch. (aerodrome x 778298–780302). Browar/Biawar w (+2,-3), hangary w (0,-3).
- Data/raw = junction do main (NIE kasować zawartości; przed usunięciem worktree: `cmd /c rmdir Data\raw`).

- ingest OK (8 plików, 325.9 MB w main Data/raw), build_region OK: 355 węzłów, 421 krawędzi, 406 budynków (58a5dc1fc).

Następny krok: `cd C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\region-0166; pwsh C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1 -Acquire -Pool heavy -Owner region-0166; uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-dojlidy`


## agent #3 (2026-11-13, po incydencie API)
- build_world dojlidy padał w `cameras()` (IndexError: kamery C zakładały ulicę Andersa na trasie). Naprawa ogólna: `cameras()` -> C: `cameras_industrial_c` (bez zmian), inne: `cameras_generic` (stacje trasy co ~300 m, ronda z góry, ortho kafla).
- Efekt uboczny 1. przebiegu: przebudowa WSPÓLNEJ biblioteki `art-source/world/{props,textures}` zestawem znaków dojlidy -> przywrócone do main; `props_library_dir()`: region != C pisze do `Data/raw/derived/<id>/props|signs|textures` (poza git).
- Następny krok: `Get-Content artifacts\region-0166\build_world2.log -Tail 30`
- 24719c964: build_world dojlidy OK; QA (qa_report + landmarks D51 + ADR 0166 draft). Shared GUGiK 2061 manifests restored (sources.py nie przepisuje). Megascans/cc0 _raw skopiowane z main. W tle: rebuild dojlidy z Megascans + pytest C (artifacts/region-0166/rerun.log).
- Następny krok: `Get-Content artifacts\region-0166\rerun.log -Tail 30`; potem `git status` (testy C przepisują pliki C -> `git checkout -- Data/Regions/bialystok-industrial-c`).
