# STATUS — treerows-0222 (D1, ADR 0222: szpalery wzdłuż DK65)

- Krok 1 (2026-11-15): sondowanie OSM API 0.6 (live) dla 14 kafli → `Data/Regions/<id>/tree_rows_osm.json`
  (tree_row / tree / track / culvert / level_crossing). OSM live = snapshot Geofabrik 261108: tree_row 0 w dk65-01…11
  i knyszyn-s; knyszyn 1 (74 m), knyszyn-w 3 (601 m); tree: dk65-06 24, knyszyn 66, knyszyn-w 2. Główne źródło szpalerów:
  BDOT10k OT_OIPR_L „rząd drzew” (już w streetscape_sources.json).
- NASTĘPNY KROK: moduł `tools/worldgen/streetscape/tree_rows.py` + testy
  `uv run --project tools/worldgen python -m pytest tests/gis -k "treerow" -q`
- Kroki 2–3, 5: `tools/worldgen/streetscape/tree_rows.py` (rytm, odsunięcie ≥ 3,0 m, trójkąty widoczności L1/L2,
  wyloty dróg polnych, przepusty, przejazdy), opt-in plikiem `Data/Regions/<id>/tree_rows.yaml` (14 kafli; linie z
  ortofoto K1 km 11,7 i 14,6), hook w vegetation.place (`tree_rows=`) + stage.py. Testy: 13 nowych, `-k "treerow or
  vegetation or planting"` 27 passed / 1 skip (lfs). Plan drzew: dk65-02 60, -04 60, -05 53, -08 33, knyszyn-w 105 …
- NASTĘPNY KROK: ADR 0222 (budżet per tier) + LICENSES + PR; lider: build_world + import + visual-qa (komendy w ADR).
- Krok 4, 6: ADR `docs/adr/0222-szpalery-dk65.md` (tabela stanu, przepisy z paragrafami, budżet per tier, komendy),
  `docs/LICENSES.md` (tree-rows-osm-probe, tree-rows-authored).
- NASTĘPNY KROK (lider): pętla z ADR 0222 §Odtworzenie (build_world + import-region + visual-qa dla 10 kafli).
