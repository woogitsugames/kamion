# STATUS — agent seams-w10 (analiza FAIL szwów fali 10)

- [krok 1] Raport fali 10 == fala 9 (diff identyczny), zestaw FAIL stały od fali 2 po ADR 0310 (21.11 04:12). Narzędzie liczy z grafu + overrides w gicie (derived:network), więc przebudowa kafli nie zmienia wyniku. Fala 11 (e9e03c56f) nie zmienia tools/worldgen ani grafów/overrides → jej raport szwów będzie identyczny.
- [krok 2] 9 FAIL "położenie osi na szwie" = D94 gameplay_widen (network.gameplay_widen): przesunięcie osi (center_offset) liczone osobno w każdym kaflu z clearance własnego kawałka krawędzi; seam_taper (ADR 0275) wyrównuje szerokość, ale nie oś. Δ = n_pasów x 0,25 / 2 (0,125 / 0,25 / 0,375).
- [krok 3] 7 FAIL "pobocze" = assign_sides na kontekście OSM/BDOT przyciętym do bbox kafla (osm_context, streetscape_sources) + "fast" z sekcji środka łańcucha — duża zmiana, tylko propozycja.
- [krok 4] Poprawka: roads/seam_taper.py — przejście osi (koniec osi w połowie wektora między osiami nominalnymi, ta sama krzywa S), match po boundary_xy; qa/seams.py pokazuje przesunięcie osi w wierszu PRZEJŚCIE. Test tests/gis/test_seam_axis_w10.py (czerwony przed, zielony po) + test_seam_taper_0275 zielony (28 passed). Seams na 7 kaflach: FAIL 16 → 7 (zostają tylko pobocza).
- Następny krok: pełny przebieg seams (21 kafli) + testy pokrewne
  `uv run --project tools/worldgen python -m tools.worldgen.qa.seams --json <scratch>/all.json --md <scratch>/all.md`
