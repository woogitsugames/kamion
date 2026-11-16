# STATUS knyszyn-sidewalks-s23 (D38, ADR 0237 dopisek)
- (a) implied sidewalks (pavements.py + network.assign_sides), opt-in `pavement_rules: implied_sidewalks`; knyszyn on: +21.8 km, road tris 225k -> 264k; C/Dojlidy unchanged (test).
- (b) Poludniowa x Szkolna: node override `cluster: separate` (junctions.py) on n7015352011 -> 4-arm crossroads + parking T, 4/4 P-10 (was 2/4), teardrop gone. markings.py untouched.
- Tests: tests/gis/test_knyszyn_sidewalks_d38.py 38 passed; related suites green. Data: docs/reports/knyszyn-szkolna/.
- NEXT (lider): add the same pavement_rules entry to Data/Regions/knyszyn-w/overrides.yaml, then
  `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region knyszyn` (+ knyszyn-w) ; `pwsh scripts/import-region.ps1 -Region knyszyn -Build` ; `pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier High -Lighting clear -OutputDir artifacts/visual-qa/knyszyn-d38`
