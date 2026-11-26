# STATUS weathering-s24 (dachy: zabrudzenia/mech/przebarwienia; ogrodzenia bloczkowe; pas brudu styk sciana-grunt; ADR 0238/0348 dopisek)

- Worktree `agent-a05410a22b79fbf0c`, galaz `worktree-agent-a05410a22b79fbf0c`; prywatna kopia `Data/raw/derived/{tykocin,dw671-tykocin-03}` (reszta derived = junction do main), Library z win-build (Win64).
- [krok 0] Kamery dowodowe `wx_zlota_fence`, `wx_zlota_plinth`, `wx_roofs_low` (tools/worldgen/qa/weathering_cameras.py). Render PRZED (import Win64 + VQA High clear/overcast) w tle: `artifacts/weathering-s24/vqa.ps1 -Phase before`.
- NASTEPNY KROK: kod generatora (roofs COLOR_0) + shader `_ROOF_WEATHER`, pas `_SplashBand`, warianty ogrodzen bloczkowych.
