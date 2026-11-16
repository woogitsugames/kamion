# STATUS — D19 map-plan-0278 (chmura D r6, ADR 0278)
- Krok 1: `tools/worldgen/qa/map_plan_0278.py` + wycinek OSM API 0.6 (21 kandydatów + 3 kalibracyjne + 2 miasta, relacje DK8/19/65, DW671/678) `Data/Plans/map-plan-0278/`, indeks GUGiK (bez pobierania), budżet z generated/*, plan + render `docs/reports/map/map_plan_0278.{json,png}` (14 kafli w kolejce).
- Krok 2: definicje 3 kafli (regions.py + overrides/sources.authored/route_endpoints): bialystok-porosly, dk8-s8-jeroniki, bialystok-dojlidy-gorne; `tests/gis/test_map_plan_0278.py` 26 passed; test_knyszynska_0208 / test_qa_tools_0219 zielone (powiaty wg ADR 0219).
- NASTĘPNY KROK: ADR 0278 + raport `docs/reports/MAP-PLAN-2026-11-16.md`, LICENSES, indeks ADR, PR.

# STATUS — G5 summer-cd-0216b (chmura G, rozszerzenie ADR 0216, D68)
- Krok 1: profile `summer-bialystok-cd` + `led-white-4000k-bialystok` (C, Dojlidy) w `Data/Regions/lighting_profiles.json`; NOAA `tools/worldgen/qa/sun_noaa.py` (31 VII −6° 21:06/311,4°; 20 VIII 20:22/299,7°).
- Krok 2: LED głowice tylko na 10 ulicach Dojlid z TED 769998-2024 (override `lamp-policy-led-tender-0216b`, 64 way); C bez zmian (`lamp-policy-unverified-0216b`); generator `furniture.chain_lamp_proto` + `lamp_led_scope`; audyt `tools/worldgen/qa/lamp_family_audit.py`.
- Krok 3: pytest `tests/gis/test_summer_cd_0216b.py` + `test_lamp_led_0216.py` 19 passed; EditMode zaktualizowany (nieuruchomiony); ADR 0216 §0216b.
- NASTĘPNY KROK (lider, po 0221): komendy w `docs/adr/0216-lato-i-biale-led-dk65-knyszyn.md` §0216b „Komendy dla lidera” (build_region → build_world → import-region → visual-qa → EditMode → APK A16).
