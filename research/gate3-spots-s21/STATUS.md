# STATUS — G3 punkty problemowe trasy C (bramka 3), sesja s21

## 2026-11-15 krok 1
- Lokalizacja 4 punktów z `gate3_cameras.json` (EPSG:2180 − origin regionu → WGS84, pyproj) — zrobione.
- OSM API 0.6 `map` dla 2 bbox (Putry, Bieżeństwa) pobrane; dopasowanie okręgu ronda Putry.
- Kandydaci kadrów: Commons geosearch (55 plików), Panoramax (24 w bbox Putry, 0 przy Bieżeństwie), KartaView
  (api.kartaview.org działa; 5 sekwencji; sekw. 14055 z 2016 r. — pliki 404/500).
- Obejrzane dotąd ok. 25 kadrów; manifest w budowie.

Następny krok: `python3 -I research/gate3-spots-s21/tools/build_manifest.py` (manifest.csv, pliki ≤1600 px do files/), potem README.
