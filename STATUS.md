# STATUS — build-hygiene-s23 (porządki przed pełnym buildem Windows)
- Krok 1: `scripts/check-build-scenes.py` — sceny regionów z katalogu (reguły RegionBuildList/RegionCatalog.Resolve), braki Low/Tile/High, D86 (kafel Low bez High = FAIL), dane bez wpisu w katalogu = FAIL, region poza d67-full = WARNING, porównanie z logiem. Main 17.11: d67-full 21/21 Low+High, 0/21 `_Tile`; ostatni pełny build ma dk65-03/04. Pierścień tylko na origin/world2-s23 (39, check OK).
- Krok 2: postbuild — korytarz tylko z `World_knyszyn-s_Tile`; `Kamion-d3d11.cmd`, `Kamion-korytarz-d3d11.cmd`; README w zipie; `collect-logs.ps1` zbiera CrashDumps (PS 5.1: 2 × 1 GB OK, 16 s).
- Krok 3–5: dry-run e28533ca31 exit 0 (bez korytarza), analiza importu, lista kontrolna `docs/reports/CHECKLIST-2026-11-16-full-build-windows.md` (D86 = punkt otwarty). Dowody: `artifacts/build-hygiene-s23/`.
- pytest tests/dist: 49 passed (system Python; `uv run` raz zawisł). Bez Unity (brak zmian C#).
- NASTĘPNY KROK (lider): scalić world2-s23, potem tę gałąź; `python scripts/check-build-scenes.py --regions d67-full --require-tiles --require-high`.
