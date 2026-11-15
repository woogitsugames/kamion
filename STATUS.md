# STATUS — F5 typology-0238 (ADR 0238)
- Zrobione: `streetscape/typology.py` (podtypy, proporcje ze statusem liczb, palety, reguła dachu), `buildings_mesh.py` (podtyp, kamienica z dachem spadzistym, front pawilonu, paleta bloków z 9 zdjęć M53), `roofs.py` (`shape`), `frontage.py` (`wall_lod1_flat`), harness `qa/typology_budget.py`.
- Liczby (harness, C): wszystkie kamery ≤ 0 (stretch_04 High −693, Low −299); Dojlidy ≤ 0.
- Testy: `-k building/facade/frontage/typology/...` 250 pass, 1 znany czerwony (test_frame_budget_with_forest_hlod).
- NASTĘPNY KROK: buildings.py (BASE_M 1.5, tagi OSM), testy `tests/gis/test_typology_0238.py`, ADR, PR:
  `uv run --project tools/worldgen python -m pytest tests/gis -k "building or facade or frontage or typology" -q`
