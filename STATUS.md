# STATUS — s8-loop-s23 (D82, ADR 0288: pętla S8 ↔ DW671 ↔ Tykocin) — ZATRZYMANE 17.11 ~13:1x (przenosiny na inny komputer)
Gotowe do scalenia: NIE. Wszystkie własne procesy zatrzymane, sloty zwolnione, nic nie biegnie w tle.

## Stan w gicie (gałąź s8-loop-s23)
- 15 definicji kafli (regions.py blok ADR 0288, plan `docs/reports/map/s8_loop_plan.*`), ADR `docs/adr/0288-petla-s8-dw671-tykocin.md`.
- s8-01, 02, 03, 05: generated = budowa r4 z przekrojem S8 klasy S (`tools/worldgen/qa/s8_xsec_overrides.py`), fidelity r6 exit=0, trasy 2102 / 2084 / 2050 / 843 m. Rendery r4 obejrzane (pas awaryjny, linie, ekrany, bariera bez krawężnika, bez włazów); s8-01 obstacle_in_lane 44 → 0.
- **s8-04: dane ≠ generated.** `overrides.yaml` + `graph_filter.authored.json` w gicie = wariant docelowy (bez `bridge: true`, way 222577653 poza grafem), a `roads.graph.json` i `generated/*` (w tym fidelity_qa.json) = odrzucona budowa r6 z `bridge: true` (2 km S8 jako pomost). Wymaga build_region + build_world.
- **dk65-01: dane ≠ generated.** `overrides.yaml` ma 2 nadpisania przekroju S8 (way 183639794, 305447699), kafel NIE przebudowany — do czasu przebudowy `tests/gis` mogą zgłaszać nieaktualne generated dk65-01, a na szwie s8-01|dk65-01 jezdnie S8 są przesunięte o ok. 1 m.
- Katalog (+5, grupa „S8”), tile_graph (pamięć z importu sprzed zmiany przekroju), route_links (`dk65-01-s8-corner`, `s8-03-to-s8-04`, korytarz `s8-loop`) — przeliczone w r6; po przebudowie s8-04 / dk65-01 przeliczyć ponownie.
- Testy: pytest tests/gis po poprawkach NIE przeszedł pełnego przebiegu (ostatni pełny, przed poprawkami: 10 failed, 1 error, 2437 passed; 2 porażki na plikach identycznych z origin/main: test_hero_bridge::test_instances_emitted, test_map_plan_0278 hash). EditMode Win64 r6: 1316 / 1257 passed / 22 failed (20 × StartClearanceTests.ImportedScene… dla regionów spoza S8, 2 × TrailerAxleSyncTests) — żaden region s8-*.
- qa.seams r6: 5 FAIL (2 × s8-01|dk65-01 przesunięcie osi, 3 × s8-03|s8-04 skutek `bridge: true`) — oba powody usuwa krok poniżej.

## NASTĘPNY KROK (nowy komputer, z katalogu checkoutu gałęzi s8-loop-s23)
1. Sprawdź dane: `Test-Path Data/raw/derived/s8-04/world/chunk_0_0.glb` oraz `(Get-Item Data\raw\derived).LinkType`.
   - Jest `Data/raw/derived` dla s8-01..05 i dk65-01 → krok 2.
   - Nie ma → najpierw dla każdego z `s8-01 s8-02 s8-03 s8-04 s8-05`: `uv run --project tools/worldgen tools/worldgen/ingest.py --region <id>` → `uv run tools/worldgen/build_region.py --region <id>` → `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region <id> --context` → `uv run --project tools/worldgen python scripts/export-route.py --region <id>` → `pwsh scripts/import-region.ps1 -Region <id> -BuildTarget Win64`; potem krok 2.
2. `Start-Process pwsh -ArgumentList '-NoProfile','-File','tools/worldgen/qa/s8_loop_continue.ps1'` (odłączone; s8-04 build_region → build_world → route; dk65-01 build_world → route; import Win64 + visual-qa obu; tile_graph / route_links / katalog; qa.seams; fidelity s8-04 i dk65-01; pytest). Statusy: `artifacts/s8-loop-s23/run/*-r7.exit`, koniec `final-r7.exit`. Bez GPU/Unity: dodaj `-SkipUnity`.
3. Po `final-r7.exit`: obejrzeć `artifacts/s8-loop-s23/vqa-r7/{s8-04,dk65-01}/route-*.png` (S8 w s8-04 bez krawężników i balustrad, bez dziury; dk65-01 narożnik S8), `artifacts/s8-loop-s23/seams/seams-final.md` (oczekiwane 0 FAIL na S8), `run/pytest-r7.log`; wpisać WORLD_MEMORY z logów importu do `tools/worldgen/streaming/tile_graph.py` i przeliczyć; `git add -A Data/Regions/s8-0* Data/Regions/dk65-01 game/Assets/_Project tools tests docs STATUS.md; git commit; git push`.

## Otwarte dla lidera
- Ciągła trasa Białystok → S8 wymaga kafla `dk8-s8-jeroniki` (ADR 0288 Otwarte 1).
- Przejazd pod S8 w s8-04 pominięty w grafie (Otwarte 7); pas dzielący w s8-04 z modelu ok. 5,0 m (zadane 4–4,8 m).
- Przesunięcie osi pasów 0,25 m i trzeci pas na zewnątrz = WORKING_VALUE (Otwarte 3).
- Dowody: `artifacts/s8-loop-s23/` w worktree starego komputera + kopia w `C:\Users\matma\Documents\Claude\kamion\artifacts\s8-loop-s23\` (bez pełnych PNG) — poza gitem, przenieść razem z projektem.
