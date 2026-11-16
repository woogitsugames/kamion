# STATUS — D27 effective-graph-s23 (czytniki grafu → pipeline.effective_graph, dopisek ADR 0274)

- [1] Baza: origin/main + origin/roundabout2-0274 (#144). `pipeline.effective_graph(region, graph=None, applied=, stale=)` = jedyny
  loader; `carriageway_split.node_aliases()` (+ pole `split_of` węzła). export-route: alias zamiast heurystyki `endswith("s")`;
  route_start.json knyszyn i C odtworzone bajt w bajt (bez zmian w Data/).
- [2] navgraph `load_graph()` (effective, raport applied/stale, via-node restrykcji przechodzi na węzeł `split_of`), measure_axis_offset,
  `tools/ui/build_nav_map.py` (`load_graph`, `--out-dir`, teraz przez uv), `scripts/map-audit-cameras.py` (alias graph_nodes).
  KRTG knyszyn: surowy graf → luka węzeł↔geometria do 26,99 m na 6 krawędziach; efektywny → max 0,68 m, 0 krawędzi. KNAV C bajt w bajt.
- [3] validate/common.py (`graph_edges`), streetscape/water_banks.py na grafie efektywnym; testy navgraph na `load_graph`.
  `tests/gis/test_effective_graph_readers.py` 18 passed (syntetyczne rondo + knyszyn read-only + klasyfikacja wszystkich czytników).
  `pytest tests/gis -k "graph or route or nav or 0274 or roundabout or camera"` 174 passed, 4 skipped. navgraph/tests: 51 passed,
  1 znany czerwony (test_region_file_is_reproducible — czerwony też na bazie bez zmian, plik .bytes nieaktualny).
- NASTĘPNY KROK: dopisek ADR 0274 „Czytniki grafu”, PR.

# STATUS — D14 roundabout2-0274 (rondo Knyszyn, ADR 0274)

- [1] `tools/worldgen/qa/roundabout_ortho.py` + `docs/reports/roundabout-0274/`: ortofoto GUGiK w punkcie ronda = arkusz
  2025-05-27 (brak 2026), `roundabout_visible: false` (skrzyżowanie sprzed budowy) → wymiary ronda WORKING_VALUE / ESTIMATED.
- [2] `roads/compact_roundabout.py` tryb krawężnikowy (`lay_lanes`, promienie 6 / 8 m, nosek 4 m), `roads/carriageway_split.py`
  (DK65 S 27 m, N 17 m → wysepki 29,2 / 20,2 m), P-13 i P-10 przy pierścieniu, siatka wyspy z pierścieni, `plantings` clumps / stones
  (945 tris). Wloty 2 m za pierścieniem 13,1/11,8/12,9/13,4 → 10,9/11,0/11,5/11,4 m; asfalt 3 m za pierścieniem 165,5 → 141,3 m².
- [3] Recenzja D18: P1 + P2-2/3/4/5/6/7/8/11 zamknięte; P2-9, P2-10 nie ruszone. Trasa startowa knyszyn + region_catalog wyeksportowane.
- [4] Testy: `pytest tests/gis -k "roundabout or 0218 or 0274 or compact"` 108 passed; całe `tests/gis` 1839 passed, 58 skipped, 2 znane
  czerwone (forest_0187 LFS, test_report_not_stale — hashe generatora). Scalony origin/main `08c2e21f8`. ADR `docs/adr/0274-…md`.
- [5] Budżet zmierzony (syntetyczne NMT): road+markings w 60 m od ronda 7 937 → 8 999 tris; płyta Delaunay 1 840 (biegunowa dałaby 25 194).
- NASTĘPNY KROK (lider): `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region knyszyn` →
  `pwsh scripts/import-region.ps1 -Region knyszyn` → `pwsh scripts/visual-qa.ps1 -Scene World_knyszyn -Tier High -Lighting clear -Cameras rondo_dk65_top,rondo_dk65_above,rondo_dk65_from_south -OutputDir artifacts/roundabout-0274/vqa/High`
