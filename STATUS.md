# STATUS — night-pc-s23 (zmierzch/noc PC, rendering-perf)
- Krok 1: visual-qa -Pc (7d7d2f1f4). BEFORE: artifacts/night-pc-s23/before/{WorldC,World_knyszyn}/{High,Low}-{dusk,night} (PC tiery, -TruckLamps low), 64 PNG, siatki grid-before/.
  Obserwacja: reflektory ciezarowki nie oswietlaja drogi (projectedHeadlamps=0 we wszystkich presetach) - z kabiny na DK65 droga czarna.
- Krok 2 (w toku): PcNightLighting (pule 8/12/16/16, highlight, reflektory na tierach PC), wiazka R112 kl. B (HeadlampBeam.cs + KamionLampPools.hlsl), MaxPools 16, PoolFocusAhead.
- NASTEPNY KROK: pwsh artifacts/night-pc-s23/run-qa.ps1 -Phase after1 ; uv run --no-project --with pillow --with numpy python -I artifacts/night-pc-s23/compare.py artifacts/night-pc-s23 before after1
# STATUS — G5 summer-cd-0216b (chmura G, rozszerzenie ADR 0216, D68)
- Krok 1: profile `summer-bialystok-cd` + `led-white-4000k-bialystok` (C, Dojlidy) w `Data/Regions/lighting_profiles.json`; NOAA `tools/worldgen/qa/sun_noaa.py` (31 VII −6° 21:06/311,4°; 20 VIII 20:22/299,7°).
- Krok 2: LED głowice tylko na 10 ulicach Dojlid z TED 769998-2024 (override `lamp-policy-led-tender-0216b`, 64 way); C bez zmian (`lamp-policy-unverified-0216b`); generator `furniture.chain_lamp_proto` + `lamp_led_scope`; audyt `tools/worldgen/qa/lamp_family_audit.py`.
- Krok 3: pytest `tests/gis/test_summer_cd_0216b.py` + `test_lamp_led_0216.py` 19 passed; EditMode zaktualizowany (nieuruchomiony); ADR 0216 §0216b.
- NASTĘPNY KROK (lider, po 0221): komendy w `docs/adr/0216-lato-i-biale-led-dk65-knyszyn.md` §0216b „Komendy dla lidera” (build_region → build_world → import-region → visual-qa → EditMode → APK A16).
