# STATUS — D15 seam-taper-0275 (chmura D, runda 5, ADR 0275)
- Krok 1: `tools/worldgen/roads/seam_taper.py` (plan z danych sąsiada w gicie, krzywa S po połowie w każdym kaflu; hw + kody pobocza 0272, gdy `roads.xsec` jest) + haki w `pipeline.build_network` / `build`; `qa/seams.py` + test z `seams-0224` zaktualizowane (przejścia 0275, `lanes_follow_width` 0233, wiersze krawędzi asfaltu ±0,02 m). Na danych main: 5 par przejść (kleeberga|knyszynska ×3, kleeberga|maczka, knyszyn-s|dw671), 0 w DK65; `test_seams_0224.py` 15 passed.
- NASTĘPNY KROK: `uv run --project tools/worldgen python -m pytest tests/gis -k "seam or taper or 0275 or 0224" -q` po dopisaniu `tests/gis/test_seam_taper_0275.py`, potem próba na scaleniu z `origin/rail-dk65-s22` (pobocza 0272), raport `docs/reports/SEAMS-2026-11-16.md`, ADR 0275.

# STATUS — G5 summer-cd-0216b (chmura G, rozszerzenie ADR 0216, D68)
- Krok 1: profile `summer-bialystok-cd` + `led-white-4000k-bialystok` (C, Dojlidy) w `Data/Regions/lighting_profiles.json`; NOAA `tools/worldgen/qa/sun_noaa.py` (31 VII −6° 21:06/311,4°; 20 VIII 20:22/299,7°).
- Krok 2: LED głowice tylko na 10 ulicach Dojlid z TED 769998-2024 (override `lamp-policy-led-tender-0216b`, 64 way); C bez zmian (`lamp-policy-unverified-0216b`); generator `furniture.chain_lamp_proto` + `lamp_led_scope`; audyt `tools/worldgen/qa/lamp_family_audit.py`.
- Krok 3: pytest `tests/gis/test_summer_cd_0216b.py` + `test_lamp_led_0216.py` 19 passed; EditMode zaktualizowany (nieuruchomiony); ADR 0216 §0216b.
- NASTĘPNY KROK (lider, po 0221): komendy w `docs/adr/0216-lato-i-biale-led-dk65-knyszyn.md` §0216b „Komendy dla lidera” (build_region → build_world → import-region → visual-qa → EditMode → APK A16).
