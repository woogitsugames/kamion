# STATUS — treerows-0222 (D1, ADR 0222: szpalery wzdłuż DK65)

- Krok 1 (2026-11-15): sondowanie OSM API 0.6 (live) dla 14 kafli → `Data/Regions/<id>/tree_rows_osm.json`
  (tree_row / tree / track / culvert / level_crossing). OSM live = snapshot Geofabrik 261108: tree_row 0 w dk65-01…11
  i knyszyn-s; knyszyn 1 (74 m), knyszyn-w 3 (601 m); tree: dk65-06 24, knyszyn 66, knyszyn-w 2. Główne źródło szpalerów:
  BDOT10k OT_OIPR_L „rząd drzew” (już w streetscape_sources.json).
- NASTĘPNY KROK: moduł `tools/worldgen/streetscape/tree_rows.py` + testy
  `uv run --project tools/worldgen python -m pytest tests/gis -k "treerow" -q`
