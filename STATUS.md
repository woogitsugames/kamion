# STATUS — rynek-p1-s23 (D41, ADR 0227 dopisek)

- (e) DONE: przyczyna uskoku DK65 płd. = narożnik mieszany (wiejskie ramię + krawężnik) ronda kompaktowego: połowa wiejska
  dostawała goły krawężnik bez pasa trawy, conform NMT 2022 (stary rów) spadał 0,5–0,74 m w 1,5 m. Poprawka `meshing.build_corner_strips`
  (tylko j.compact): trawa za całym krawężnikiem + soft footprint → spadek ≤ 0,28 m (repro: NMT z WCS GUGiK, tylko liczby).
- NASTĘPNY KROK: (d) klucz `outer_diameter_m` w compact_roundabout.py → `uv run --project tools/worldgen python -m pytest tests/gis/test_rynek_p1_0227.py -q`
