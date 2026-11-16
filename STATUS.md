# STATUS — dk19-tiles-s23 (D81: kafle 5–7 ADR 0278, trasa C ↔ Dojlidy przez DK19)
- Krok 0 (16.11): worktree `.claude/worktrees/dk19-tiles-s23`, gałąź `dk19-tiles-s23` z `origin/map-plan-0278` + merge `origin/main` (konflikt tylko `docs/adr/README.md`, rozwiązany `tools/docs/adr_index.py`); `Data/raw/derived` = Junction do main.
- Ustalenia: kafle bialystok-mickiewicza (1,−2), -bojary (1,−1), -wygoda (1,0) NIE mają wpisów w `regions.py` ani plików authored (ADR 0278 definiuje tylko 3 pierwsze) — do dodania; NMT 2025 jak C i Dojlidy; `qa/seams.py` jest tylko na `origin/seam-taper-0275`; 1206 m trasy (Dywizjonu 303) leży w kaflu 4 `bialystok-krywlany` (poza zakresem) — do zgłoszenia.
- NASTĘPNY KROK: dodać 3 wpisy `tools/worldgen/regions.py` + `Data/Regions/<id>/{overrides.yaml,sources.authored.json,route_endpoints.json}`, potem `uv run --project tools/worldgen python -m pytest -q tests/gis/test_map_plan_0278.py` i `uv run --project tools/worldgen tools/worldgen/ingest.py --region bialystok-wygoda` (odłączone, Start-Process).
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
