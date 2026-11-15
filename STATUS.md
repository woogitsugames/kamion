# STATUS — F5 typology-0238 (ADR 0238)
- Zrobione: `streetscape/typology.py`, zmiany w `buildings_mesh.py` / `roofs.py` / `frontage.py` / `materials.py`, `buildings.py` (BASE_M 1,5 z pomiaru, tagi OSM), `osm_extract.py` (`roof:shape`), harness `qa/typology_budget.py`, testy `tests/gis/test_typology_0238.py` (21/21), ADR 0238, LICENSES, docs/05.
- Liczby (harness, szacunek): C LOD0 −4 507, LOD1 −465, wszystkie 23 kamery ≤ 0 (stretch_04 High −693, Low −299); Dojlidy LOD0 −4 654, LOD1 −528.
- Otwarte: ocena wizualna u lidera (front pawilonu, barwy bloków), +6 submeshy LOD0 w C (`showroom_glass`).
- NASTĘPNY KROK (lider): `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c` → `pwsh scripts/import-region.ps1 -Region bialystok-industrial-c` → `pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting overcast -OutputDir artifacts/visual-qa/typology-0238/low`
