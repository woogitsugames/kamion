# STATUS — D39 roofs-noise-s23 (ADR 0238 dopisek D39)
- Zrobione: `roofs.stable_rect` (remis MRR → kanoniczny prostokąt), `_frame` remis boków, `_angle` mod π + wybór siatki świetlików (mniej z dwóch), kopia bram w `build` (BC59), `roof_vents` margines 1 mm. Skan 1e-12…1e-6 m: C 0/644, Dojlidy 1/415 (daa0c871 tylko 1e-6).
- Baseline 0238 przeliczony (procedura FIX-2026-11-16): Dojlidy LOD0 −106 / LOD1 −21, C −465 / +1; testy gis 198 passed 3 skipped, tools/worldgen/tests 21 passed.
- NASTĘPNY KROK (lider, Windows): `uv run --project tools/worldgen python -m pytest tests/gis/test_typology_0238.py -q` → 27 passed; potem przebudowa C i Dojlid w world3.

# STATUS — G5 summer-cd-0216b (chmura G, rozszerzenie ADR 0216, D68)
- Krok 1: profile `summer-bialystok-cd` + `led-white-4000k-bialystok` (C, Dojlidy) w `Data/Regions/lighting_profiles.json`; NOAA `tools/worldgen/qa/sun_noaa.py` (31 VII −6° 21:06/311,4°; 20 VIII 20:22/299,7°).
- Krok 2: LED głowice tylko na 10 ulicach Dojlid z TED 769998-2024 (override `lamp-policy-led-tender-0216b`, 64 way); C bez zmian (`lamp-policy-unverified-0216b`); generator `furniture.chain_lamp_proto` + `lamp_led_scope`; audyt `tools/worldgen/qa/lamp_family_audit.py`.
- Krok 3: pytest `tests/gis/test_summer_cd_0216b.py` + `test_lamp_led_0216.py` 19 passed; EditMode zaktualizowany (nieuruchomiony); ADR 0216 §0216b.
- NASTĘPNY KROK (lider, po 0221): komendy w `docs/adr/0216-lato-i-biale-led-dk65-knyszyn.md` §0216b „Komendy dla lidera” (build_region → build_world → import-region → visual-qa → EditMode → APK A16).
