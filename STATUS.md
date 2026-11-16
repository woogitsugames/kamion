# STATUS — s8-loop-s23 (D82: pętla S8 ↔ DW671 ↔ Tykocin, ADR 0288 — numer do potwierdzenia przez lidera)
- Baza: origin/map-plan-0278 + merge origin/main (baza była 555 commitów za main). Worktree `.claude/worktrees/s8-loop-s23`, Data/raw/derived = junction.
- Krok 1 (33bb671bd): 15 kafli zdefiniowanych — `tools/worldgen/qa/s8_loop_plan.py` (pinned pbf, okno 22.60 E), blok `ADR 0288` w `tools/worldgen/regions.py`, `Data/Regions/{s8-01..12,dw671-jezewo-01..03}/{overrides.yaml,route_endpoints.json}`, plan `docs/reports/map/s8_loop_plan.{json,png}` (obejrzany). Trasy kontrolne 26,07 km. Węzły (OSM motorway_junction): Choroszcz (s8-01), Tykocin (s8-03), Rzędziany (s8-07), Jeżewo (s8-11/12).
- Krok 2 (w toku): ingest s8-01..05 (NMT 2025 = jak dk65-01, orto 2024) → `artifacts/s8-loop-s23/run/ingest-<id>.{log,exit}`.
- NASTĘPNY KROK: `uv run tools/worldgen/build_region.py --region s8-01` → `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region s8-01 --context` (slot heavy) → fidelity → export-route → katalog → import-region → visual-qa.
# STATUS — D19 map-plan-0278 (chmura D r6, ADR 0278)
- Krok 1: `tools/worldgen/qa/map_plan_0278.py` + wycinek OSM API 0.6 (21 kandydatów + 3 kalibracyjne + 2 miasta, relacje DK8/19/65, DW671/678) `Data/Plans/map-plan-0278/`, indeks GUGiK (bez pobierania), budżet z generated/*, plan + render `docs/reports/map/map_plan_0278.{json,png}` (14 kafli w kolejce).
- Krok 2: definicje 3 kafli (regions.py + overrides/sources.authored/route_endpoints): bialystok-porosly, dk8-s8-jeroniki, bialystok-dojlidy-gorne; `tests/gis/test_map_plan_0278.py` 26 passed; test_knyszynska_0208 / test_qa_tools_0219 zielone (powiaty wg ADR 0219).
- Krok 3: ADR 0278, raport `docs/reports/MAP-PLAN-2026-11-16.md`, LICENSES (2 wpisy), indeks ADR; PR do main.
- NASTĘPNY KROK (lider): `uv run --project tools/worldgen tools/worldgen/ingest.py --region dk8-s8-jeroniki` → build_region → build_world → export-route → katalog → import-region (ADR 0278 „Odtworzenie”).

# STATUS — G5 summer-cd-0216b (chmura G, rozszerzenie ADR 0216, D68)
- Krok 1: profile `summer-bialystok-cd` + `led-white-4000k-bialystok` (C, Dojlidy) w `Data/Regions/lighting_profiles.json`; NOAA `tools/worldgen/qa/sun_noaa.py` (31 VII −6° 21:06/311,4°; 20 VIII 20:22/299,7°).
- Krok 2: LED głowice tylko na 10 ulicach Dojlid z TED 769998-2024 (override `lamp-policy-led-tender-0216b`, 64 way); C bez zmian (`lamp-policy-unverified-0216b`); generator `furniture.chain_lamp_proto` + `lamp_led_scope`; audyt `tools/worldgen/qa/lamp_family_audit.py`.
- Krok 3: pytest `tests/gis/test_summer_cd_0216b.py` + `test_lamp_led_0216.py` 19 passed; EditMode zaktualizowany (nieuruchomiony); ADR 0216 §0216b.
- NASTĘPNY KROK (lider, po 0221): komendy w `docs/adr/0216-lato-i-biale-led-dk65-knyszyn.md` §0216b „Komendy dla lidera” (build_region → build_world → import-region → visual-qa → EditMode → APK A16).
