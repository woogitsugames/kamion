# STATUS region-0166 (ADR 0166 Dojlidy/Krywlany — przygotowanie danych)

- Kafel wybrany: `bialystok-dojlidy` bbox EPSG:2180 [779019, 589055, 781067, 591103] (siatka 2048 m od kafla C, i=+1, j=-3), origin (780043, 590079). Wpis w `tools/worldgen/regions.py` (addytywny, C bez zmian).
- Uzasadnienie (OSM 2026-11-08): w kaflu KAN, Rosti x2, Bravilor, Masterpress, Odlewnia, Bison, PSS Społem DC, BPN-T; lotnisko Krywlany wsch. (aerodrome x 778298–780302). Browar/Biawar w (+2,-3), hangary w (0,-3).
- Data/raw = junction do main (NIE kasować zawartości; przed usunięciem worktree: `cmd /c rmdir Data\raw`).

Następny krok: `cd C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\region-0166; uv run --project tools/worldgen tools/worldgen/ingest.py --region bialystok-dojlidy --dry-run`
