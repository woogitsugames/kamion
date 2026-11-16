# STATUS qa-tools-0219 (chmura C, ADR 0219)

- [a] Parser id grafu w `roadgraph.py` (`parse_node_id`, `edge_osm_way`, `osm_node_id`, `boundary_node_id`); fidelity `node_arm_check` pomija cięcia granicy kafla (`skipped: tile_boundary`), `way_of`/edge_sides bez `lstrip`. Testy `tests/gis/test_qa_tools_0219.py` 49 pass.
  NASTĘPNY KROK: (b) wspólny wybór powiatów dla bbox → `uv run --project tools/worldgen python -m pytest tests/gis/test_qa_tools_0219.py -q`
- [b] `tools/worldgen/powiaty.py` + PRG `Data/Admin/powiaty_prg.geojson` (8 powiatów, 139 KB); far_field (BDOT/LoD1 każdego powiatu pierścienia + okno OSM pierścienia), lod2_extract, water (tylko wybór powiatów). ADR 0219, LICENSES. test_qa_tools_0219: 78 pass; far_field testy 54 pass.
  NASTĘPNY KROK: pełne `uv run --project tools/worldgen python -m pytest tests/gis tools/worldgen/tests -q` → PR
- [c] Testy powiązane (16 plików) 214 pass / 6 skip / 1 xfail; cały pakiet tests/gis > 600 s w chmurze (nie dokończony). PR otwarty.
  NASTĘPNY KROK (lider): komendy z opisu PR (fidelity wszystkich regionów, far_field regionów granicznych + `pytest tests/gis -k far_field`, visual-qa WorldC Low).
