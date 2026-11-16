# STATUS — rynek-p1-s23 (D41, ADR 0227 dopisek)

- (e) DONE: przyczyna uskoku DK65 płd. = narożnik mieszany (wiejskie ramię + krawężnik) ronda kompaktowego: połowa wiejska
  dostawała goły krawężnik bez pasa trawy, conform NMT 2022 (stary rów) spadał 0,5–0,74 m w 1,5 m. Poprawka `meshing.build_corner_strips`
  (tylko j.compact): trawa za całym krawężnikiem + soft footprint → spadek ≤ 0,28 m (repro: NMT z WCS GUGiK, tylko liczby).
- (d) DONE: klucz `outer_diameter_m` (14–40 m, max(2 m, 40 %) od promienia OSM, inaczej stale), scalanie opcji compact_roundabout w network.load, override knyszyn 26,0 m WORKING_VALUE na końcu overrides.yaml; test_roundabout_0274: baseline 0218 bez D41, dolna granica wysepki S 28→27.
- NASTĘPNY KROK: (a) pomiar wiat z ortofoto → `uv run --project tools/worldgen python tools/worldgen/qa/market_canopy_ortho.py measure`
