# STATUS — D32 typology-bitid-s23 (ADR 0238, dopisek D32)
- Przyczyna czerwonego `test_authored_and_untouched_buildings_are_bit_identical` (Dojlidy 18, C 43, same domy): dach domu chaotyczny wobec szumu float (przesunięcie 1e-9 m zmieniało 51/415 i 74/644 budynków) → baseline z Windows lidera ≠ Linux CI. Nie (a)/(b)/(c).
- Naprawa: `streetscape/roofs.py` `PLAN_TOL_M` 1 mm (`_clean` regionów/pokrycia/podbitki, `profile` bez przecięć wzdłuż krawędzi) → 3/415 i 1/644; baseline przeliczony (ade885234 + łatka, dane main); test regresji `test_house_triangles_do_not_depend_on_float_noise`.
- pytest `-k "typology or 0238 or 0242 or dojlidy or building"` 177 passed, 3 skipped; `-k "roof or house or multi or facade or kamienica"` 90 passed, 2 skipped.
- NASTĘPNY KROK (lider, Windows): `uv run --project tools/worldgen python -m pytest tests/gis/test_typology_0238.py -q` (oczekiwane 24 passed), potem przebudowa C + Dojlid (komendy w ADR 0238 / FIX-2026-11-16).
